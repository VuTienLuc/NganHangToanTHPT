# -*- coding: utf-8 -*-
"""
NGÂN HÀNG TỰ SINH — từ một câu mẫu trong kho sinh câu TƯƠNG TỰ THEO MẪU (gắn dòng '% mau: <mã>') để in phiếu bài học.

Hai cách:
  1) PYTHON (không cần mạng): "phát lại" lời giải mẫu với số liệu mới.
     - Số trong đề = số liệu đầu vào; trong lời giải, mỗi đẳng thức "$24 \\times 4 = 96$" cho biết 96 = 24 × 4 …
       → dựng lại toàn bộ chuỗi tính theo số liệu đầu vào.
     - Chọn số liệu mới cùng số chữ số, cùng số chữ số 0 tận cùng, cùng chẵn/lẻ; mọi kết quả trung gian phải là
       số tự nhiên dương (chia hết, trừ không âm), mọi dòng "thử lại" vẫn đúng → mới nhận.
     - Câu mẫu không đổi số an toàn được (bài suy luận, đề có số ngoài công thức, lời giải có số "lạ" không suy ra
       được từ đề…) → bỏ qua, tự chọn câu mẫu khác cùng dạng.
     - Nâng cao (Python): cùng lời giải, số liệu lớn hơn (khó tính hơn một chút).
  2) AI (Gemini / Claude qua khoá API của thầy, lưu ở ai_khoa.json — KHÔNG đưa lên git): gửi prompt "tương tự theo mẫu"
     (tao_prompt.prompt_tuong_tu) và lấy khối ```latex trả về.
"""
import json, os, random, re, sys, urllib.request, urllib.error
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nh_core import GOC  # noqa: E402

SO = re.compile(r"\d{1,3}(?:\\,\d{3})+|\d+(?:\{,\}\d+)?")
TOAN = re.compile(r"\$([^$]+)\$")
HANG_NHO = 12                      # hằng số nhỏ (2 chân, 4 cạnh…) được phép xuất hiện trong lời giải mà không có trong đề
MUC_SAU = {"N": "H", "H": "V", "V": "C", "C": "C"}


def gia_tri(tok):
    return Fraction(tok.replace("\\,", "").replace("{,}", "."))


def viet_so(v, mau_tok=""):
    """Số → LaTeX: phân cách nghìn bằng \\, (như ngân hàng); số thập phân dùng {,}."""
    if v.denominator != 1:
        s = f"{float(v):.6f}".rstrip("0").rstrip(".")
        return s.replace(".", "{,}")
    n = int(v)
    s = str(abs(n))
    if abs(n) >= 1000:
        s = re.sub(r"(?<=\d)(?=(\d{3})+$)", r"\\,", s)
    return ("-" if n < 0 else "") + s


# ------------------------------------------------------------------ phân tích câu mẫu
CHO_PHEP = re.compile(r"^[\s0-9.+\-*/()]*$")


def _bieu_thuc(phan, ten_cua):
    """Một vế (LaTeX) → biểu thức Python theo tên kí hiệu, hoặc None nếu có chữ/kí hiệu lạ."""
    s = phan
    s = re.sub(r"\\[dt]?frac\{([^{}]*)\}\{([^{}]*)\}", r"((\1)/(\2))", s)
    for a, b in ((r"\times", "*"), (r"\cdot", "*"), (r"\div", "/"), (":", "/"), (r"\left", ""), (r"\right", ""),
                 ("−", "-"), ("{", "("), ("}", ")"), ("[", "("), ("]", ")")):
        s = s.replace(a, b)
    toks = []

    def thay(m):
        toks.append(m.group(0)); return f" @{len(toks) - 1}@ "
    s = SO.sub(thay, s.replace("\\,", "\\,"))
    s = re.sub(r"\\[,;:! ]|\\quad|\\qquad", " ", s)
    if not CHO_PHEP.match(re.sub(r"@\d+@", "", s)) or not toks:
        return None, toks
    ten = [ten_cua(t) for t in toks]
    return re.sub(r"@(\d+)@", lambda m: ten[int(m.group(1))], s), toks


def phan_tich(de, lg):
    """→ mô hình {vao, dan, rang_buoc, mau_de, mau_lg} hoặc (None, lý do)."""
    ngoai = re.sub(TOAN, " ", de)
    if re.search(r"\d", re.sub(r"\\[a-zA-Z]+", "", ngoai)):
        return None, "đề có số nằm ngoài công thức"
    if re.search(r"tikzpicture|\\begin\{tabular\}", de + lg):
        return None, "câu có hình / bảng"
    if re.search(r"chữ số|\\overline|\\dots|\\ldots", de):
        return None, "bài về chữ số / dãy số (đổi số dễ sai nghĩa)"
    ky = {}                            # tên → {"bt": biểu thức hoặc None (đầu vào), "v": giá trị gốc}
    theo_gt = {}                       # giá trị → tên (ưu tiên kí hiệu có trước)
    vao = []

    def moi(v, bt=None):
        t = f"s{len(ky)}"
        ky[t] = {"bt": bt, "v": v}
        theo_gt.setdefault(v, t)
        return t
    for m in TOAN.finditer(de):
        for t in SO.findall(m.group(1)):
            v = gia_tri(t)
            if v not in theo_gt:
                vao.append(moi(v))
    if not vao:
        return None, "đề không có số liệu"
    hang = set()

    def ten_cua(tok):
        v = gia_tri(tok)
        if v in theo_gt:
            return theo_gt[v]
        hang.add(v)
        return f"F({v.numerator},{v.denominator})"

    def biet(tok):
        return gia_tri(tok) in theo_gt
    rang_buoc, dung = [], set()
    cuoi = (None, None)                                # vế cuối của công thức trước (cho dòng bắt đầu bằng "= …")
    for m in TOAN.finditer(lg):
        ve = [p.strip() for p in m.group(1).split("=")]
        if len(ve) < 2:
            for t in SO.findall(m.group(1)):          # số đứng riêng (Đáp số: $38$) → phải suy ra được
                ten_cua(t)
            cuoi = (None, None)
            continue
        truoc, truoc_tex = (cuoi if ve[0] == "" else (None, None))   # biểu thức vế trước (đã tính được) và LaTeX của nó
        if ve[0] == "":
            ve = ve[1:]
        for p in ve:
            chi_so = SO.fullmatch(re.sub(r"\s+", "", p))
            if chi_so and truoc is not None:
                v = gia_tri(chi_so.group(0))
                if v in theo_gt:                       # đã có kí hiệu → ràng buộc (vd dòng thử lại) phải luôn đúng
                    rang_buoc.append((truoc, theo_gt[v]))
                    truoc = theo_gt[v]
                else:
                    truoc = moi(v, truoc)
                truoc_tex = p
                continue
            if truoc is not None and truoc_tex is not None:   # vế trung gian "44 + 56" khớp từng số hạng với vế trước "22×2 + 14×4"
                a, b = _so_hang(truoc_tex), _so_hang(p)
                if a and b and len(a) == len(b) and [x[0] for x in a] == [x[0] for x in b]:
                    for (_, ta), (_, tb) in zip(a, b):
                        so_b = SO.fullmatch(re.sub(r"\s+", "", tb))
                        if so_b and not biet(so_b.group(0)):
                            bt_a, _ = _bieu_thuc(ta, ten_cua)
                            if bt_a:
                                moi(gia_tri(so_b.group(0)), bt_a)
            bt, toks = _bieu_thuc(p, ten_cua)
            if bt is None:
                loai = {("v" if gia_tri(t) in theo_gt and theo_gt[gia_tri(t)] in vao else "k" if gia_tri(t) not in theo_gt else "d")
                        for t in SO.findall(p)}
                if "v" in loai and "k" in loai:
                    return None, "công thức chữ trộn số liệu với hằng số (vd a × 8 suy ra từ 'gấp 3 lần')"
                for t in SO.findall(p):
                    ten_cua(t)
                truoc, truoc_tex = None, None
                continue
            if truoc is not None and _eval_goc(bt, ky) is not None and _eval_goc(truoc, ky) is not None:
                rang_buoc.append((bt, truoc))
            dung |= set(re.findall(r"s\d+", bt))
            truoc, truoc_tex = bt, p
        cuoi = (truoc, truoc_tex)
    if any(k["v"] in hang for k in ky.values()):
        return None, "một kết quả trùng giá trị với hằng số trong lời giải (đổi số dễ nhầm)"
    if any(v > HANG_NHO for v in hang):
        return None, "lời giải có số không suy ra được từ đề (" + ", ".join(str(x) for x in sorted(hang) if x > HANG_NHO)[:40] + ")"
    if not set(vao) <= dung:
        return None, "có số liệu trong đề không tham gia phép tính (bài suy luận / đọc số)"
    if not any(ky[t]["bt"] for t in ky):
        return None, "lời giải không có phép tính"
    # kiểm tra lại mô hình trên số liệu gốc
    gt = _tinh(ky, {t: ky[t]["v"] for t in vao})
    if gt is None or any(gt[t] != ky[t]["v"] for t in ky) or not all(_eval(a, gt) == _eval(b, gt) for a, b in rang_buoc):
        return None, "lời giải mẫu chưa khớp phép tính"
    if any(ky[t]["v"].denominator != 1 or ky[t]["v"] < 0 for t in ky):
        return None, "có số thập phân / phân số (Python chỉ đổi số tự nhiên)"
    tron = bool(re.search(r"thuận tiện|tính nhanh|hợp lí|hợp lý", de, re.I))   # bài tính nhanh: kết quả phải giữ "tròn"
    return {"ky": ky, "vao": vao, "rang_buoc": rang_buoc, "hang": hang, "de": de, "lg": lg, "tron": tron}, ""


def _so_hang(tex):
    """Tách các số hạng cấp ngoài cùng theo + / - (bỏ qua trong ngoặc) → [(dấu, số hạng)]."""
    t = tex.strip()
    ra, sau, buf, dau = [], 0, "", "+"
    for ch in t:
        if ch in "({[":
            sau += 1
        elif ch in ")}]":
            sau -= 1
        if ch in "+-−" and sau == 0 and buf.strip():
            ra.append((dau, buf.strip())); buf, dau = "", ("+" if ch == "+" else "-")
            continue
        buf += ch
    if buf.strip():
        ra.append((dau, buf.strip()))
    return ra


def _khong_tan(v):
    """Số chữ số 0 tận cùng (giữ tính 'tròn' của kết quả: bài tính thuận tiện, tiền…)."""
    n = int(v)
    return 0 if n == 0 else len(str(n)) - len(str(n).rstrip("0"))


def _eval_goc(bt, ky):
    return _eval(bt, {t: k["v"] for t, k in ky.items()})


def _eval(bt, gt):
    try:
        return Fraction(eval(bt, {"__builtins__": {}, "F": Fraction}, gt))
    except Exception:
        return None


def _tinh(ky, dau_vao):
    gt = dict(dau_vao)
    for t, k in ky.items():
        if k["bt"] is None:
            continue
        v = _eval(k["bt"], gt)
        if v is None:
            return None
        gt[t] = v
    return gt


# ------------------------------------------------------------------ sinh số liệu mới
def _ung_vien(v, rng, nang_cao):
    v = int(v)
    if v <= 0:
        return v
    z = len(str(v)) - len(str(v).rstrip("0")) if v >= 10 else 0
    buoc = 10 ** z
    if nang_cao:
        lo, hi = int(v * 1.6), int(v * 4) + buoc
    elif v < 10:
        lo, hi = 2, 9
    else:
        d = len(str(v))
        lo, hi = max(10 ** (d - 1), v - max(v // 2, 2 * buoc)), min(10 ** d - 1, v + max(int(v * 0.7), 3 * buoc))
    lo = max(lo, buoc)
    for _ in range(40):
        n = rng.randint(lo // buoc, max(lo // buoc, hi // buoc)) * buoc
        if z == 0 and n % 2 != v % 2:
            n += 1
        if n > 0 and n != v:
            return n
    return None


def sinh(mh, so, rng, nang_cao=False, tranh=(), da_de=None):
    """→ danh sách (đề, lời giải) mới. da_de: tập đề đã sinh (tránh trùng giữa câu giống mẫu và câu nâng cao)."""
    da_de = set() if da_de is None else da_de
    ky, vao, hang = mh["ky"], mh["vao"], mh["hang"]
    ra, da = [], set(tranh)
    goc = tuple(ky[t]["v"] for t in vao)
    da.add(goc)
    for _ in range(4000):
        if len(ra) >= so:
            break
        dv = {}
        for t in vao:
            n = _ung_vien(ky[t]["v"], rng, nang_cao)
            if n is None:
                break
            dv[t] = Fraction(n)
        if len(dv) < len(vao):
            continue
        khoa = tuple(dv[t] for t in vao)
        if khoa in da or len(set(khoa)) < len(set(goc)):
            continue
        if any((goc[i] < goc[j]) != (khoa[i] < khoa[j]) for i in range(len(vao)) for j in range(len(vao)) if i != j):
            continue                                      # giữ thứ tự lớn – bé giữa các số liệu (đề hợp lí như mẫu)
        if any(x <= HANG_NHO and x in hang for x in khoa):       # tránh trùng hằng số nhỏ (dễ đổi nhầm nghĩa)
            continue
        gt = _tinh(ky, dv)
        if gt is None or not all(_eval(a, gt) == _eval(b, gt) for a, b in mh["rang_buoc"]):
            continue
        hong = False
        for t, k in ky.items():
            x, x0 = gt[t], k["v"]
            if x.denominator != 1 or x < 0 or (x0 > 0 and x == 0) or x > 10 ** 8 or (mh["tron"] and _khong_tan(x) < _khong_tan(x0)):
                hong = True; break
        if hong:
            continue
        cac_gt = [gt[t] for t in ky]
        if len(set(cac_gt)) < len(set(k["v"] for k in ky.values())):   # hai đại lượng khác nhau trùng số → dễ hiểu nhầm
            continue
        da.add(khoa)
        doi = {k["v"]: gt[t] for t, k in ky.items()}

        def thay(s):
            return TOAN.sub(lambda m: "$" + SO.sub(lambda n: viet_so(doi.get(gia_tri(n.group(0)), gia_tri(n.group(0))), n.group(0))
                                                   if gia_tri(n.group(0)) in doi else n.group(0), m.group(1)) + "$", s)
        de_moi = thay(mh["de"])
        if de_moi in da_de:
            continue
        da_de.add(de_moi)
        ra.append((de_moi, thay(mh["lg"])))
    return ra


# ------------------------------------------------------------------ khối LaTeX
def khoi_bt(ma_dang, ma_mau, de, lg, nguon, nang_cao):
    de = "\n".join("\t" + x.strip() for x in de.strip().split("\n") if x.strip())
    lg = "\n".join("\t\t" + x.strip() for x in lg.strip().split("\n") if x.strip())
    return (f"\\begin{{bt}}%[{ma_dang}]\n% nguon: {nguon} {ma_mau}\n% mau: {ma_mau}{' nang_cao' if nang_cao else ''}\n"
            f"{de}\n\t\\loigiai{{\n{lg}\n\t}}\n\\end{{bt}}")


def chon_mau_python(ds_dang, theo, rng):
    """theo: {dạng: [câu (dict có _tl, ma, muc_chuan, _mau)]} → {dạng: [(câu mẫu, mô hình)…] theo thứ tự ưu tiên}, {dạng: lý do}."""
    ra, ly_do = {}, {}
    thu_tu = {"N": 0, "H": 1, "V": 2, "C": 3}
    for d in ds_dang:
        ung = [c for c in theo.get(d, []) if not c.get("_mau") and c["_tl"]["lg"]]
        rng.shuffle(ung)
        ung.sort(key=lambda c: ((c.get("so_lan_dung") or 0) > 0, thu_tu.get(c.get("muc_chuan") or "H", 1)))
        lo = []
        for c in ung:
            mh, l = phan_tich(c["_tl"]["de"], c["_tl"]["lg"])
            if mh:
                ra.setdefault(d, []).append((c, mh))
            else:
                lo.append(l)
        if d not in ra:
            ly_do[d] = (lo[0] if lo else "kho chưa có câu tự luận có lời giải")
    return ra, ly_do


def sinh_python(cfg, so, kieu, rng):
    """→ (latex, vi_du_mau, nhật kí)."""
    import phieu_tu_luan, luyen_moi_ngay
    from phieu_bai_hoc import thuoc, hop_le, khoa_noi_dung
    ds = [c for c in map(json.loads, open(os.path.join(GOC, "du-lieu", "chi_muc.jsonl"), encoding="utf-8"))
          if c["loai"] in ("TL", "TLN", "TN") and thuoc(c, cfg["pham_vi"]) and (c["loai"] == "TL" or hop_le(c))
          and (not cfg.get("dang") or c["dang_key"] in cfg["dang"])]
    theo = {}
    for c in ds:
        t = phieu_tu_luan.doi_tu_luan(c)
        if t:
            theo.setdefault(c["dang_key"], []).append(dict(c, _tl=t, _k=khoa_noi_dung(c), _mau=phieu_tu_luan.mau_cua(c)))
    cac_dang = sorted(theo, key=luyen_moi_ngay.khoa_dang)
    mau, ly_do = chon_mau_python(cac_dang, theo, rng)
    n_nc = so if kieu == "nang_cao" else (1 if kieu == "giong_nc" and so > 1 else 0)
    n_g = so - n_nc
    khoi, nk = [], []
    for d in cac_dang:
        if d not in mau:
            nk.append(f"  – {d}: không đổi số tự động được ({ly_do.get(d)}) → dùng 📝 Prompt AI cho dạng này")
            continue
        tot = None
        for c, mh in mau[d][:6]:                         # mẫu đầu sinh không đủ → thử mẫu khác cùng dạng
            da_de = {mh["de"]}
            g = sinh(mh, n_g, rng, da_de=da_de)
            nc = sinh(mh, n_nc, rng, nang_cao=True, da_de=da_de) if n_nc else []
            if tot is None or len(g) + len(nc) > len(tot[2]) + len(tot[3]):
                tot = (c, mh, g, nc)
            if len(g) + len(nc) >= so:
                break
        c, mh, g, nc = tot
        mau[d] = [(c, mh)]
        muc = c.get("muc_chuan") or "H"
        for de, lg in g:
            khoi.append(khoi_bt(d.replace("?", muc), c["ma"], de, lg, "Python sinh từ câu mẫu", False))
        for de, lg in nc:
            khoi.append(khoi_bt(d.replace("?", MUC_SAU.get(muc, "V")), c["ma"], de, lg, "Python sinh (số lớn hơn) từ câu mẫu", True))
        nk.append(f"  ✓ {d}: mẫu {c['ma']} → {len(g)} câu giống mẫu" + (f" + {len(nc)} câu nâng cao" if n_nc else "")
                  + ("" if len(g) + len(nc) >= so else "  (không đủ số liệu đẹp)"))
    return "\n\n".join(khoi), {d: mau[d][0][0]["ma"] for d in mau}, nk


# ------------------------------------------------------------------ AI qua khoá API
KHOA = os.path.join(GOC, "ai_khoa.json")


def doc_khoa():
    try:
        return json.load(open(KHOA, encoding="utf-8"))
    except Exception:
        return {}


def luu_khoa(nha, khoa, mo_hinh=""):
    json.dump({"nha": nha, "khoa": khoa.strip(), "mo_hinh": mo_hinh.strip()}, open(KHOA, "w", encoding="utf-8"))
    gi = os.path.join(GOC, ".gitignore")
    try:
        t = open(gi, encoding="utf-8").read()
        if "ai_khoa.json" not in t:
            open(gi, "a", encoding="utf-8").write("\n# khoá API AI của thầy — không đưa lên git\nai_khoa.json\n")
    except OSError:
        pass


def goi_ai(prompt, k=None, timeout=300):
    """Gửi prompt → văn bản trả về. k: {"nha": "gemini"|"claude", "khoa", "mo_hinh"}."""
    k = k or doc_khoa()
    if not k.get("khoa"):
        raise RuntimeError("Chưa có khoá API AI — bấm ⚙ Khoá AI… trong hộp Phiếu bài học.")
    if k.get("nha") == "claude":
        mo = k.get("mo_hinh") or "claude-sonnet-5-5"
        req = urllib.request.Request("https://api.anthropic.com/v1/messages",
                                     json.dumps({"model": mo, "max_tokens": 16000, "messages": [{"role": "user", "content": prompt}]}).encode(),
                                     {"content-type": "application/json", "x-api-key": k["khoa"], "anthropic-version": "2023-06-01"})
        r = json.load(urllib.request.urlopen(req, timeout=timeout))
        return "".join(x.get("text", "") for x in r.get("content", []))
    def goi(mo):
        req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{mo}:generateContent",
                                     json.dumps({"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.7}}).encode(),
                                     {"content-type": "application/json", "x-goog-api-key": k["khoa"]})
        r = json.load(urllib.request.urlopen(req, timeout=timeout))
        return "".join(p.get("text", "") for c in r.get("candidates", []) for p in c.get("content", {}).get("parts", []))
    try:
        return goi(k.get("mo_hinh") or "gemini-flash-latest")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
        return goi(_gemini_moi_nhat(k["khoa"]))          # tên mô hình đã cũ → lấy bản "flash" mới nhất đang có


def _gemini_moi_nhat(khoa):
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models?pageSize=200", headers={"x-goog-api-key": khoa})
    ds = json.load(urllib.request.urlopen(req, timeout=60)).get("models", [])
    ten = [m["name"].split("/")[-1] for m in ds if "generateContent" in (m.get("supportedGenerationMethods") or [])]
    tot = [t for t in ten if re.fullmatch(r"gemini-[\d.]+-flash", t)] or [t for t in ten if "flash" in t and "lite" not in t] or ten
    if not tot:
        raise RuntimeError("Khoá API không có mô hình Gemini nào dùng được.")
    return max(tot, key=lambda t: [int(x) for x in re.findall(r"\d+", t)] or [0])
