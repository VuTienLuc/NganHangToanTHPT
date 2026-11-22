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


# ------------------------------------------------------------------ AI qua khoá API: nhiều khoá, tự nhận dạng, xoay vòng, tự chạy tiếp khi bị ngắt
import time as _time

KHOA = os.path.join(GOC, "ai_khoa.json")
TEN_NHA = {"gemini": "Gemini", "deepseek": "DeepSeek", "claude": "Claude", "openai": "ChatGPT"}
MO_MAC_DINH = {"gemini": "gemini-flash-latest", "deepseek": "deepseek-chat", "claude": "claude-sonnet-5-5", "openai": "gpt-4.1"}


def nhan_dang(khoa):
    """Đoán nhà cung cấp từ dạng khoá."""
    k = (khoa or "").strip()
    if k.startswith("AIza"):
        return "gemini"
    if k.startswith("sk-ant-"):
        return "claude"
    if k.startswith(("sk-proj-", "sk-svcacct-")):
        return "openai"
    if k.startswith("sk-"):
        return "deepseek"
    return "gemini"


def doc_khoa():
    """→ {"ds": [{"khoa", "nha", "mo_hinh"}…]} (đọc cả kiểu cũ một khoá)."""
    try:
        k = json.load(open(KHOA, encoding="utf-8"))
    except Exception:
        return {"ds": []}
    if "ds" not in k:
        k = {"ds": [{"khoa": k.get("khoa", ""), "nha": k.get("nha") or nhan_dang(k.get("khoa")), "mo_hinh": k.get("mo_hinh", "")}] if k.get("khoa") else []}
    k["ds"] = [x for x in k["ds"] if x.get("khoa")]
    return k


def luu_khoa(van, mo_hinh=None, them=False):
    """van: chuỗi nhiều khoá (cách nhau xuống dòng / dấu phẩy / khoảng trắng); có thể ghi 'deepseek:sk-…' hoặc 'gemini@gemini-3.5-flash:AIza…'."""
    ds = doc_khoa()["ds"] if them else []
    da = {x["khoa"] for x in ds}
    for tok in re.split(r"[\s,;]+", van or ""):
        if not tok:
            continue
        nha, mo = None, ""
        m = re.match(r"^(gemini|deepseek|claude|openai)(?:@([\w.\-]+))?:(.+)$", tok, re.I)
        if m:
            nha, mo, tok = m.group(1).lower(), m.group(2) or "", m.group(3)
        if tok in da or len(tok) < 20:
            continue
        da.add(tok)
        ds.append({"khoa": tok, "nha": nha or nhan_dang(tok), "mo_hinh": mo or (mo_hinh or {}).get(nha or nhan_dang(tok), "")})
    cu = doc_khoa()
    cu.pop("khoa", None); cu.pop("nha", None); cu.pop("mo_hinh", None)
    cu["ds"] = ds                                            # giữ các mục khác (vd "vai" của Hội đồng AI)
    json.dump(cu, open(KHOA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    gi = os.path.join(GOC, ".gitignore")
    try:
        t = open(gi, encoding="utf-8").read()
        if "ai_khoa.json" not in t:
            open(gi, "a", encoding="utf-8").write("\n# khoá API AI của thầy — không đưa lên git\nai_khoa.json\n")
    except OSError:
        pass
    return ds


def che(khoa):
    return khoa[:6] + "…" + khoa[-4:]


class HetKhoa(RuntimeError):
    pass


_SSL = None


def ngu_canh_ssl():
    """Chứng chỉ HTTPS: Python cài từ python.org trên macOS không dùng kho chứng chỉ của máy → lỗi CERTIFICATE_VERIFY_FAILED.
    Thứ tự: gói certifi → /etc/ssl/cert.pem (macOS, Linux) → mặc định. Vẫn KIỂM TRA chứng chỉ, không tắt bảo mật."""
    global _SSL
    if _SSL is None:
        import ssl
        cac = []
        try:
            import certifi
            cac.append(certifi.where())
        except Exception:
            pass
        cac += ["/etc/ssl/cert.pem", "/etc/ssl/certs/ca-certificates.crt", "/opt/homebrew/etc/openssl@3/cert.pem", "/usr/local/etc/openssl@3/cert.pem"]
        _SSL = ssl.create_default_context()
        for f in cac:
            if f and os.path.isfile(f):
                try:
                    _SSL = ssl.create_default_context(cafile=f)
                    break
                except Exception:
                    continue
    return _SSL


def _http(url, body, headers, timeout):
    req = urllib.request.Request(url, json.dumps(body).encode() if body is not None else None, {"content-type": "application/json", **headers})
    return json.load(urllib.request.urlopen(req, timeout=timeout, context=ngu_canh_ssl()))


def goi_mot(k, prompt, timeout=240, max_tok=8000):
    """Gọi MỘT khoá → (văn bản, bị_cắt)."""
    nha, khoa, mo = k["nha"], k["khoa"], k.get("mo_hinh") or MO_MAC_DINH.get(k["nha"])
    if nha == "claude":
        def cla(m):
            r = _http("https://api.anthropic.com/v1/messages", {"model": m, "max_tokens": max_tok, "messages": [{"role": "user", "content": prompt}]},
                      {"x-api-key": khoa, "anthropic-version": "2023-06-01"}, timeout)
            return "".join(x.get("text", "") for x in r.get("content", [])), r.get("stop_reason") == "max_tokens"
        try:
            return cla(mo)
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
            k["mo_hinh"] = _moi_nhat(nha, khoa)            # tên mô hình đã cũ → bản Claude mới nhất đang có
            return cla(k["mo_hinh"])
    if nha in ("deepseek", "openai"):
        url = "https://api.deepseek.com/chat/completions" if nha == "deepseek" else "https://api.openai.com/v1/chat/completions"
        def oai(m, gon=False):
            body = {"model": m, "messages": [{"role": "user", "content": prompt}], "stream": False}
            if nha == "openai":                            # OpenAI đời mới: max_completion_tokens; mô hình suy luận không nhận temperature
                body["max_completion_tokens"] = max_tok
                if not gon:
                    body["temperature"] = 0.7
            else:
                body.update(max_tokens=max_tok, temperature=0.7) if not m.endswith("reasoner") else body.update(max_tokens=max_tok)
            r = _http(url, body, {"authorization": "Bearer " + khoa}, timeout)
            c = (r.get("choices") or [{}])[0]
            return (c.get("message") or {}).get("content") or "", c.get("finish_reason") in ("length", "insufficient_system_resource")
        try:
            return oai(mo)
        except urllib.error.HTTPError as e:
            try:
                noi = e.read().decode("utf-8", "ignore")
            except Exception:
                noi = ""
            if nha == "openai" and e.code == 400 and "temperature" in noi:
                return oai(mo, gon=True)
            if nha == "openai" and (e.code == 404 or (e.code == 400 and "model" in noi and "not" in noi)):
                k["mo_hinh"] = _moi_nhat(nha, khoa)
                return oai(k["mo_hinh"], gon=True)
            raise urllib.error.HTTPError(e.url, e.code, e.msg, e.hdrs, __import__("io").BytesIO(noi.encode()))

    def gem(m):
        r = _http(f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent",
                  {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.7, "maxOutputTokens": max_tok}},
                  {"x-goog-api-key": khoa}, timeout)
        c = (r.get("candidates") or [{}])[0]
        return "".join(p.get("text", "") for p in (c.get("content") or {}).get("parts", [])), c.get("finishReason") == "MAX_TOKENS"
    try:
        return gem(mo)
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
        k["mo_hinh"] = _gemini_moi_nhat(khoa)              # tên mô hình đã cũ → bản "flash" mới nhất đang có
        return gem(k["mo_hinh"])


def _moi_nhat(nha, khoa):
    """OpenAI / Claude: tên mô hình mặc định đã cũ → lấy danh sách mô hình của khoá, chọn bản mới nhất phù hợp."""
    if nha == "openai":
        ds = [m["id"] for m in _http("https://api.openai.com/v1/models", None, {"authorization": "Bearer " + khoa}, 60).get("data", [])]
        tot = [t for t in ds if re.fullmatch(r"gpt-\d+(\.\d+)?", t)] or [t for t in ds if t.startswith("gpt-") and not re.search(r"audio|realtime|image|tts|search|transcribe|nano", t)]
    else:
        ds = [m["id"] for m in _http("https://api.anthropic.com/v1/models?limit=100", None, {"x-api-key": khoa, "anthropic-version": "2023-06-01"}, 60).get("data", [])]
        tot = [t for t in ds if "sonnet" in t] or ds
    if not tot:
        raise RuntimeError(f"Khoá {TEN_NHA.get(nha, nha)} không có mô hình phù hợp.")
    return max(tot, key=lambda t: [int(x) for x in re.findall(r"\d+", t)[:3]] or [0])


def _gemini_moi_nhat(khoa):
    ds = _http("https://generativelanguage.googleapis.com/v1beta/models?pageSize=200", None, {"x-goog-api-key": khoa}, 60).get("models", [])
    ten = [m["name"].split("/")[-1] for m in ds if "generateContent" in (m.get("supportedGenerationMethods") or [])]
    tot = [t for t in ten if re.fullmatch(r"gemini-[\d.]+-flash", t)] or [t for t in ten if "flash" in t and "lite" not in t] or ten
    if not tot:
        raise RuntimeError("Khoá API không có mô hình Gemini nào dùng được.")
    return max(tot, key=lambda t: [int(x) for x in re.findall(r"\d+", t)] or [0])


class XoayKhoa:
    """Dùng lần lượt các khoá; khoá hết lượt / lỗi thì nghỉ một lúc và chuyển khoá khác; tất cả đang nghỉ thì chờ."""
    NGHI = {401: 3600, 403: 3600, 402: 3600, 429: 60, "mang": 20, "khac": 30}

    def __init__(self, ds=None, ghi=print, timeout=240, max_tok=8000):
        self.ds = [dict(x) for x in (ds if ds is not None else doc_khoa()["ds"])]
        self.timeout, self.max_tok = timeout, max_tok
        if not self.ds:
            raise HetKhoa("Chưa có khoá API AI — bấm ⚙ Khoá AI… trong hộp Phiếu bài học.")
        self.nghi = {}
        self.i = 0
        self.ghi = ghi

    def goi(self, prompt, cho_toi_da=180):
        bat_dau = _time.time()
        while True:
            now = _time.time()
            for _ in range(len(self.ds)):
                k = self.ds[self.i % len(self.ds)]
                if self.nghi.get(k["khoa"], 0) <= now:
                    try:
                        t, cat = goi_mot(k, prompt, timeout=self.timeout, max_tok=self.max_tok)
                        if not t.strip():
                            raise RuntimeError("trả về rỗng")
                        return t, cat, k
                    except urllib.error.HTTPError as e:
                        try:
                            noi = e.read().decode("utf-8", "ignore")[:160]
                        except Exception:
                            noi = ""
                        lau = self.NGHI.get(e.code, self.NGHI["khac"] if e.code >= 500 else 60)
                        if e.code in (400, 429) and re.search(r"quota|billing|exhaust|balance|insufficient|per.?day|API key", noi, re.I):
                            lau = 3600                       # hết hạn mức ngày / hết tiền / sai khoá → bỏ khoá này lâu
                        self.nghi[k["khoa"]] = _time.time() + lau
                        self.ghi(f"    ↪ {TEN_NHA.get(k['nha'], k['nha'])} {che(k['khoa'])}: lỗi {e.code}"
                                 f"{' (hết lượt / sai khoá)' if lau >= 3600 else ' (quá tải, nghỉ ' + str(lau) + 's)'} → đổi khoá")
                    except Exception as e:
                        self.nghi[k["khoa"]] = _time.time() + self.NGHI["mang"]
                        self.ghi(f"    ↪ {TEN_NHA.get(k['nha'], k['nha'])} {che(k['khoa'])}: {str(e)[:80]} → đổi khoá")
                self.i += 1
            con = [v for v in self.nghi.values() if v > _time.time()]
            if len(con) >= len(self.ds) and min(con) - _time.time() > 600:
                raise HetKhoa("Mọi khoá API đều hết lượt hoặc sai khoá. Thầy thêm khoá khác ở ⚙ Khoá AI…")
            if _time.time() - bat_dau > cho_toi_da:
                raise HetKhoa("Các khoá API đang quá tải lâu — thử lại sau.")
            cho = max(2, min(30, (min(con) - _time.time()) if con else 2))
            self.ghi(f"    … mọi khoá đang nghỉ, chờ {int(cho)}s")
            _time.sleep(cho)


KHOI_BT = re.compile(r"\\begin\{bt\}.*?\\end\{bt\}", re.S)


def tach_khoi_ai(t):
    """Lấy các khối \\begin{bt}…\\end{bt} HOÀN CHỈNH (khối bị cắt dở ở cuối thì bỏ)."""
    t = re.sub(r"```(?:latex|tex)?", "", t or "")
    ra = []
    for k in KHOI_BT.findall(t):
        than = k[k.find("\\loigiai"):] if "\\loigiai" in k else ""
        if not than or than.count("{") != than.count("}"):
            continue
        ra.append(k)
    return ra


def _de_cua(k):
    t = re.sub(r"^\\begin\{bt\}[^\n]*\n", "", k)
    t = "\n".join(x for x in t.split("\n") if not x.strip().startswith("%"))
    return re.sub(r"\s+", " ", t.split("\\loigiai")[0]).strip()


def sinh_ai(mau, so, kieu, lop, ghi=print, xoay=None, lan_toi_da=6, hoi_dong=None):
    """mau: [{"ma", "dang_key", "muc", "ten_dang", "ten_bai", "de", "lg"}] → (danh sách khối LaTeX, {dạng: mã mẫu}).
    Mỗi lượt gọi CHỈ MỘT mẫu (câu trả lời ngắn, ít bị ngắt); thiếu câu (bị cắt / AI trả thiếu) → tự hỏi tiếp phần còn thiếu."""
    import tao_prompt
    xoay = xoay or XoayKhoa(ghi=ghi)
    n_nc = so if kieu == "nang_cao" else (1 if kieu == "giong_nc" and so > 1 else 0)
    ra, vdm = [], {}
    for j, m in enumerate(mau, 1):
        can = {"giong": so - n_nc, "nang_cao": n_nc}
        co = {"giong": [], "nang_cao": []}
        da_de = {re.sub(r"\s+", " ", m["de"]).strip()}
        ghi(f"  [{j}/{len(mau)}] {m['dang_key']} · mẫu {m['ma']}: cần {can['giong']} giống mẫu" + (f" + {can['nang_cao']} nâng cao" if n_nc else ""))
        for lan in range(lan_toi_da):
            loai = "giong" if len(co["giong"]) < can["giong"] else ("nang_cao" if len(co["nang_cao"]) < can["nang_cao"] else None)
            if not loai:
                break
            thieu = can[loai] - len(co[loai])
            p = tao_prompt.prompt_tuong_tu([m], thieu, loai, lop)
            if da_de and lan:
                p += "\n\n# KHÔNG LẶP LẠI các đề đã có sau (soạn câu MỚI, số liệu khác):\n" + "\n".join("- " + d[:160] for d in list(da_de)[:12])
            try:
                t, cat, k = xoay.goi(p)
            except HetKhoa:
                raise
            moi = 0
            for kb in tach_khoi_ai(t):
                nc = bool(re.search(r"%\s*mau:\s*[0-9a-f]{8}\s+nang_cao", kb)) or loai == "nang_cao"
                if not re.search(r"%\s*mau:", kb):              # AI quên dòng mẫu → tự thêm
                    kb = re.sub(r"(\\begin\{bt\}[^\n]*\n)", r"\1% mau: " + m["ma"] + (" nang_cao" if nc else "") + "\n", kb, count=1)
                kb = re.sub(r"%\s*mau:\s*[0-9a-f]{8}", "% mau: " + m["ma"], kb)
                d = _de_cua(kb)
                lo = "nang_cao" if nc else "giong"
                if not d or d in da_de or len(co[lo]) >= can[lo]:
                    continue
                da_de.add(d); co[lo].append(kb); moi += 1
            ghi(f"    lượt {lan + 1} ({TEN_NHA.get(k['nha'], k['nha'])} {che(k['khoa'])}): +{moi} câu"
                + (" · bị ngắt giữa chừng → hỏi tiếp phần còn thiếu" if cat else "")
                + f" · có {len(co['giong'])}/{can['giong']}" + (f" + {len(co['nang_cao'])}/{can['nang_cao']}" if n_nc else ""))
        if hoi_dong and (co["giong"] or co["nang_cao"]):     # Hội đồng AI giải lại – phản biện – biên tập trước khi nhận
            qua = hoi_dong.duyet(co["giong"] + co["nang_cao"], muc=m.get("muc") or "",
                                 ngu_canh=f"Toán lớp {lop}, {m.get('ten_bai') or ''} — dạng {m.get('ten_dang') or m['dang_key']}. "
                                          f"Câu phải CÙNG DẠNG với câu mẫu (câu ghi 'nang_cao' ở dòng % mau được phép khó hơn một chút). Câu mẫu: "
                                          + re.sub(r"\s+", " ", m["de"])[:500])
            co = {"giong": [k for k in qua if not re.search(r"%\s*mau:\s*\S+\s+nang_cao", k)],
                  "nang_cao": [k for k in qua if re.search(r"%\s*mau:\s*\S+\s+nang_cao", k)]}
        if co["giong"] or co["nang_cao"]:
            ra += co["giong"] + co["nang_cao"]; vdm[m["dang_key"]] = m["ma"]
        if len(co["giong"]) < can["giong"] or len(co["nang_cao"]) < can["nang_cao"]:
            ghi("    ⚠ chưa đủ số câu sau nhiều lượt — giữ các câu đã có")
    return ra, vdm


def goi_ai(prompt, k=None, timeout=300):
    """Tương thích cũ: gọi lần lượt các khoá, trả văn bản."""
    t, _, _ = XoayKhoa([k] if k else None, ghi=lambda x: None).goi(prompt)
    return t


def kiem_tra_khoa(ghi=print):
    """Gọi thử từng khoá với câu rất ngắn → [(nhà, khoá che, ok, ghi chú)]."""
    ra = []
    for k in doc_khoa()["ds"]:
        try:
            t, _ = goi_mot(dict(k), "Trả lời đúng một từ: OK", timeout=60, max_tok=20)
            ra.append((TEN_NHA.get(k["nha"], k["nha"]), che(k["khoa"]), True, (k.get("mo_hinh") or MO_MAC_DINH.get(k["nha"])) + " · " + t.strip()[:20]))
        except urllib.error.HTTPError as e:
            ra.append((TEN_NHA.get(k["nha"], k["nha"]), che(k["khoa"]), False, f"lỗi {e.code}"))
        except Exception as e:
            ra.append((TEN_NHA.get(k["nha"], k["nha"]), che(k["khoa"]), False, str(e)[:60]))
    return ra
