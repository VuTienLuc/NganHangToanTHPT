# -*- coding: utf-8 -*-
"""PHIẾU HOẠT ĐỘNG — dạy học vui hơn, hiệu quả hơn (menu Dạy học → 🎲 Phiếu hoạt động).

  🔐 Mật mã          mỗi câu đúng cho 1 chữ cái → ghép thành thông điệp bí mật (tự kiểm tra: sai là chữ vô nghĩa).
                     Câu TN: nhãn phương án là chữ cái; câu trả lời ngắn: tra đáp số trong bảng giải mã.
  🔍 Tìm lỗi sai     lời giải "của bạn An" có MỘT bước sai (lỗi thường gặp) → học sinh tìm bước sai, giải thích, sửa.
                     Nội dung lấy từ kho lỗi sai du-lieu/tim_loi_sai/<dạng>.json (AI tạo từ lời giải đúng trong ngân hàng).
  🔄 Ôn tập ngắt quãng  ~70% bài hôm nay + ~30% dạng đã học 1 tuần / 2 tuần / 1 tháng trước (theo lịch sử đề đã ra hoặc thầy chọn).
Prompt AI: sinh câu JSON nhập ngân hàng (Mật mã, Ôn tập) · sinh lời giải có lỗi nhập kho lỗi sai (Tìm lỗi sai).
"""
import os, re, json, time, random, shutil, datetime, collections, unicodedata
from nh_core import GOC, doc as doc_tep, ghi, cau_hinh, thu_muc_xuat, tai_id_map, chuan_vecto

KHO_LOI = os.path.join(GOC, "du-lieu", "tim_loi_sai")
KHO_IN = {"tiet_kiem": ("11", "left=1.2cm,right=1.1cm,top=1.0cm,bottom=1.4cm,footskip=0.6cm"),
          "binh_thuong": ("12", "left=1.8cm,right=1.6cm,top=1.4cm,bottom=1.6cm,footskip=0.7cm")}
THU_MUC = {"N": 0, "H": 1, "V": 2, "C": 3}
CHU = list("ABCDEGHIKLMNOPQRSTUVXY") + ["Ă", "Â", "Đ", "Ê", "Ô", "Ơ", "Ư"]
THONG_DIEP_MAU = ["TOÁN HỌC THẬT VUI", "CỐ GẮNG LÊN NHÉ", "HỌC TẬP CHĂM CHỈ", "EM LÀM ĐƯỢC", "KIÊN TRÌ SẼ THÀNH CÔNG",
                  "TOÁN LÀ CHÌA KHÓA", "MỖI NGÀY MỘT TIẾN BỘ"]


def thoat(s):
    from phieu_bai_hoc import thoat as t
    return t(s)


def _kho():
    from xem_truoc import kho
    return kho()


def _lich_su():
    p = os.path.join(GOC, "du-lieu", "lich_su_dung.json")
    try:
        return json.load(open(p, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _tach(c):
    from k12word import tach_cau
    try:
        p = tach_cau(c)
    except Exception:
        return None
    p["de"] = chuan_vecto(p.get("de") or "")[0].strip()
    p["lg"] = chuan_vecto(p.get("lg") or "")[0].strip()
    if p.get("pa"):
        p["pa"] = [chuan_vecto(x)[0] for x in p["pa"]]
    return p


_CHI = None          # tập mã: phiếu CHỈ dùng các câu AI vừa sinh & nhập (cfg["chi_ma"]), không rút thêm từ ngân hàng


def _dat_chi(cfg):
    global _CHI
    _CHI = set(cfg.get("chi_ma") or []) or None
    return _CHI is not None


def _ung_vien(dang, loai, muc=None, tranh=(), giu_muc=False):
    """Câu hợp lệ của các dạng; xếp: câu chưa dùng trước, ngẫu nhiên trong nhóm.
    Đang ở chế độ 'chỉ câu AI vừa nhập' (_CHI): chỉ lấy các mã đó và bỏ lọc mức (trừ khi giu_muc — vd chia bậc Leo núi)."""
    from xem_truoc import hop_le
    ls, tr = _lich_su(), set(tranh)
    if _CHI is not None and not giu_muc:
        muc = None
    ds = [c for c in _kho().values() if c.get("dang_key") in dang and c.get("loai") in loai and hop_le(c)
          and c["ma"] not in tr and (not muc or (c.get("muc_chuan") or "H") in muc) and (_CHI is None or c["ma"] in _CHI)]
    random.shuffle(ds)
    ds.sort(key=lambda c: bool(ls.get(c["ma"])))
    return ds


def _xoay_vong(theo_dang, can):
    """Lấy lần lượt mỗi dạng một câu cho đủ `can` câu (rải đều các dạng)."""
    ra, i = [], 0
    hang = [list(v) for v in theo_dang.values() if v]
    while len(ra) < can and any(hang):
        h = hang[i % len(hang)]
        if h:
            ra.append(h.pop(0))
        i += 1
    return ra


# ------------------------------------------------------------------ tài liệu chung
def _tai_lieu(cfg, nhan, ten, noi_hs, noi_gv, phu, dang_keys, hai_cot=False):
    """Dựng 2 file PhieuHoatDong.tex (học sinh) + PhieuHoatDong_LoiGiai.tex theo mẫu trình bày đã chọn."""
    import mau_phieu
    from phieu_bai_hoc import ten_tep, tieu_de_ten
    tt = {**cau_hinh().get("thong_tin_de", {}), **{k: v for k, v in cfg.items() if v not in (None, "")}}
    gv = (tt.get("giao_vien") or "").strip()
    co, le = KHO_IN.get(cfg.get("kho")) or KHO_IN["tiet_kiem"]
    out_goc = thu_muc_xuat(ten_tep(f"{nhan.title()} - {ten} - {time.strftime('%d-%m-%Y')}", 90), list(dang_keys) or None, "phieu")
    out = os.path.join(out_goc, "tex")
    os.makedirs(out_goc)
    src = os.path.join(GOC, "khung", "DeThiChinhThuc")
    shutil.copytree(src, out, ignore=shutil.ignore_patterns("mau_de.tex", "*.bat"))
    mau = doc_tep(os.path.join(src, "mau_de.tex"))
    for a, v in {"<<SO_GD>>": tt.get("so_gd", ""), "<<TRUONG>>": tt.get("truong", ""), "<<TEN_KY_THI>>": ten,
                 "<<NAM_HOC>>": tt.get("nam_hoc", ""), "<<MON>>": "TOÁN", "<<THOI_GIAN>>": "", "<<CHAN_TRANG>>": ten}.items():
        mau = mau.replace(a, thoat(v))
    mau = re.sub(r"\\documentclass\[\d+pt,", f"\\\\documentclass[{co}pt,", mau, count=1)
    mau = re.sub(r"\\usepackage\[a4paper,[^\]]*\]\{geometry\}", lambda m: "\\usepackage[a4paper," + le + "]{geometry}", mau, count=1)
    mau = mau.replace("\\setlength{\\parskip}{6pt}", "\\setlength{\\parskip}{3pt}")
    chan = thoat(f"{nhan.title()}: {ten}"[:70])
    them = [r"%==================== PHIẾU HOẠT ĐỘNG ====================",
            r"\pagestyle{fancy}\fancyhf{}\renewcommand{\headrulewidth}{0pt}\renewcommand{\footrulewidth}{0.4pt}",
            r"\fancyfoot[L]{\footnotesize " + ("GV: " + thoat(gv) if gv else "") + r"}\fancyfoot[C]{\footnotesize " + chan + r"}"
            r"\fancyfoot[R]{\footnotesize Trang \thepage/\pageref{trangCuoiPhieu}}",
            r"\fancypagestyle{plain}{\fancyhf{}\fancyfoot[L]{\footnotesize " + ("GV: " + thoat(gv) if gv else "") +
            r"}\fancyfoot[R]{\footnotesize Trang \thepage/\pageref{trangCuoiPhieu}}}",
            mau_phieu.mo_dau(cfg.get("mau_trinh_bay")),
            r"\newcommand{\oChu}[2]{\tikz[reset cm,baseline=0]{\draw[mauPhieu,line width=0.8pt,rounded corners=1.2pt] (0,0) rectangle (0.82,0.9);"
            r"\node[font=\scriptsize,text=black!60] at (0.41,-0.25){#1};}}",
            r"\newcommand{\hopNhom}[1]{\par\smallskip\noindent{\color{mauDang}\bfseries #1}\par\nopagebreak}",
            r"\usepackage{multicol}\setlength{\columnsep}{0.6cm}\setlength{\columnseprule}{0.3pt}"]
    mau = mau.replace("\\begin{document}", "\n".join(them) + "\n\\begin{document}", 1)
    def dau(tieu, ho_ten, phu_=None, ten_=None):
        return (r"\dauPhieuKhung{" + thoat(tt.get("truong") or "") + "}{" + thoat(tt.get("nam_hoc") or "") + "}{" + tieu + "}{"
                + tieu_de_ten(ten_ or ten, thoat) + "}{" + (phu_ if phu_ is not None else phu) + "}{" + ("1" if ho_ten else "0") + "}")
    # phiếu nhiều tờ (vd Mảnh ghép): mỗi tờ tự đặt đầu phiếu bằng <<DAU|tiêu đề|tên|dòng phụ>>
    tu_dau = noi_hs.lstrip().startswith("<<DAU|")
    noi_hs = re.sub(r"<<DAU\|(.*?)\|(.*?)\|(.*?)>>", lambda m: dau(m.group(1), True, m.group(3), m.group(2)), noi_hs)
    ky = (r"\par\bigskip\noindent\hfill{\small\itshape Giáo viên: }{\small\bfseries " + thoat(gv) + r"}\par" if gv else "")
    bat, tat = ("\\begin{multicols}{2}\n", "\n\\end{multicols}") if hai_cot and co == "11" else ("", "")
    het = "\n\\par\\bigskip\\begin{center}{\\small\\itshape --- Hết ---}\\end{center}" + ky + "\n\\label{trangCuoiPhieu}\n"
    ghi(os.path.join(out, "PhieuHoatDong.tex"), mau_phieu.gan_bieu_tuong(
        mau.replace("<<CHE_DO_LOI_GIAI>>", "\\anloigiai").replace("<<NOI_DUNG>>", ("" if tu_dau else dau(nhan, True) + "\n") + bat + noi_hs + tat + het)))
    ghi(os.path.join(out, "PhieuHoatDong_LoiGiai.tex"), mau_phieu.gan_bieu_tuong(
        mau.replace("<<CHE_DO_LOI_GIAI>>", "\\hienthiloigiai").replace("<<NOI_DUNG>>", dau("ĐÁP ÁN – " + nhan, False) + "\n" + noi_gv + het)))
    ghi(os.path.join(out, "_ten_phieu.txt"), ten_tep(f"{nhan.title()} - {ten}", 90))
    json.dump(cfg, open(os.path.join(out, "cau_hinh_phieu_hoat_dong.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return out_goc


def _phu(dang_keys, them=""):
    id_map = tai_id_map()
    bai = collections.OrderedDict()
    for d in dang_keys:
        v = id_map.get(d, {})
        bai.setdefault((v.get("lesson_name") or d.split("-")[0]).strip(), 1)
    lop = ""
    if dang_keys:
        from nh_core import lop_tu_so
        lop = f"Toán {lop_tu_so(sorted(dang_keys)[0][0])} · "
    ten = "; ".join(list(bai)[:2]) + (f" (+{len(bai) - 2} bài)" if len(bai) > 2 else "")
    return thoat(lop + ten + (" · " + them if them else ""))


def _cau_tn(c, nhan=None, so=None, hep=False):
    """Câu TN in thường: đề + 4 phương án (nhãn A–D hoặc nhãn chữ cho Mật mã)."""
    p = _tach(c)
    nh = nhan or list("ABCD")
    o = [r"\fbox{\textbf{" + nh[i] + r"}}\ " + p["pa"][i] for i in range(4)]
    dai = max(len(re.sub(r"\\(?:dfrac|frac|left|right|limits)|[{}$\s]", "", re.sub(r"\\(?:overrightarrow|vec|sqrt|mathbb)", "##", x))) for x in p["pa"])
    gioi = 7 if hep else 13                       # độ dài phương án dài nhất → 4 / 2 / 1 phương án mỗi dòng
    if dai <= gioi:
        bang = r"\par\noindent" + "".join(r"\makebox[0.25\linewidth][l]{" + x + "}" for x in o)
    elif dai <= 2.3 * gioi:
        bang = (r"\par\noindent\begin{tabular}{@{}p{0.48\linewidth}@{\hspace{0.02\linewidth}}p{0.48\linewidth}@{}}" + o[0] + " & " + o[1]
                + r"\\[2pt]" + o[2] + " & " + o[3] + r"\end{tabular}")
    else:
        bang = r"\par" + "".join(r"\noindent " + x + r"\par" for x in o)
    return r"\par\smallskip\noindent\textbf{\color{mauPhieu}Câu " + str(so) + r".}\ " + p["de"] + bang + r"\par"


def _cau_tln(c, so):
    p = _tach(c)
    return (r"\par\smallskip\noindent\textbf{\color{mauPhieu}Câu " + str(so) + r".}\ " + p["de"]
            + r"\par\noindent\hfill{\small Đáp số:}\ \makebox[2.6cm]{\dotfill}\par")


def _cau_tl(c, so, dong=3):
    p = _tach(c)
    return r"\par\smallskip\noindent\textbf{\color{mauPhieu}Câu " + str(so) + r".}\ " + p["de"] + r"\dongKe{" + str(dong) + "}"


def _dap(c):
    if c["loai"] == "TN":
        return c.get("dap_an") or ""
    if c["loai"] == "TLN":
        return (c.get("dap_an") or "").strip()
    return ""


# ------------------------------------------------------------------ 🔐 MẬT MÃ
def _so(x):
    try:
        return float(str(x).replace(",", ".").replace("−", "-"))
    except ValueError:
        return None


def _viet_so(v, mau):
    """Viết số nhiễu giống kiểu đáp số gốc (số chữ số thập phân, dấu phẩy)."""
    n = len(mau.split(",")[1]) if "," in mau else 0
    t = f"{v:.{n}f}".replace(".", ",")
    return t if len(t) <= 4 else None


def mat_ma(cfg, in_ra=print):
    dang = list(cfg.get("dang") or [])
    if not dang:
        raise ValueError("Chưa chọn dạng.")
    td = re.sub(r"\s+", " ", (cfg.get("thong_diep") or random.choice(THONG_DIEP_MAU)).upper()).strip()
    chu = [ch for ch in td if not ch.isspace()]
    if not 3 <= len(chu) <= 32:
        raise ValueError("Thông điệp cần 3–32 chữ cái (không tính dấu cách).")
    rng = random.Random(cfg.get("seed") or time.time()); random.seed(rng.random())
    chi = _dat_chi(cfg)
    muc = set(cfg.get("muc") or ["N", "H"])
    loai = ["TN", "TLN"] if cfg.get("co_tln", True) else ["TN"]
    hang = [sorted(_ung_vien([d], loai, muc), key=lambda c: c["loai"] != "TN") for d in dang]   # ưu tiên câu TN
    hs, bang_giai, dung_tln, dap, cau = [], {}, {}, [], []
    k = 0
    for l in chu:
        c = None
        for _ in range(len(hang)):                    # xoay vòng các dạng; bỏ câu TLN trùng đáp số với câu khác
            h = hang[k % len(hang)]; k += 1
            while h:
                x = h.pop(0)
                if x["loai"] == "TLN":
                    dsv = (x.get("dap_an") or "").strip()
                    if dsv in dung_tln and dung_tln[dsv] != l:
                        continue
                c = x; break
            if c:
                break
        if not c:
            break
        cau.append((c, l))
    if len(cau) < len(chu) and chi:
        raise ValueError(f"Thông điệp {len(chu)} chữ nhưng AI mới sinh {len(cau)} câu dùng được (TN / trả lời ngắn không trùng đáp số) "
                         f"— rút thông điệp còn ≤ {len(cau)} chữ, hoặc bỏ tích “Chỉ dùng câu AI vừa nhập”.")
    if len(cau) < len(chu):
        raise ValueError(f"Thông điệp {len(chu)} chữ nhưng kho chỉ có {len(cau)} câu phù hợp (TN"
                         + (" / trả lời ngắn" if "TLN" in loai else "") + f", mức {'/'.join(sorted(muc))}) cho các dạng đã chọn. "
                         "Rút ngắn thông điệp, chọn thêm dạng, hoặc dùng 📝 Prompt AI sinh câu rồi nhập ngân hàng.")
    for i, (c, l) in enumerate(cau, 1):
        if c["loai"] == "TN":
            dung = "ABCD".index(c["dap_an"])
            nhieu = rng.sample([x for x in CHU if x != l], 3)
            hs.append(_cau_tn(c, nhieu[:dung] + [l] + nhieu[dung:], i))
            dap.append((i, f"{c['dap_an']} → {l}", c))
        else:
            dsv = (c.get("dap_an") or "").strip()
            dung_tln[dsv] = l; bang_giai[dsv] = l
            v, n = _so(dsv), 0
            for x in ((v + 1, v - 1, -v, 2 * v, v + 2, v - 2) if v is not None else ()):
                t = _viet_so(x, dsv)
                if t and t not in bang_giai and t not in dung_tln:
                    bang_giai[t] = rng.choice([y for y in CHU if y != l]); n += 1
                    if n >= 2:
                        break
            hs.append(_cau_tln(c, i))
            dap.append((i, f"{dsv} → {l}", c))
    cau = [c for c, _ in cau]
    # ô giải mã: chữ theo từng từ, dưới mỗi ô là số câu
    k, o = 0, []
    for tu in td.split(" "):
        o.append(r"\mbox{" + r"\,".join(r"\oChu{" + str(k + j + 1) + "}{}" for j in range(len(tu))) + "}")
        k += len(tu)
    giai_ma = (r"\phanPhieu[\faKey]{GIẢI MÃ THÔNG ĐIỆP}" + "\n"
               r"{\small Làm từng câu, ghi \textbf{chữ cái} của đáp án đúng vào ô có số thứ tự của câu. Đọc thông điệp — nếu chữ ghép lại "
               r"vô nghĩa thì có câu sai, hãy kiểm tra lại!}\par\medskip\noindent" + r"\hspace{6mm}".join(o) + r"\par\vspace{6mm}")
    bang = ""
    if bang_giai:
        ds = sorted(bang_giai.items(), key=lambda kv: (_so(kv[0]) if _so(kv[0]) is not None else 1e9, kv[0]))
        cot = 6
        dong = [ds[j:j + cot] for j in range(0, len(ds), cot)]
        bang = (r"\par\medskip\noindent{\bfseries\color{mauDang}Bảng giải mã cho câu trả lời ngắn:} {\small tìm đáp số của em, lấy chữ cái bên cạnh.}\par\smallskip"
                r"\noindent\begin{tabular}{" + "|c|c" * cot + "|}\\hline " +
                r"\\\hline ".join(" & ".join("$" + a.replace(",", "{,}") + "$ & \\textbf{" + b + "}" for a, b in d) + " & " * (2 * (cot - len(d))) for d in dong) + r"\\\hline\end{tabular}\par")
    noi_hs = (r"\phanPhieu{NHIỆM VỤ}" + "\n{\\small Có " + str(len(chu)) + r" câu. Mỗi đáp án đúng ứng với một chữ cái (chữ trong ô vuông trước phương án, hoặc tra bảng giải mã). "
              r"Các chữ ghép lại thành một thông điệp bí mật.}\par" + "\n" + giai_ma + r"\phanPhieu[\faPencil]{CÁC CÂU HỎI}" + "\n" + "\n".join(hs) + bang)
    noi_gv = (r"\phanPhieu[\faKey]{THÔNG ĐIỆP: " + thoat(td) + "}\n" + r"\begin{multicols}{3}\small" + "\n" +
              "\n".join(r"\noindent Câu " + str(i) + ": \\textbf{" + thoat(x) + r"}\par" for i, x, _ in dap) + r"\end{multicols}" +
              r"\phanPhieu[\faCheckSquareO]{LỜI GIẢI}" + "\n" +
              "\n".join(r"\par\noindent\textbf{Câu " + str(i) + ".} " + (_tach(c)["lg"] or "") + r"\par" for i, _, c in dap))
    ten = (cfg.get("ten") or "").strip() or "Giải mã thông điệp"
    out = _tai_lieu(cfg, "PHIẾU MẬT MÃ", ten, noi_hs, noi_gv, _phu(dang, f"{len(chu)} câu"), dang)
    in_ra(f"🔐 Phiếu Mật mã: «{td}» — {len(chu)} câu ({sum(c['loai'] == 'TN' for c in cau)} TN, {sum(c['loai'] == 'TLN' for c in cau)} trả lời ngắn)")
    return out


# ------------------------------------------------------------------ 🔍 TÌM LỖI SAI
def _tep_loi(dang):
    return os.path.join(KHO_LOI, dang.replace("?", "_") + ".json")


def doc_loi(dang):
    try:
        return json.load(open(_tep_loi(dang), encoding="utf-8"))
    except (OSError, ValueError):
        return []


def dem_loi(dang_keys):
    return {d: len(doc_loi(d)) for d in dang_keys}


def mau_cho_loi(dang, so=4, tranh=()):
    """Câu trong ngân hàng có lời giải tính toán rõ ràng → làm gốc cho AI dựng lời giải có lỗi."""
    ra = []
    for c in _ung_vien(dang, ["TLN", "TL", "TN"], None, tranh):
        p = _tach(c)
        if not p or len(re.sub(r"\s", "", p["lg"] or "")) < 60 or "tikzpicture" in (p["de"] + p["lg"]):
            continue
        ra.append({"ma": c["ma"], "dang": c["dang_key"], "loai": c["loai"], "muc": c.get("muc_chuan") or "H", "de": p["de"],
                   "pa": p.get("pa"), "dap_an": _dap(c), "lg": p["lg"]})
        if len(ra) >= so:
            break
    return ra


def prompt_loi(dang, so=4):
    """Prompt cho AI: từ câu + lời giải ĐÚNG trong ngân hàng, viết lời giải của học sinh có MỘT lỗi thường gặp."""
    da_co = {x.get("nguon_ma") for d in dang for x in doc_loi(d)}
    goc = []
    for d in dang:
        goc += mau_cho_loi([d], max(1, so // max(1, len(dang)) + 1), tranh=da_co)
    goc = goc[:max(so, len(dang))]
    if not goc:
        raise ValueError("Các dạng đã chọn chưa có câu nào kèm lời giải tính toán đủ dài để làm gốc.")
    id_map = tai_id_map()
    p = ["Bạn là giáo viên Toán THPT/THCS giàu kinh nghiệm chấm bài, hiểu rõ những lỗi sai học sinh Việt Nam hay mắc.",
         "Với MỖI câu dưới đây (có lời giải đúng), hãy viết LỜI GIẢI CỦA MỘT HỌC SINH có đúng MỘT lỗi sai điển hình, để làm phiếu \"Tìm lỗi sai\".",
         "", "YÊU CẦU:",
         "1. Lời giải chia 3–6 bước ngắn (mỗi bước 1–2 dòng, công thức trong $...$). Các bước TRƯỚC lỗi phải đúng.",
         "2. Lỗi chỉ ở MỘT bước, là lỗi thật hay gặp: nhầm dấu khi chuyển vế/phá ngoặc, quên điều kiện xác định, nhầm công thức "
         "(vd $-\\dfrac{b}{2a}$, $\\sin$/$\\cos$), chia cho biểu thức có thể bằng 0, nhầm quy tắc đếm, làm tròn sớm, đọc sai đề…",
         "3. Các bước SAU lỗi tính toán nhất quán theo cái sai (nên kết quả cuối sai), không tự sửa lại.",
         "4. Lỗi khó vừa phải: học sinh khá đọc kĩ mới phát hiện. Không viết chữ \"sai\" hay gợi ý trong lời giải của học sinh.",
         "5. Trả về DUY NHẤT một khối ```json là MẢNG, mỗi phần tử:",
         '   {"nguon_ma": "<mã câu>", "dang": "<mã dạng>", "de": "<đề, giữ nguyên LaTeX>", "buoc": ["bước 1", "bước 2", …], '
         '"buoc_sai": <số thứ tự bước sai, bắt đầu từ 1>, "loi": "<giải thích ngắn vì sao sai>", '
         '"sua": "<lời giải đúng từ bước sai trở đi>", "dap_so_dung": "<đáp số đúng>"}',
         "6. Trong JSON mỗi dấu \\ của LaTeX viết thành \\\\ (vd \"$\\\\dfrac{1}{2}$\"). Không thêm chữ nào ngoài khối json.", "", "CÁC CÂU:"]
    for i, g in enumerate(goc, 1):
        ten_d = (id_map.get(g["dang"], {}).get("type_name") or "").strip()
        p.append(f"\n### Câu {i} — mã {g['ma']} — dạng {g['dang']} ({ten_d}) — mức {g['muc']}")
        p.append("Đề: " + g["de"])
        if g["pa"]:
            p.append("Phương án: " + " | ".join(f"{'ABCD'[j]}. {x}" for j, x in enumerate(g["pa"])) + f"  (đúng: {g['dap_an']})")
        elif g["dap_an"]:
            p.append("Đáp số: " + g["dap_an"])
        p.append("Lời giải đúng: " + g["lg"])
    return "\n".join(p), len(goc)


def nhap_loi(van_ban, id_ra=None):
    """Kết quả AI (JSON mảng) → kho lỗi sai theo dạng. → (số bài nhập, danh sách lỗi bỏ qua).
    id_ra (list, tuỳ chọn): nhận id các bài vừa nhập (kể cả bài trùng đã có) để phiếu dùng đúng các bài đó."""
    from doc_nhap import sua_gach
    t = re.sub(r"```(?:json)?", "", van_ban or "")
    i, j = t.find("["), t.rfind("]")
    if i < 0 or j <= i:
        raise ValueError("Không thấy mảng JSON [ … ] trong kết quả AI.")
    tho = t[i:j + 1]
    try:
        ds = json.loads(tho)
    except ValueError:
        ds = json.loads(re.sub(r",\s*([\]}])", r"\1", sua_gach(tho)))
    K, bo, so = _kho(), [], 0
    moi = collections.defaultdict(list)
    for k, x in enumerate(ds, 1):
        if not isinstance(x, dict):
            continue
        buoc = [str(b).strip() for b in (x.get("buoc") or []) if str(b).strip()]
        try:
            bs = int(x.get("buoc_sai"))
        except (TypeError, ValueError):
            bs = 0
        dang = (x.get("dang") or (K.get(x.get("nguon_ma") or "", {}) or {}).get("dang_key") or "").strip()
        if not dang or not x.get("de") or len(buoc) < 2 or not 1 <= bs <= len(buoc) or not x.get("loi"):
            bo.append(f"mục {k}: thiếu dạng / đề / bước / bước sai / giải thích"); continue
        moi[dang].append({"id": f"{int(time.time())}{k:02d}", "nguon_ma": x.get("nguon_ma") or "", "dang": dang, "de": str(x["de"]).strip(),
                          "buoc": buoc, "buoc_sai": bs, "loi": str(x["loi"]).strip(), "sua": str(x.get("sua") or "").strip(),
                          "dap_so_dung": str(x.get("dap_so_dung") or "").strip(), "luc": time.strftime("%Y-%m-%d")})
    os.makedirs(KHO_LOI, exist_ok=True)
    for dang, v in moi.items():
        cu = doc_loi(dang)
        da = {(y.get("nguon_ma"), y.get("buoc_sai"), y.get("de")) for y in cu}
        if id_ra is not None:
            id_cu = {(y.get("nguon_ma"), y.get("buoc_sai"), y.get("de")): y.get("id") for y in cu}
            id_ra.extend(id_cu.get((y["nguon_ma"], y["buoc_sai"], y["de"])) or y["id"] for y in v)
        v = [y for y in v if (y["nguon_ma"], y["buoc_sai"], y["de"]) not in da]
        json.dump(cu + v, open(_tep_loi(dang), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        so += len(v)
    return so, bo


def tim_loi_sai(cfg, in_ra=print):
    dang = list(cfg.get("dang") or [])
    so = max(1, min(12, int(cfg.get("so") or 4)))
    rng = random.Random(cfg.get("seed") or time.time())
    theo = collections.OrderedDict()
    chi_id = set(cfg.get("chi_id") or [])
    for d in dang:
        v = doc_loi(d); rng.shuffle(v)
        theo[d] = [x for x in v if x.get("id") in chi_id] if chi_id else v
    if chi_id:                                                # chỉ bài AI vừa viết: dùng hết
        so = sum(len(v) for v in theo.values())
    chon = _xoay_vong(theo, so)
    if not chon:
        raise ValueError("Kho lỗi sai chưa có bài nào cho các dạng đã chọn — bấm 🤖 AI tạo ngay hoặc 📝 Prompt AI rồi nhập kết quả.")
    ten_ban = (cfg.get("ten_ban") or "An").strip()
    hs, gv = [], []
    for i, x in enumerate(chon, 1):
        buoc = r"\begin{enumerate}[label=\textbf{(\arabic*)},leftmargin=8mm,itemsep=1pt,topsep=2pt]" + "".join(
            r"\item " + b for b in x["buoc"]) + r"\end{enumerate}"
        hs.append(r"\par\medskip\noindent\textbf{\color{mauPhieu}Bài " + str(i) + r".}\ " + x["de"] + "\n" +
                  r"\begin{khungKT}{\small\bfseries\color{mauDang}Lời giải của bạn " + thoat(ten_ban) + r":}\par" + buoc + r"\end{khungKT}" +
                  r"\par\noindent{\small \faSearch\ Bạn " + thoat(ten_ban) + r" sai ở bước số:} \fbox{\rule{0pt}{2.2ex}\hspace{5mm}}"
                  r"\qquad{\small Vì sao sai?}\dongKe{1}\noindent{\small \faPencil\ Sửa lại cho đúng:}\dongKe{3}")
        gv.append(r"\par\medskip\noindent\textbf{Bài " + str(i) + r".} Sai ở \textbf{bước " + str(x["buoc_sai"]) + r"}: " + x["loi"] +
                  (r"\par\noindent\textit{Lời giải đúng:} " + x["sua"] if x.get("sua") else "") +
                  (r"\par\noindent\textbf{Đáp số đúng:} " + x["dap_so_dung"] if x.get("dap_so_dung") else "") + r"\par")
    noi_hs = (r"\phanPhieu{NHIỆM VỤ}" + "\n" + r"{\small Mỗi bài có lời giải của bạn " + thoat(ten_ban) +
              r" — trong đó có \textbf{đúng một bước sai}. Em hãy: \textbf{(1)} khoanh bước sai, \textbf{(2)} giải thích vì sao sai, "
              r"\textbf{(3)} sửa lại từ bước đó cho đúng.}\par" + "\n" + r"\phanPhieu[\faSearch]{TÌM LỖI SAI}" + "\n" + "\n".join(hs))
    noi_gv = r"\phanPhieu[\faKey]{ĐÁP ÁN}" + "\n" + "\n".join(gv)
    ten = (cfg.get("ten") or "").strip() or "Ai sai, sai ở đâu?"
    used = [x["dang"] for x in chon]
    out = _tai_lieu(cfg, "PHIẾU TÌM LỖI SAI", ten, noi_hs, noi_gv, _phu(used, f"{len(chon)} bài"), used)
    in_ra(f"🔍 Phiếu Tìm lỗi sai: {len(chon)} bài từ kho lỗi sai ({len(set(used))} dạng)")
    return out


# ------------------------------------------------------------------ 🔄 ÔN TẬP NGẮT QUÃNG
KHOANG = [("1 tuần trước", 4, 10), ("2 tuần trước", 11, 21), ("1 tháng trước", 22, 50)]


def lich_su_dang(lop=None):
    """{dạng: ngày gần nhất ra đề} từ lịch sử dùng câu."""
    K, ls, ra = _kho(), _lich_su(), {}
    for ma, ds in ls.items():
        c = K.get(ma)
        if not c or not c.get("dang_key"):
            continue
        if lop and str(c.get("lop") or "") != str(lop):
            continue
        for x in ds:
            m = re.match(r"(\d{4}-\d{2}-\d{2})", str(x))
            if m:
                d = datetime.date.fromisoformat(m.group(1))
                if c["dang_key"] not in ra or d > ra[c["dang_key"]]:
                    ra[c["dang_key"]] = d
    return ra


def goi_y_on(dang_nay, lop=None):
    """Dạng nên ôn lại theo khoảng 1 tuần / 2 tuần / 1 tháng (trừ dạng hôm nay)."""
    hom_nay = datetime.date.today()
    ls = lich_su_dang(lop)
    ra = {t: [] for t, _, _ in KHOANG}
    for d, ngay in sorted(ls.items(), key=lambda kv: kv[1], reverse=True):
        if d in dang_nay:
            continue
        n = (hom_nay - ngay).days
        for t, a, b in KHOANG:
            if a <= n <= b:
                ra[t].append(d)
    return ra


def on_tap(cfg, in_ra=print):
    dang_nay = list(cfg.get("dang") or [])
    if not dang_nay:
        raise ValueError("Chưa chọn dạng của bài hôm nay.")
    so_nay = max(1, min(20, int(cfg.get("so_nay") or 7)))
    so_cu = max(0, min(15, int(cfg.get("so_cu") or 3)))
    random.seed(cfg.get("seed") or time.time())
    loai = ["TN", "TLN"] + (["TL"] if cfg.get("co_tl") else [])
    nhom = []
    if _dat_chi(cfg):                                         # chỉ câu AI vừa nhập: dùng hết, đúng số câu AI sinh
        K = _kho()
        loai = ["TN", "TLN", "TL"]
        dang_ai = sorted({K[m]["dang_key"] for m in _CHI if m in K})
        cu = [d for d in dang_ai if d not in dang_nay]
        so_nay = len(_ung_vien(dang_nay, loai))
        so_cu = len(_ung_vien(cu, loai)) if cu else 0
        if cu:
            nhom.append(("Nhớ lại bài đã học", cu))
    elif cfg.get("dang_cu"):                                     # thầy tự chọn dạng ôn lại
        cu = [d for d in cfg["dang_cu"] if d not in dang_nay]
        nhom.append(("Nhớ lại bài đã học", cu))
    else:
        g = goi_y_on(dang_nay, cfg.get("lop"))
        nhom = [(f"Nhớ lại – {t}", v) for t, v in g.items() if v]
    if so_cu and not any(v for _, v in nhom) and _CHI is None:
        in_ra("  ⚠ Chưa có lịch sử ra đề 1 tuần – 1 tháng trước (hoặc chưa chọn dạng ôn lại) — phiếu chỉ có phần hôm nay.")
    da = set()
    cau_nay = _xoay_vong(collections.OrderedDict((d, _ung_vien([d], loai)) for d in dang_nay), so_nay)
    da |= {c["ma"] for c in cau_nay}
    phan = [("Bài hôm nay", r"\faPencil", cau_nay)]
    con = so_cu
    nhom_co = [(t, v) for t, v in nhom if v]
    for k, (t, v) in enumerate(nhom_co):
        can = con // (len(nhom_co) - k) if k < len(nhom_co) - 1 else con
        c = _xoay_vong(collections.OrderedDict((d, _ung_vien([d], loai, {"N", "H"}, da)) for d in v), can)
        da |= {x["ma"] for x in c}; con -= len(c)
        if c:
            phan.append((t, r"\faHistory", c))
    hs, gv, so = [], [], 0
    for t, bt, ds in phan:
        hs.append(r"\phanPhieu[" + bt + "]{" + thoat(t.upper()) + "}")
        for c in sorted(ds, key=lambda c: (["TN", "TLN", "TL"].index(c["loai"]), THU_MUC.get(c.get("muc_chuan") or "H", 1))):
            so += 1
            hs.append(_cau_tn(c, None, so, hep=bool(cfg.get("hai_cot", True)) and cfg.get("kho") != "binh_thuong") if c["loai"] == "TN" else _cau_tln(c, so) if c["loai"] == "TLN" else _cau_tl(c, so))
            p = _tach(c)
            gv.append(r"\par\noindent\textbf{Câu " + str(so) + ".} " + (r"Đáp án \textbf{" + thoat(_dap(c)) + "}. " if _dap(c) else "") + (p["lg"] or "") + r"\par")
        if t != "Bài hôm nay":
            hs.append(r"\par\noindent{\small Em còn nhớ phần này không?\quad \faSmileO\ Nhớ rõ \quad \faMehO\ Nhớ mang máng \quad \faFrownO\ Quên rồi}\par")
    tong_cu = sum(len(ds) for t, _, ds in phan[1:])
    noi_hs = (r"{\small Phiếu trộn câu của \textbf{bài hôm nay} với câu của \textbf{bài đã học} — ôn lại đúng lúc sắp quên giúp nhớ lâu hơn. "
              r"Làm hết rồi tự đánh dấu mức độ nhớ ở cuối mỗi phần.}\par" + "\n" + "\n".join(hs))
    noi_gv = r"\phanPhieu[\faKey]{ĐÁP ÁN – LỜI GIẢI}" + "\n" + "\n".join(gv)
    ten = (cfg.get("ten") or "").strip() or (tai_id_map().get(dang_nay[0], {}).get("lesson_name") or "Ôn tập").strip()
    used = dang_nay + [c["dang_key"] for _, _, ds in phan[1:] for c in ds]
    out = _tai_lieu(cfg, "PHIẾU ÔN TẬP NGẮT QUÃNG", ten, noi_hs, noi_gv, _phu(dang_nay, f"{len(cau_nay)} câu mới + {tong_cu} câu ôn lại"), used,
                    hai_cot=bool(cfg.get("hai_cot", True)))
    in_ra(f"🔄 Phiếu Ôn tập ngắt quãng: {len(cau_nay)} câu bài hôm nay + {tong_cu} câu ôn lại ("
          + ", ".join(f"{t}: {len(ds)}" for t, _, ds in phan[1:]) + ")")
    return out


# ------------------------------------------------------------------ ⭐ THỬ THÁCH 3 MỨC (LEO NÚI)
BAC = [("⭐", "Chân núi – Cơ bản", {"N", "H"}, 1), ("⭐⭐", "Sườn núi – Vận dụng", {"V"}, 2), ("⭐⭐⭐", "Đỉnh núi – Thử thách", {"C"}, 3)]


def _sao(n):
    return r"{\color{mauDang}" + r"\,".join([r"\faStar"] * n) + "}"


def thu_thach(cfg, in_ra=print):
    dang = list(cfg.get("dang") or [])
    if not dang:
        raise ValueError("Chưa chọn dạng.")
    so = [max(0, min(6, int(x))) for x in (cfg.get("so_bac") or [2, 2, 1])][:3]
    random.seed(cfg.get("seed") or time.time())
    chi = _dat_chi(cfg)
    loai = ["TN", "TLN", "TL"] if cfg.get("co_tl", True) or chi else ["TN", "TLN"]
    id_map = tai_id_map()
    hs, gv, bang, dem, da, tong_sao, thieu = [], [], [], 0, set(), 0, []
    for j, d in enumerate(dang, 1):
        ten_d = (id_map.get(d, {}).get("type_name") or d).strip()
        hs.append(r"\phanPhieu[\faFlag]{CHẶNG " + str(j) + ". " + thoat(ten_d.upper()) + "}")
        hang, vt = [], len(hs)
        for b, (ky, ten_b, muc, diem) in enumerate(BAC):
            if not so[b] and not chi:
                hang.append("—"); continue
            ds = _ung_vien([d], loai, muc, da, giu_muc=True)
            if chi:                                       # chỉ câu AI vừa nhập: lấy hết câu đúng mức của bậc
                if not ds:
                    hang.append("—"); continue
            else:
                ds = ds[:so[b]]
            if not chi and len(ds) < so[b] and b == 2:    # thiếu VDC → lấy thêm câu vận dụng khó nhất
                ds += _ung_vien([d], loai, {"V"}, da | {c["ma"] for c in ds})[:so[b] - len(ds)]
            if not chi and len(ds) < so[b]:
                thieu.append(f"{d} bậc {ky}: có {len(ds)}/{so[b]} câu")
            if not ds:
                hang.append("—"); continue
            da |= {c["ma"] for c in ds}
            hs.append(r"\par\smallskip\noindent\tikz[reset cm,baseline=(b.base)]\node[fill=mauDang!" + str(12 + 10 * b) +
                      r",rounded corners=1.5mm,inner xsep=2mm,inner ysep=1.5pt,font=\small\bfseries](b){" + _sao(diem) + r"\ \ " + ten_b +
                      r"};\hfill{\small " + str(diem) + r" sao / câu}\par")
            for c in ds:
                dem += 1; tong_sao += diem
                hs.append((_cau_tn(c, None, dem) if c["loai"] == "TN" else _cau_tln(c, dem) if c["loai"] == "TLN" else _cau_tl(c, dem, 4))
                          + r"\vspace{-2pt}\noindent\hfill{\scriptsize Đạt:\ \fbox{\rule{0pt}{1.6ex}\hspace{3mm}}}\par")
                p = _tach(c)
                gv.append(r"\par\noindent\textbf{Câu " + str(dem) + r"} (" + _sao(diem) + r"). " + (r"Đáp án \textbf{" + thoat(_dap(c)) + "}. " if _dap(c) else "") + (p["lg"] or "") + r"\par")
            hang.append(f"{len(ds)} câu × {diem}")
        if chi and len(hs) == vt + 1:                     # dạng này AI không sinh câu nào → bỏ chặng
            hs.pop(); continue
        bang.append((j, ten_d, hang))
    if not dem:
        raise ValueError("Các dạng đã chọn chưa có câu phù hợp.")
    # bảng tích sao: mỗi chặng × 3 bậc
    tich = (r"\phanPhieu[\faTrophy]{BẢNG TÍCH SAO}" + "\n" + r"{\small Mỗi câu làm đúng: tô sao tương ứng. Chinh phục đủ một bậc mới lên bậc tiếp theo! Tổng tối đa: \textbf{"
            + str(tong_sao) + r" sao}.}\par\smallskip\noindent\begin{tabular}{|p{0.40\linewidth}|p{0.13\linewidth}|p{0.13\linewidth}|p{0.13\linewidth}|}\hline \textbf{Chặng} & " +
            " & ".join(r"\hfill" + _sao(diem) + r"\hfill\null" for _, _, _, diem in BAC) + r"\\\hline " +
            r"\\\hline ".join(f"{j}. " + thoat(t if len(t) <= 46 else t[:44].rsplit(" ", 1)[0] + "…") + " & " + " & ".join(r"\rule{0pt}{4mm}" for _ in BAC) for j, t, _ in bang) +
            r"\\\hline\multicolumn{4}{|r|}{\rule{0pt}{4.5mm}Tổng số sao: \makebox[1.6cm]{\dotfill}\ /\ " + str(tong_sao) +
            r"\qquad Danh hiệu: \faFlag\ Nhà leo núi ($\ge 50\%$)\quad \faTrophy\ Chinh phục đỉnh ($\ge 80\%$)}\\\hline\end{tabular}\par")
    if cfg.get("bang_nhom"):
        so_nhom = max(2, min(10, int(cfg.get("so_nhom") or 6)))
        tich += (r"\par\medskip\noindent{\bfseries\color{mauDang}Bảng xếp hạng nhóm} {\small(tổng sao các thành viên)}\par\smallskip\noindent"
                 r"\begin{tabular}{|l|" + r"p{8mm}|" * so_nhom + r"}\hline Nhóm & " + " & ".join(str(i) for i in range(1, so_nhom + 1)) +
                 r"\\\hline Sao & " + " & ".join(r"\rule{0pt}{5mm}" for _ in range(so_nhom)) + r"\\\hline\end{tabular}\par")
    noi_hs = (r"{\small Mỗi chặng là một dạng toán với 3 bậc: " + _sao(1) + r" cơ bản, " + _sao(2) + r" vận dụng, " + _sao(3) +
              r" thử thách. Em tự chọn bậc phù hợp, làm đúng được tích sao — cố gắng leo tới đỉnh!}\par" + "\n" + "\n".join(hs) + "\n" + tich)
    noi_gv = r"\phanPhieu[\faKey]{ĐÁP ÁN – LỜI GIẢI}" + "\n" + "\n".join(gv)
    ten = (cfg.get("ten") or "").strip() or (id_map.get(dang[0], {}).get("lesson_name") or "Leo núi").strip()
    out = _tai_lieu(cfg, "THỬ THÁCH LEO NÚI", ten, noi_hs, noi_gv, _phu(dang, f"{len(dang)} chặng · {dem} câu · tối đa {tong_sao} sao"), dang)
    in_ra(f"⭐ Phiếu Thử thách 3 mức: {len(dang)} chặng, {dem} câu, tối đa {tong_sao} sao")
    for x in thieu:
        in_ra("  ⚠ " + x)
    return out


# ------------------------------------------------------------------ 🧩 MẢNH GHÉP (JIGSAW)
MAU_NHOM = ["mauPhieu", "mauDang", "orange!80!black", "teal!70!black", "violet!75!black", "red!70!black"]


def manh_ghep(cfg, in_ra=print):
    """Mỗi dạng = một nhóm chuyên gia (A, B, C…). Tờ chuyên gia: phương pháp + ví dụ mẫu có lời giải + bài luyện + ghi chú để dạy lại.
    Tờ mảnh ghép: mỗi dạng một ô tóm tắt (nghe bạn chuyên gia dạy) + bài tập. Đáp án kèm sơ đồ chia nhóm cho cả lớp."""
    import beamer_phieu
    dang = list(cfg.get("dang") or [])
    if not 2 <= len(dang) <= 6:
        raise ValueError("Mảnh ghép cần chọn 2–6 dạng (mỗi dạng là một nhóm chuyên gia).")
    random.seed(cfg.get("seed") or time.time())
    so_hs = max(len(dang), min(60, int(cfg.get("so_hs") or 40)))
    so_luyen = max(1, min(4, int(cfg.get("so_luyen") or 2)))
    chi = _dat_chi(cfg)
    id_map = tai_id_map()
    nhom = "ABCDEF"
    so_manh = -(-so_hs // len(dang))
    to, gv, mg, da = [], [], [], set()
    ten = (cfg.get("ten") or "").strip() or (id_map.get(dang[0], {}).get("lesson_name") or "Học nhóm mảnh ghép").strip()
    phu = _phu(dang, f"{len(dang)} nhóm chuyên gia · {so_manh} nhóm mảnh ghép")
    for j, d in enumerate(dang):
        ten_d = (id_map.get(d, {}).get("type_name") or d).strip()
        mau = MAU_NHOM[j % len(MAU_NHOM)]
        the = (r"\tikz[reset cm,baseline=(n.base)]\node[circle,fill=" + mau + r",text=white,minimum size=7mm,inner sep=0pt,font=\bfseries](n){" + nhom[j] + "};")
        ds = _ung_vien([d], ["TL", "TLN", "TN"], None, da)
        vd = next((c for c in ds if len(re.sub(r"\s", "", (_tach(c) or {}).get("lg") or "")) > 40), None)
        if vd:
            da.add(vd["ma"])
        if chi and not ds:
            in_ra(f"  ⚠ Nhóm {nhom[j]} ({ten_d}): không có câu AI vừa nhập — tờ chuyên gia chỉ có phương pháp; nên sinh thêm câu cho dạng này.")
        con = [c for c in ds if c["ma"] not in da]
        # chỉ câu AI vừa nhập: dùng hết — chừa 1 câu cho tờ mảnh ghép, còn lại là bài luyện của chuyên gia
        luyen = (con[:-1] if len(con) >= 2 else con) if chi else con[:so_luyen]
        da |= {c["ma"] for c in luyen}
        bt_mg = [c for c in _ung_vien([d], ["TN", "TLN", "TL"], {"N", "H", "V"}, da)][:1]
        da |= {c["ma"] for c in bt_mg}
        pp = beamer_phieu.doc_pp(d).strip()
        from phieu_bai_hoc import chuan_kien_thuc
        t = [r"<<DAU|PHIẾU CHUYÊN GIA – NHÓM " + nhom[j] + "|" + ten_d + "|" + thoat(f"In {so_manh} bản · mỗi bạn nhóm {nhom[j]} một bản") + ">>",
             r"\par\noindent" + the + r"\ {\large\bfseries\color{" + mau + r"}Nhiệm vụ của chuyên gia " + nhom[j] + r"}\par"
             r"{\small Cả nhóm cùng đọc phương pháp, hiểu kĩ ví dụ mẫu, làm bài luyện và thống nhất cách giảng. Sau đó mỗi bạn về nhóm mảnh ghép "
             r"\textbf{dạy lại} dạng này cho các bạn trong khoảng 5 phút.}\par",
             r"\phanPhieu[\faLightbulbO]{1. PHƯƠNG PHÁP}",
             (r"\begin{khungKT}" + chuan_kien_thuc(pp) + r"\end{khungKT}") if pp else r"{\small\itshape Cả nhóm cùng rút ra các bước giải:}\dongKe{3}"]
        if vd:
            p = _tach(vd)
            t += [r"\phanPhieu[\faBook]{2. VÍ DỤ MẪU}", r"\par\noindent\textbf{Ví dụ.} " + p["de"] +
                  (r"\par\noindent " + r"\quad ".join(f"\\textbf{{{'ABCD'[i]}.}} {x}" for i, x in enumerate(p["pa"])) if vd["loai"] == "TN" and p.get("pa") else "") +
                  r"\par\noindent{\bfseries\color{" + mau + r"}Lời giải.} " + p["lg"] + r"\par"]
        t.append(r"\phanPhieu[\faPencil]{3. CHUYÊN GIA LUYỆN TẬP}")
        for k, c in enumerate(luyen, 1):
            t.append(_cau_tn(c, None, k) if c["loai"] == "TN" else _cau_tln(c, k) if c["loai"] == "TLN" else _cau_tl(c, k, 3))
            gv.append(r"\par\noindent\textbf{Nhóm " + nhom[j] + " – luyện " + str(k) + ".} " + (r"Đáp án \textbf{" + thoat(_dap(c)) + "}. " if _dap(c) else "") + (_tach(c)["lg"] or "") + r"\par")
        t += [r"\phanPhieu[\faCommentO]{4. GHI CHÚ ĐỂ DẠY LẠI BẠN}", r"{\small Các bước chính / lỗi hay gặp / mẹo nhớ:}\dongKe{3}", r"\newpage"]
        to.append("\n".join(t))
        # ô trên tờ mảnh ghép
        o = [r"\par\medskip\noindent" + the + r"\ {\bfseries\color{" + mau + r"}Dạng " + nhom[j] + ". " + thoat(ten_d) + r"}{\small\ — bạn chuyên gia " + nhom[j] + r" giảng}\par",
             r"{\small Tóm tắt cách làm:}\dongKe{2}"]
        for c in bt_mg:
            x = _cau_tn(c, None, "#") if c["loai"] == "TN" else _cau_tln(c, "#") if c["loai"] == "TLN" else _cau_tl(c, "#", 3)
            o.append(x.replace(r"\color{mauPhieu}Câu #.}", r"\color{" + mau + "}Bài " + nhom[j] + ".}"))
            gv.append(r"\par\noindent\textbf{Mảnh ghép – bài " + nhom[j] + ".} " + (r"Đáp án \textbf{" + thoat(_dap(c)) + "}. " if _dap(c) else "") + (_tach(c)["lg"] or "") + r"\par")
        mg.append("\n".join(o))
    to.append(r"<<DAU|PHIẾU MẢNH GHÉP|" + thoat(ten) + "|" + thoat(f"In {so_hs} bản · mỗi học sinh một bản") + ">>" + "\n" +
              r"{\small Mỗi nhóm mảnh ghép có đủ chuyên gia " + ", ".join(nhom[:len(dang)]) + r". Lần lượt từng bạn giảng dạng của mình (≈5 phút), "
              r"cả nhóm ghi tóm tắt rồi cùng giải bài tương ứng. Cuối giờ tự đánh giá.}\par" + "\n".join(mg) +
              r"\phanPhieu[\faCheckSquareO]{TỰ ĐÁNH GIÁ}" + r"{\small Dạng em hiểu rõ nhất: \makebox[4cm]{\dotfill}\quad Dạng cần hỏi thêm: \makebox[4cm]{\dotfill}"
              r"\par\smallskip Bạn chuyên gia giảng dễ hiểu nhất: \makebox[5cm]{\dotfill}}\par")
    # sơ đồ chia nhóm cho giáo viên
    chia = [[] for _ in range(so_manh)]
    for i in range(so_hs):
        chia[i // len(dang)].append((i + 1, nhom[i % len(dang)]))
    so_do = (r"\phanPhieu[\faUsers]{SƠ ĐỒ CHIA NHÓM (" + str(so_hs) + r" học sinh)}" + "\n" +
             r"{\small Học sinh số $n$ (theo danh sách) vào \textbf{nhóm chuyên gia} theo chữ cái và \textbf{nhóm mảnh ghép} theo số dòng. "
             r"Mỗi nhóm chuyên gia có khoảng " + str(so_manh) + r" bạn; mỗi nhóm mảnh ghép có " + str(len(dang)) + r" bạn (một bạn mỗi dạng).}\par\smallskip"
             r"\noindent\begin{tabular}{|c|" + "c|" * len(dang) + r"}\hline\textbf{Mảnh ghép} & " +
             " & ".join(r"\textbf{" + nhom[k] + "}" for k in range(len(dang))) + r"\\\hline " +
             r"\\\hline ".join(f"{m + 1} & " + " & ".join("HS " + str(n) for n, _ in r) + " & " * (len(dang) - len(r)) for m, r in enumerate(chia)) +
             r"\\\hline\end{tabular}\par")
    noi_gv = so_do + r"\phanPhieu[\faKey]{ĐÁP ÁN – LỜI GIẢI}" + "\n" + "\n".join(gv)
    out = _tai_lieu(cfg, "HỌC NHÓM MẢNH GHÉP", ten, "\n".join(to), noi_gv, phu, dang)
    in_ra(f"🧩 Phiếu Mảnh ghép: {len(dang)} tờ chuyên gia (A–{nhom[len(dang) - 1]}) + tờ mảnh ghép; {so_hs} HS → {so_manh} nhóm mảnh ghép")
    return out


# ------------------------------------------------------------------ prompt AI sinh câu nhập ngân hàng (Mật mã, Ôn tập, Leo núi, Mảnh ghép)
def prompt_cau(dang, so_moi=4, kieu="mat_ma", lop=None):
    id_map = tai_id_map()
    dem = {d: collections.Counter(c["loai"] for c in _kho().values() if c.get("dang_key") == d) for d in dang}
    tn_tln = kieu == "mat_ma"
    muc_dich = {"mat_ma": "để làm PHIẾU MẬT MÃ: câu ngắn, làm trong 1–2 phút, mỗi câu một đáp án rõ ràng.",
                "on_tap": "để làm PHIẾU ÔN TẬP NGẮT QUÃNG: câu gọn, kiểm tra đúng kiến thức cốt lõi của dạng, mức nhận biết – thông hiểu là chính.",
                "thu_thach": "để làm PHIẾU THỬ THÁCH 3 MỨC (leo núi): mỗi dạng đủ 3 bậc — ⭐ cơ bản (NB/TH), ⭐⭐ vận dụng (VD), "
                             "⭐⭐⭐ thử thách (VDC: nhiều bước, tình huống thực tế hoặc biện luận) — bậc sau khó hơn rõ rệt nhưng vẫn cùng dạng.",
                "manh_ghep": "để làm PHIẾU MẢNH GHÉP (học nhóm): mỗi dạng cần 1 ví dụ mẫu tự luận có LỜI GIẢI ĐẦY ĐỦ TỪNG BƯỚC (để học sinh "
                             "chuyên gia đọc hiểu rồi dạy lại bạn) và vài bài luyện cùng dạng, mức thông hiểu – vận dụng."}.get(kieu, "")
    p = ["Bạn là giáo viên Toán giỏi (chương trình GDPT 2018, sách Kết nối tri thức). Soạn câu hỏi MỚI cho các dạng toán dưới đây " + muc_dich,
         "", "YÊU CẦU:",
         "1. Trả về DUY NHẤT một khối ```json có dạng {\"trac_nghiem\": [...], \"tra_loi_ngan\": [...]} (nhóm không có câu thì để []).",
         "2. trac_nghiem: {\"cau\", \"phuong_an\": [4 chuỗi, không ghi A./B.], \"dap_an\": \"A\"|\"B\"|\"C\"|\"D\", \"giai_thich\", \"muc\": \"NB\"|\"TH\"|\"VD\", "
         "\"ma_dang\", \"figures\": []}. Đáp án đúng rải đều A–D. Phương án nhiễu sinh từ lỗi sai thường gặp, 4 phương án khác nhau.",
         "3. tra_loi_ngan: {\"cau\", \"dap_an\": chuỗi số tối đa 4 ký tự (vd \"2,5\", \"-3\"), \"giai_thich\", \"muc\", \"ma_dang\", \"figures\": []}."
         + (" tu_luan: {\"cau\", \"giai_thich\": lời giải đầy đủ từng bước, \"muc\", \"ma_dang\", \"figures\": []} (thêm khoá \"tu_luan\": [...] vào JSON)."
            if kieu in ("thu_thach", "manh_ghep") else ""),
         "4. ma_dang: lấy đúng mã dạng ở danh sách, thay \"?\" bằng N (NB) / H (TH) / V (VD) / C (VDC); \"muc\" ghi NB/TH/VD/VDC tương ứng.",
         "5. LaTeX trong $...$, mỗi dấu \\ viết thành \\\\ trong JSON. Tự giải lại từng câu trước khi trả lời; đáp án phải khớp lời giải.",
         "", "DANH SÁCH DẠNG (mỗi dạng " + str(so_moi) + " câu" + {"mat_ma": ", khoảng 2/3 trắc nghiệm, 1/3 trả lời ngắn",
                                                                  "thu_thach": ", chia đều 3 bậc NB-TH / VD / VDC, trộn TN, trả lời ngắn và tự luận",
                                                                  "manh_ghep": ", trong đó ít nhất 1 câu tự luận có lời giải chi tiết làm ví dụ mẫu"}.get(kieu, ", trộn trắc nghiệm và trả lời ngắn") + "):"]
    for d in dang:
        v = id_map.get(d, {})
        p.append(f"- {d}: {(v.get('type_name') or '').strip()} — bài {(v.get('lesson_name') or '').strip()} "
                 f"(kho đang có {dem[d]['TN']} TN, {dem[d]['TLN']} TLN)")
    return "\n".join(p)
