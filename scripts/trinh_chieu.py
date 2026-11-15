# -*- coding: utf-8 -*-
"""CHUYỂN CÂU ĐÃ CHỌN SANG ỨNG DỤNG TRÌNH CHIẾU HTML (Soạn đề & trình chiếu Toán).

Câu lấy theo ma trận (xem trước) → JSON "math-exam-v1" → nhúng vào bản sao của ứng dụng
khung/TrinhChieu/ung_dung_trinh_chieu.html → mở ra là có sẵn đề: trình chiếu, xuất HTML
trình chiếu, bài kiểm tra cho học sinh, Word, lưu thư viện Google Sheets…

Hình TikZ và bảng (tabular) được biên dịch sẵn thành SVG bằng MacTeX (latex + dvisvgm),
nên trình chiếu hiện hình ngay, không phải chuyển TikZ → SVG bằng tay.

Dùng:  python3 trinh_chieu.py <ma1> <ma2> … [--ten "Tên đề"] [--khong-hinh]
"""
import os, re, json, shutil, time, argparse, glob
from nh_core import GOC, doc_nhom, ten_khong_dau
from xem_truoc import kho
from k12word import tach_cau, bien_dich_manh

UNG_DUNG = os.path.join(GOC, "khung", "TrinhChieu", "ung_dung_trinh_chieu.html")
THU_MUC_RA = os.path.join(GOC, "de-da-ra", "TrinhChieu")
GIAO_VIEN = "Thầy Vũ Tiến Lực - Trường THPT Nguyễn Hữu Cảnh"
LOP_SO = {"0": "10", "1": "11", "2": "12"}

HINH = re.compile(r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}|<svg\b[^>]*>.*?</svg>", re.S | re.I)


def bo_immini(s):
    """\\immini[..]{chữ}{hình} → hình rồi chữ (giống ứng dụng trình chiếu khi nạp TeX)."""
    out, p = "", 0
    for m in re.finditer(r"\\immini\s*(?:\[[^\]]*\])?", s):
        if m.start() < p:
            continue
        try:
            i = m.end()
            while i < len(s) and s[i].isspace(): i += 1
            a, ea = doc_nhom(s, i)
            while ea < len(s) and s[ea].isspace(): ea += 1
            b, eb = doc_nhom(s, ea)
        except Exception:
            continue
        out += s[p:m.start()] + b + "\n" + bo_immini(a)
        p = eb
    return out + s[p:]


def _bang_ngoai_toan(t):
    """Vị trí các khối tabular (kèm center bao ngoài nếu có) không nằm trong tikzpicture."""
    ra = []
    for m in re.finditer(r"\\begin\{tabular\}", t):
        dau = t.rfind("\\begin{tikzpicture}", 0, m.start())
        if dau >= 0 and t.rfind("\\end{tikzpicture}", 0, m.start()) < dau:
            continue
        sau = 0; i = m.end(); muc = 1
        while muc:
            a, b = t.find("\\begin{tabular}", i), t.find("\\end{tabular}", i)
            if b < 0:
                break
            if 0 <= a < b:
                muc += 1; i = a + 15
            else:
                muc -= 1; i = b + 13
        if muc == 0:
            ra.append((m.start(), i))
    # bỏ khối lồng trong khối khác
    return [(a, b) for a, b in ra if not any(x < a and b <= y for x, y in ra)]


VAN_BAN = ((r"\\lq\\lq", "“"), (r"\\rq\\rq", "”"), (r"\\lq(?![A-Za-z])", "‘"), (r"\\rq(?![A-Za-z])", "’"),
           (r"\\(?:hfill|newline|noindent|centering)(?![A-Za-z])", ""))


def lam_sach(t):
    for a, b in VAN_BAN:
        t = re.sub(a, b, t)
    return t


def cau_json(c):
    p = tach_cau(c)
    p = {k: (lam_sach(v) if isinstance(v, str) else [lam_sach(x) for x in v] if isinstance(v, list) else v)
         for k, v in p.items()}
    loai = {"TN": "mcq", "DS": "tf", "TLN": "short"}.get(c["loai"])
    if not loai:
        return None
    q = {"type": loai, "stem": bo_immini(p["de"]).strip(), "solution": bo_immini(p["lg"] or "").strip(),
         "options": [x.strip() for x in (p["pa"] or [])] if loai != "short" else []}
    da = c.get("dap_an") or ""
    if loai == "mcq":
        q["answer"] = "ABCD".index(da) if len(da) == 1 and da in "ABCD" else 0
    elif loai == "tf":
        q["answer"] = [x in "ĐT" for x in da[:4]] + [False] * (4 - len(da[:4]))
    else:
        q["answer"] = (p["tln"] or da or "").strip()
    if loai != "short" and len(q["options"]) != 4:
        return None
    q["ma"] = c["ma"]
    if c.get("dang_key"):
        q["ma_dang"] = c["dang_key"]; q["ten_dang"] = c.get("ten_dang") or ""
    return q


def _cac_truong(q):
    yield "stem"
    yield "solution"
    for i in range(len(q.get("options") or [])):
        yield f"option{i}"


def _lay(q, f):
    return q["options"][int(f[6:])] if f.startswith("option") else q[f]


def _dat(q, f, v):
    if f.startswith("option"):
        q["options"][int(f[6:])] = v
    else:
        q[f] = v


def ve_hinh(cau, in_ra=print):
    """Biên dịch TikZ + tabular → SVG; tabular thay bằng SVG nhúng, TikZ ghi vào q['figures']['stem:0']…"""
    manh, vi_tri = {}, []
    for qi, q in enumerate(cau):
        for f in _cac_truong(q):
            t = _lay(q, f)
            for a, b in _bang_ngoai_toan(t):
                k = f"b{len(manh)}"; manh[k] = ("fig", t[a:b]); vi_tri.append(("bang", qi, f, (a, b), k))
            for i, m in enumerate(HINH.finditer(t)):
                if m.group(0).lstrip().startswith("\\begin"):
                    k = f"h{len(manh)}"; manh[k] = ("fig", m.group(0)); vi_tri.append(("tikz", qi, f, m.group(0), k))
    if not manh:
        return 0, 0
    tm = os.path.join(THU_MUC_RA, "_bien_dich")
    if os.path.isdir(tm):
        shutil.rmtree(tm, ignore_errors=True)
    shutil.copytree(os.path.join(GOC, "khung", "DeThiChinhThuc"), tm)
    mau = open(os.path.join(tm, "mau_de.tex"), encoding="utf-8").read()
    open(os.path.join(tm, "De_tam.tex"), "w", encoding="utf-8").write(re.sub(r"<<[A-Z_]+>>", "", mau))
    kq = bien_dich_manh(manh, tm, in_ra)
    svg = {}
    for k, v in kq.items():
        if v.get("svg") and os.path.exists(v["svg"]):
            s = open(v["svg"], encoding="utf-8").read()
            s = re.sub(r"^<\?xml[^>]*\?>\s*", "", s)
            s = re.sub(r"<!--.*?-->", "", s, flags=re.S).strip()
            svg[k] = s
    # bảng: thay trong văn bản (từ cuối lên để không lệch vị trí)
    for qi, f, a, b, k in sorted(((x[1], x[2], *x[3], x[4]) for x in vi_tri if x[0] == "bang"),
                                 key=lambda x: (x[0], x[1], -x[2])):
        if k in svg:
            t = _lay(cau[qi], f)
            _dat(cau[qi], f, t[:a] + "\n" + svg[k] + "\n" + t[b:])
    # tikz: khoá theo thứ tự hình (tikz + svg) trong từng trường SAU khi đã thay bảng
    nguon = {}
    for x in vi_tri:
        if x[0] == "tikz":
            nguon.setdefault((x[1], x[2], x[3]), x[4])
    so_ok = sum(1 for x in vi_tri if x[4] in svg)
    for qi, q in enumerate(cau):
        for f in _cac_truong(q):
            for i, m in enumerate(HINH.finditer(_lay(q, f))):
                k = nguon.get((qi, f, m.group(0)))
                if k and k in svg:
                    q.setdefault("figures", {})[f"{f}:{i}"] = svg[k]
    shutil.rmtree(tm, ignore_errors=True)
    return len(manh), so_ok


def tao(cac_ma, ten="Đề trình chiếu", in_ra=print, ve=True, lop=None):
    if not os.path.exists(UNG_DUNG):
        raise RuntimeError("Chưa có ứng dụng trình chiếu: cần file khung/TrinhChieu/ung_dung_trinh_chieu.html")
    k = kho()
    cau, bo = [], []
    for ma in cac_ma:
        c = k.get(ma)
        q = cau_json(c) if c else None
        (cau.append(q) if q else bo.append(ma))
    if not cau:
        raise RuntimeError("Không có câu nào chuyển được.")
    if bo:
        in_ra(f"  Bỏ {len(bo)} câu không đúng cấu trúc (thiếu 4 phương án/đáp án): {', '.join(bo)}")
    if ve:
        try:
            n, ok = ve_hinh(cau, in_ra)
        except Exception as e:
            n, ok = 1, 0
            in_ra(f"  Chưa vẽ được hình sang SVG ({e}); câu vẫn chuyển đủ, hình TikZ chuyển sau trong ứng dụng.")
        if n:
            in_ra(f"  Hình/bảng: {ok}/{n} đã thành SVG" + ("" if ok == n else
                  " — hình còn thiếu: dùng mục 08 · SVG hàng loạt trong ứng dụng trình chiếu"))
    if not lop:
        so = [k[m]["dang_key"][0] for m in cac_ma if m in k and k[m].get("dang_key")]
        lop = (LOP_SO.get(max(set(so), key=so.count)) if so and max(set(so), key=so.count) in LOP_SO
               else (max(set(so), key=so.count) if so else ""))
    d = {"format": "math-exam-v1", "title": ten, "teacher": GIAO_VIEN, "questions": cau}
    if lop:
        d["grade"] = str(lop)
    os.makedirs(THU_MUC_RA, exist_ok=True)
    goc = re.sub(r"[^\w\-]+", "_", ten_khong_dau(ten, 60)).strip("_") or "De"
    goc = f"{goc}_{time.strftime('%Y%m%d_%H%M')}"
    p_json = os.path.join(THU_MUC_RA, goc + ".json")
    json.dump(d, open(p_json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    app = open(UNG_DUNG, encoding="utf-8").read()
    nhung = json.dumps(d, ensure_ascii=False).replace("<", "\\u003c")
    m = re.search(r'(<script type="application/json" id="initial">)(.*?)(</script>)', app, re.S)
    if not m:
        raise RuntimeError("Ứng dụng trình chiếu không có khối dữ liệu id=\"initial\" (phiên bản khác?)")
    app = app[:m.start(2)] + nhung + app[m.end(2):]
    p_html = os.path.join(THU_MUC_RA, goc + ".html")
    open(p_html, "w", encoding="utf-8").write(app)
    dem = {t: sum(1 for q in cau if q["type"] == t) for t in ("mcq", "tf", "short")}
    in_ra(f"Đã chuyển {len(cau)} câu (TN {dem['mcq']} · Đúng/Sai {dem['tf']} · TLN {dem['short']}) sang ứng dụng trình chiếu.")
    in_ra(f"  {os.path.relpath(p_html, GOC)}\n  {os.path.relpath(p_json, GOC)} (mở lại bằng nút Nạp JSON của ứng dụng)")
    return {"html": p_html, "json": p_json, "so_cau": len(cau)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("ma", nargs="+")
    ap.add_argument("--ten", default="Đề trình chiếu")
    ap.add_argument("--khong-hinh", action="store_true")
    a = ap.parse_args()
    tao(a.ma, a.ten, ve=not a.khong_hinh)
