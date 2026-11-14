# -*- coding: utf-8 -*-
"""
TÌM VÀ XOÁ CÂU TRÙNG TRONG NGÂN HÀNG (cau-hoi/).

Ba mức:
  trung    : trùng hoàn toàn — cùng đề bài và cùng bộ phương án/đáp số (chỉ khác cách gõ, khoảng trắng, lời giải, thứ tự phương án)
             → mặc định chọn xoá các bản thừa, GIỮ 1 bản tốt nhất (đã phân loại dạng, lời giải dài hơn, có hình)
  cung_de  : cùng đề bài nhưng khác phương án / đáp án — thường là 2 câu khác nhau, cần thầy xem
  gan_giong: đề bài + phương án giống ≥ 90% (khác vài số, vài chữ) — cần thầy xem

  python3 scripts/cau_trung.py               # in thống kê
  python3 scripts/cau_trung.py --xoa ma1 ma2 # xoá các câu theo mã %[ma:…], lưu bản sao vào du-lieu/da_xoa/
Xoá xong tự lập lại chỉ mục. Câu đã xoá vẫn còn trong du-lieu/da_xoa/<thời điểm>.tex để khôi phục khi cần.
"""
import os, sys, re, json, time, random, collections, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nh_core import GOC, tim_lenh, doc_tham_so, MA_CAU

def _bo(t, ten, so=1):
    m = tim_lenh(t, ten)
    if m:
        ds, j = doc_tham_so(t, m.end(), so)
        if ds:
            return t[:m.start()] + t[j:], [x[2] for x in ds]
    return t, None

def chuan(t):
    t = t.replace("{,}", ",").replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac")
    t = re.sub(r"\\True(?![A-Za-z])", "", t)
    t = re.sub(r"\\(left|right|displaystyle|,|;|!|quad|qquad|limits)(?![A-Za-z])", "", t)
    return re.sub(r"[\s${}~]", "", t).lower()

def tach(k):
    """→ (đề chuẩn hoá, bộ phương án/đáp số chuẩn hoá, độ dài lời giải)."""
    t = re.sub(r"(?<!\\)%[^\n]*", "", k)
    t, lg = _bo(t, "loigiai")
    t, sa = _bo(t, "shortans")
    pa = None
    for ten in ("choiceTF", "choice"):
        t, pa = _bo(t, ten, 4)
        if pa:
            break
    t = re.sub(r"\\(begin|end)\{(ex|bt)\}", "", t)
    bo = tuple(sorted(chuan(x) for x in pa)) if pa else (chuan(sa[0]),) if sa else ()
    return chuan(t), bo, len(lg[0]) if lg else 0

def doc_chi_muc():
    ds = []
    for l in open(os.path.join(GOC, "du-lieu", "chi_muc.jsonl"), encoding="utf-8"):
        d = json.loads(l)
        de, bo, dlg = tach(d["noi_dung"])
        d.update(_de=de, _bo=bo, _lg=dlg)
        ds.append(d)
    return ds

def diem_giu(d):
    """Bản nên GIỮ: đã phân loại dạng > có lời giải dài > có hình > đang ở file dạng (không phải _chua_phan_loai)."""
    return (0 if "_chua_phan_loai" in d["file"] else 1, 1 if d.get("id") else 0, d["_lg"], 1 if d.get("co_hinh") else 0)

def gon(d):
    """Thông tin gọn gửi cho giao diện."""
    t = re.sub(r"(?<!\\)%[^\n]*", "", d["noi_dung"])
    t, _ = _bo(t, "loigiai")
    t = re.sub(r"\\(begin|end)\{(ex|bt)\}", "", t)
    t = re.sub(r"\\(choiceTF|choice|shortans)(?![A-Za-z])", " ▸ ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return {"ma": d["ma"], "id": d.get("id") or "", "loai": d["loai"], "dap_an": d.get("dap_an") or "",
            "file": d["file"], "ten_dang": d.get("ten_dang") or "", "lg": d["_lg"], "hinh": bool(d.get("co_hinh")),
            "dung": d.get("so_lan_dung") or 0, "xem": t[:420], "tex": d["noi_dung"]}

def tim(nguong=0.9, gan_giong=True):
    ds = doc_chi_muc()
    nhom = collections.defaultdict(list)
    for d in ds:
        if len(d["_de"]) >= 20:
            nhom[(d["loai"], d["_de"])].append(d)
    ket_qua, da_nhom = [], set()
    for (loai, _), v in nhom.items():
        if len(v) < 2:
            continue
        theo_bo = collections.defaultdict(list)
        for d in v:
            theo_bo[d["_bo"]].append(d)
        for bo, w in theo_bo.items():                      # trùng hoàn toàn
            if len(w) > 1:
                w.sort(key=diem_giu, reverse=True)
                ket_qua.append({"kieu": "trung", "cau": [gon(x) for x in w], "xoa": [x["ma"] for x in w[1:]]})
                da_nhom |= {x["ma"] for x in w}
        if len(theo_bo) > 1:                                 # cùng đề, khác phương án
            w = sorted(v, key=diem_giu, reverse=True)
            ket_qua.append({"kieu": "cung_de", "cau": [gon(x) for x in w], "xoa": []})
            da_nhom |= {x["ma"] for x in w}
    if gan_giong:                                            # gần giống: MinHash trên đề + phương án
        rnd = random.Random(7)
        hat = [rnd.getrandbits(61) for _ in range(8)]
        vung = collections.defaultdict(list)
        tap = {}
        for i, d in enumerate(ds):
            s = d["_de"] + "|" + "|".join(d["_bo"])
            if len(s) < 40:
                continue
            S = {hash(s[j:j + 6]) for j in range(len(s) - 5)}
            tap[i] = S
            mh = [min(h ^ x for h in S) for x in hat]
            for b in range(4):
                vung[(b, mh[2 * b], mh[2 * b + 1])].append(i)
        cap = set()
        for v in vung.values():
            if 1 < len(v) < 40:
                for a in range(len(v)):
                    for b in range(a + 1, len(v)):
                        cap.add((v[a], v[b]))
        cha = {}
        def goc(x):
            while cha.get(x, x) != x:
                x = cha[x]
            return x
        for a, b in cap:
            A, B = ds[a], ds[b]
            if A["loai"] != B["loai"] or (A["_de"] == B["_de"]):
                continue
            j = len(tap[a] & tap[b]) / len(tap[a] | tap[b])
            if j >= nguong:
                cha[goc(a)] = goc(b)
        cum = collections.defaultdict(list)
        for x in list(cha):
            cum[goc(x)].append(x)
        for r, v in cum.items():
            w = sorted({ds[i]["ma"]: ds[i] for i in v + [r]}.values(), key=diem_giu, reverse=True)
            if len(w) > 1:
                ket_qua.append({"kieu": "gan_giong", "cau": [gon(x) for x in w], "xoa": []})
    thu_tu = {"trung": 0, "cung_de": 1, "gan_giong": 2}
    ket_qua.sort(key=lambda g: (thu_tu[g["kieu"]], g["cau"][0]["file"]))
    return ket_qua

def xoa(cac_ma, in_ra=print):
    """Xoá khối câu có %[ma:…] trong các file cau-hoi/, lưu bản sao, lập lại chỉ mục."""
    cac_ma = set(cac_ma)
    if not cac_ma:
        return 0
    vi_tri = collections.defaultdict(set)
    for l in open(os.path.join(GOC, "du-lieu", "chi_muc.jsonl"), encoding="utf-8"):
        d = json.loads(l)
        if d["ma"] in cac_ma:
            vi_tri[d["file"]].add(d["ma"])
    sao = []
    da = 0
    for rel, mas in vi_tri.items():
        p = os.path.join(GOC, rel)
        t = open(p, encoding="utf-8").read()
        def bo(m):
            nonlocal da
            k = m.group(0)
            mm = MA_CAU.search(k.split("\n", 1)[0])
            if mm and mm.group(1) in mas:
                sao.append(f"% từ: {rel}\n{k.rstrip()}\n")
                da += 1
                return ""
            return k
        moi = re.sub(r"\\begin\{(ex|bt)\}.*?\\end\{\1\}[ \t]*\n?(?:[ \t]*\n)?", bo, t, flags=re.S)
        if moi != t:
            open(p, "w", encoding="utf-8").write(moi)
    if sao:
        thu = os.path.join(GOC, "du-lieu", "da_xoa")
        os.makedirs(thu, exist_ok=True)
        ten = os.path.join(thu, time.strftime("xoa_trung_%Y%m%d-%H%M%S.tex"))
        open(ten, "w", encoding="utf-8").write(f"% {len(sao)} câu đã xoá khỏi ngân hàng (câu trùng) — chép lại vào file dạng để khôi phục\n\n"
                                               + "\n".join(sao))
        in_ra(f"Đã xoá {da} câu. Bản sao: {os.path.relpath(ten, GOC)}")
    r = subprocess.run([sys.executable, os.path.join(GOC, "scripts", "lap_chi_muc.py")], cwd=GOC,
                       capture_output=True, text=True)
    in_ra((r.stdout or "").strip().splitlines()[-1] if r.stdout else "Đã lập lại chỉ mục.")
    return da

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--xoa":
        xoa(sys.argv[2:])
    else:
        kq = tim()
        dem = collections.Counter(g["kieu"] for g in kq)
        print(f"Trùng hoàn toàn: {dem['trung']} nhóm ({sum(len(g['xoa']) for g in kq)} câu thừa) · "
              f"cùng đề khác phương án: {dem['cung_de']} nhóm · gần giống: {dem['gan_giong']} nhóm")
