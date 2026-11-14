# -*- coding: utf-8 -*-
"""
KIỂM TRA CÂU TRƯỚC KHI NHẬP KHO — câu lỗi không được vào ngân hàng.
  1) Kiểm tra tĩnh: ngoặc { } và dấu $ cân, TN đúng 1 \\True, ĐS ≤ 4 \\True, đáp số trả lời ngắn là số ≤ 4 kí tự.
  2) Biên dịch thử bằng pdflatex với khung đề thật (nếu máy có pdflatex): lỗi LaTeX của câu nào → loại câu đó.
Dùng: from kiem_bien_dich import kiem;  loi = kiem(cac_khoi)   # {mã câu: [lý do…]}
CLI : python3 scripts/kiem_bien_dich.py file.tex …   (in danh sách câu lỗi)
"""
import os, re, sys, shutil, subprocess, tempfile, collections
from nh_core import GOC, doc, tach_khoi, phan_tich_cau, tim_pdflatex

MA = re.compile(r"%\[ma:([0-9a-f]{8})\]")


def _ma(k):
    m = MA.search(k.split("\n", 1)[0])
    return m.group(1) if m else None


def _can(k):
    t = re.sub(r"(?<!\\)%[^\n]*", "", k)
    t = t.replace("\\\\", "")
    t = re.sub(r"\\[{}$%&#_]", "", t)
    return t.count("{") - t.count("}"), t.count("$")


def kiem_tinh(k):
    ly = []
    lech, do = _can(k)
    if lech:
        ly.append("ngoặc { } không cân")
    if do % 2:
        ly.append("số dấu $ lẻ")
    if "\\choiceTF" not in k and "\\choice" in k and k.count("\\True") != 1:
        ly.append(f"trắc nghiệm có {k.count(chr(92) + 'True')} \\True (cần đúng 1)")
    for s in re.findall(r"\\shortans(?:\[[^\]]*\])?\{((?:[^{}]|\{[^{}]*\})*)\}", k):
        v = s.strip().strip("$").replace("{,}", ",").replace(" ", "").replace("\\,", "")
        if not re.fullmatch(r"-?\d+(,\d+)?", v) or len(v) > 4:
            ly.append(f"đáp số trả lời ngắn “{s.strip()[:30]}” không phải số ≤ 4 kí tự")
    return ly


def kiem_bien_dich(cac_khoi, in_ra=print, nhom=400):
    """Biên dịch thử theo nhóm; → {mã: [lỗi…]}. Không có pdflatex → {}."""
    pdfl = tim_pdflatex()
    if not pdfl:
        in_ra("   (máy không có pdflatex — bỏ qua bước biên dịch thử, chỉ kiểm tra tĩnh)")
        return {}
    khung = os.path.join(GOC, "khung", "DeThiChinhThuc")
    mau = doc(os.path.join(khung, "mau_de.tex"))
    for k in ("SO_GD", "TRUONG", "TEN_KY_THI", "NAM_HOC", "MON", "THOI_GIAN"):
        mau = mau.replace(f"<<{k}>>", "X")
    tam = tempfile.mkdtemp(prefix="kiem_bd_")
    loi = collections.defaultdict(list)
    try:
        for x in os.listdir(khung):
            s, d = os.path.join(khung, x), os.path.join(tam, x)
            (shutil.copytree if os.path.isdir(s) else shutil.copy)(s, d)
        for g in range(0, len(cac_khoi), nhom):
            phan = cac_khoi[g:g + nhom]
            nd = ("\\Opensolutionfile{ans}[Ans/kt]\\Opensolutionfile{ansbook}[Ansbook/kt]\\Opensolutionfile{ansbt}[Ansbook/ktb]\n"
                  + "\n\n".join(phan) +
                  "\n\\Closesolutionfile{ans}\\Closesolutionfile{ansbook}\\Closesolutionfile{ansbt}\n")
            t = mau.replace("<<CHE_DO_LOI_GIAI>>", "\\hienthiloigiai").replace("<<NOI_DUNG>>", nd)
            t = re.sub(r"<<[A-Z_]+>>", "", t)
            open(os.path.join(tam, "kt.tex"), "w", encoding="utf-8").write(t)
            dong_ma, cur = [], None
            for l in t.split("\n"):
                m = MA.search(l)
                if m:
                    cur = m.group(1)
                dong_ma.append(cur)
            try:
                r = subprocess.run([pdfl, "-interaction=nonstopmode", "kt.tex"], cwd=tam, capture_output=True,
                                   text=True, errors="ignore", timeout=60 + 3 * len(phan),
                                   env=dict(os.environ, TEXINPUTS=os.environ.get("NH_TEXINPUTS", "") + ":"))
                log = open(os.path.join(tam, "kt.log"), encoding="latin-1").read().split("\n")
            except subprocess.TimeoutExpired:
                in_ra("   ⚠ biên dịch thử quá lâu, bỏ qua nhóm này"); continue
            for i, l in enumerate(log):
                if l.startswith("!"):
                    for x in log[i:i + 14]:
                        m = re.match(r"l\.(\d+)", x)
                        if m:
                            n = int(m.group(1))
                            ma = dong_ma[n - 1] if 0 < n <= len(dong_ma) else None
                            thong = "LaTeX: " + l[2:70].strip()
                            if ma and len(loi[ma]) < 2 and thong not in loi[ma]:
                                loi[ma].append(thong)
                            break
            in_ra(f"   biên dịch thử {min(g + nhom, len(cac_khoi))}/{len(cac_khoi)} câu…")
    finally:
        shutil.rmtree(tam, ignore_errors=True)
    return dict(loi)


def kiem(cac_khoi, in_ra=print, bien_dich=True):
    """→ {mã câu: [lý do]} cho các câu lỗi (khối phải có %[ma:…])."""
    loi = collections.defaultdict(list)
    for k in cac_khoi:
        for x in kiem_tinh(k):
            loi[_ma(k)].append(x)
    if bien_dich:
        for m, ds in kiem_bien_dich(cac_khoi, in_ra).items():
            loi[m] += ds
    loi.pop(None, None)
    return dict(loi)


if __name__ == "__main__":
    ks = [k for f in sys.argv[1:] for k in tach_khoi(doc(f))]
    l = kiem(ks)
    print(f"{len(ks)} câu, {len(l)} câu lỗi")
    for m, ds in l.items():
        print(f"  {m}: {'; '.join(ds)}")
