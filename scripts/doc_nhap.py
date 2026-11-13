# -*- coding: utf-8 -*-
"""
ĐỌC FILE NHẬP CÂU HỎI: .tex, .txt, .md, .json  →  văn bản LaTeX gồm các khối \\begin{ex}…\\end{ex}.

• .tex / .txt / .md : chứa sẵn các khối \\begin{ex}…\\end{ex} (đúng cấu trúc ngân hàng); bỏ rào ```latex nếu có.
• .json : chấp nhận nhiều kiểu
    - mảng chuỗi, mỗi chuỗi là một khối \\begin{ex}…\\end{ex}
    - mảng đối tượng có trường chứa sẵn khối tex ("tex", "latex", "noi_dung"…)
    - mảng đối tượng theo trường (kể cả mẫu 13 trường của thầy):
        "Loại"/"loai"/"type"            : Trắc nghiệm | Đúng/Sai | Trả lời ngắn | Tự luận (TN/DS/TLN/TL)
        "Nội dung"/"de"/"cau_hoi"/"question"
        "Lựa chọn A / Mệnh đề a" … hoặc "A","B"… hoặc mảng "phuong_an"/"options"
        "Đáp án đúng"/"dap_an"/"answer" : B | a-Đúng, b-Sai, c-Sai, d-Đúng | ĐSSĐ | 2,67
        "Lời giải"/"loi_giai"/"solution"
        "Mức độ nhận thức"/"muc"        : Nhận biết | Thông hiểu | Vận dụng | Vận dụng cao (NB/TH/VD/VDC)
        "Mã dạng"/"ma_dang"/"id"        : 2D1N1-2 (không bắt buộc)
    - đối tượng bọc ngoài {"cau_hoi": [...]} / {"questions": [...]} … đều được.
Câu chưa có mã dạng mà người dùng đưa mã mặc định (vd 2D1?1-2) thì được gán mã đó, "?" thay bằng mức độ của câu.
"""
import os, re, json, unicodedata

MA_DANG = re.compile(r"%\[\s*(\d)([A-Z])(\d+)([A-Z?])(\d+)-(\d+)\s*\]")
KHOI = re.compile(r"\\begin\{(ex|bt)\}(.*?)\\end\{\1\}", re.S)
MA_TRAN = re.compile(r"^\s*(\d)([DHC])(\d+)([NHVC?])(\d+)-(\d+)\s*$")

def khong_dau(s):
    s = str(s).replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower().strip()

def chuan_ma_dang(s):
    """'2D1?1-2', '[2D1N1-2]', '%[2D1N1-2]' → '2D1?1-2' (hoặc None)."""
    s = re.sub(r"[%\[\]\s]", "", str(s or "")).upper()
    return s if MA_TRAN.match(s) else None

def muc_tu_chu(s):
    k = khong_dau(s).replace(" ", "")
    if not k:
        return None
    if k in ("n", "nb", "nhanbiet", "biet", "1", "muc1"):
        return "N"
    if k in ("h", "th", "thonghieu", "hieu", "2", "muc2"):
        return "H"
    if k in ("c", "vdc", "vandungcao", "4", "muc4"):
        return "C"
    if k in ("v", "vd", "vdt", "vandung", "vandungthap", "3", "muc3"):
        return "V"
    return None

def gan_ma(khoi, ma_dang, muc=None):
    """Gắn %[ma] vào dòng đầu khối nếu khối chưa có mã dạng."""
    m = re.match(r"\\begin\{(ex|bt)\}", khoi)
    dong_dau = khoi[m.end():].split("\n", 1)[0]
    if not ma_dang or MA_DANG.search(dong_dau):
        return khoi
    ma = ma_dang.replace("?", muc or "N")
    return khoi[:m.end()] + f"%[{ma}]" + khoi[m.end():]

# ---------------------------------------------------------------- JSON → tex
TRUONG = {
    "noi_dung": ["noi dung", "noidung", "noi_dung", "de", "de bai", "cau hoi", "cauhoi", "cau_hoi", "question",
                 "content", "stem", "text", "problem"],
    "loai": ["loai", "loai cau", "type", "kieu", "dang cau"],
    "dap_an": ["dap an dung", "dap an", "dap_an", "dapan", "answer", "correct", "correct answer", "key", "ket qua"],
    "loi_giai": ["loi giai", "loi_giai", "loigiai", "huong dan giai", "huong dan", "solution", "giai", "explanation"],
    "muc": ["muc do nhan thuc", "muc do", "muc_do", "muc", "level", "difficulty", "do kho"],
    "ma_dang": ["ma dang", "ma_dang", "madang", "id dang", "dang", "code", "id", "ma"],
    "phuong_an": ["phuong an", "phuong_an", "lua chon", "options", "choices", "cac phuong an", "menh de", "y"],
    "tex": ["tex", "latex", "khoi", "ex", "noi dung tex", "ma tex"],
}

def lay(d, ten):
    for k, v in d.items():
        if khong_dau(k).replace("_", " ") in [x.replace("_", " ") for x in TRUONG[ten]]:
            return v
    return None

def phuong_an(d):
    pa = lay(d, "phuong_an")
    if isinstance(pa, list):
        return [str(x) for x in pa][:4]
    if isinstance(pa, dict):
        return [str(pa.get(c) or pa.get(c.lower()) or "") for c in "ABCD"]
    ra = {}
    for k, v in d.items():
        kk = khong_dau(k)
        m = re.match(r"^(?:lua chon|phuong an|menh de|option|choice|y|cau)?\s*_?\(?([abcd])\)?\.?(?:\s|/|$)", kk)
        if m and (kk[0] in "abcd" and len(kk) <= 3 or not kk[0] in "abcd" or kk.startswith(("lua", "phuong", "menh", "option", "choice"))):
            ra.setdefault(m.group(1), str(v if v is not None else ""))
    return [ra[c] for c in "abcd"] if len(ra) == 4 else None

def loai_cau(d, pa, da):
    k = khong_dau(lay(d, "loai") or "").replace(" ", "")
    if k:
        if k in ("tn", "mcq") or "tracnghiem" in k and "dung" not in k or "nhieulua" in k or "multiple" in k:
            return "TN"
        if k in ("ds", "tf", "dungsai", "truefalse") or "dung" in k and "sai" in k or "true" in k:
            return "DS"
        if k in ("tln", "saq", "short") or "traloingan" in k or "short" in k or "dien" in k:
            return "TLN"
        if k in ("tl", "essay") or "tuluan" in k or "essay" in k:
            return "TL"
    if pa and any(x.strip() for x in pa):
        s = khong_dau(da if isinstance(da, str) else json.dumps(da, ensure_ascii=False))
        return "DS" if re.search(r"dung|sai|\b[ds]\b|true|false", s) and not re.fullmatch(r"\s*[abcd]\s*", s) else "TN"
    return "TLN" if da not in (None, "") else "TL"

def dap_an_tn(da):
    s = str(da or "").strip()
    m = re.search(r"\b([ABCD])\b", s.upper())
    if m:
        return "ABCD".index(m.group(1))
    if s.isdigit() and 0 <= int(s) - 1 < 4:
        return int(s) - 1
    return None

def dap_an_ds(da):
    """→ danh sách 4 giá trị True/False (None nếu không đọc được)."""
    if isinstance(da, list) and len(da) == 4:
        return [khong_dau(x) in ("d", "dung", "true", "t", "1", "đ") or x is True for x in da]
    if isinstance(da, dict):
        return [khong_dau(da.get(c, da.get(c.upper(), ""))) in ("d", "dung", "true", "t", "1") for c in "abcd"]
    s = str(da or "")
    ra = {}
    for c, v in re.findall(r"([abcdABCD])\s*[-:).=]?\s*(Đúng|Sai|Đ|S|True|False|T|F)\b", s):
        ra[c.lower()] = khong_dau(v) in ("dung", "d", "true", "t")
    if len(ra) == 4:
        return [ra[c] for c in "abcd"]
    chu = re.sub(r"[^ĐSTFđstf]", "", s.replace("Đúng", "Đ").replace("Sai", "S"))
    if len(chu) == 4:
        return [c in "ĐđTt" for c in chu]
    return None

DUNG = "\\True "

def don(s):
    s = "" if s is None else str(s)
    return s.replace("\r", "").strip()

def json_cau_sang_tex(d, ma_dang=None):
    tex = lay(d, "tex")
    if isinstance(tex, str) and KHOI.search(tex):
        return [gan_ma(k.group(0), chuan_ma_dang(lay(d, "ma_dang")) or ma_dang, muc_tu_chu(lay(d, "muc") or ""))
                for k in KHOI.finditer(tex)]
    nd = lay(d, "noi_dung")
    if isinstance(nd, str) and KHOI.search(nd):
        return [gan_ma(k.group(0), ma_dang, muc_tu_chu(lay(d, "muc") or "")) for k in KHOI.finditer(nd)]
    if nd is None:
        return []
    pa, da, lg = phuong_an(d), lay(d, "dap_an"), don(lay(d, "loi_giai"))
    loai = loai_cau(d, pa, da)
    muc = muc_tu_chu(lay(d, "muc") or "")
    md = chuan_ma_dang(lay(d, "ma_dang")) or ma_dang
    ma = f"%[{md.replace('?', muc or 'N')}]" if md else ""
    env = "bt" if loai in ("TL", "TLN") else "ex"           # quy ước ngân hàng: TLN/TL dùng môi trường bt
    dong = [f"\\begin{{{env}}}{ma}", "\t" + don(nd)]
    if loai == "TN":
        i = dap_an_tn(da)
        dong.append("\t\\choice")
        dong += ["\t{" + (DUNG if j == i else "") + don(x) + "}" for j, x in enumerate((pa or [""] * 4)[:4])]
    elif loai == "DS":
        dung = dap_an_ds(da) or [False] * 4
        dong.append("\t\\choiceTF")
        dong += ["\t{" + (DUNG if dung[j] else "") + don(x) + "}" for j, x in enumerate((pa or [""] * 4)[:4])]
    elif loai == "TLN":
        dong.append(f"\t\\shortans{{{don(da)}}}")
    if lg:
        dong.append(f"\t\\loigiai{{\n\t\t{lg}\n\t}}")
    dong.append(f"\\end{{{env}}}")
    return ["\n".join(dong)]

def duyet(obj, ma_dang, ra):
    if isinstance(obj, str):
        ra += [gan_ma(k.group(0), ma_dang) for k in KHOI.finditer(obj)]
    elif isinstance(obj, list):
        for x in obj:
            duyet(x, ma_dang, ra)
    elif isinstance(obj, dict):
        if isinstance(lay(obj, "noi_dung"), str) or isinstance(lay(obj, "tex"), str):
            ra += json_cau_sang_tex(obj, ma_dang)
        else:
            for v in obj.values():
                if isinstance(v, (list, dict, str)):
                    duyet(v, ma_dang, ra)

# lệnh LaTeX mà JSON hiểu nhầm thành ký tự điều khiển khi chỉ viết một dấu \ (\frac → \f + rac, \neq → \n + eq…)
LENH_DE_NHAM = re.compile(r"^(?:frac|dfrac|tfrac|forall|flat|beta|binom|bar|begin|boxed|bigg?|bot|bullet|backslash|"
                          r"neq|ne|nabla|newline|notin|not|nu|neg|nmid|nexists|right|rho|rangle|rfloor|rceil|"
                          r"times|text\w*|tan|tanh|theta|tau|to|triangle|top|tilde|textbf|tfrac)(?![a-z])")

def sua_gach(tho):
    """Sửa JSON do AI/người viết: '\frac' (một gạch) → '\\frac'; '\alpha' (escape sai) → '\\alpha'."""
    def thay(m):
        c, sau = m.group(1), m.group(2)
        if c == "\\":
            return m.group(0)
        if c in '"/':
            return m.group(0)
        if c == "u" and (not sau or re.fullmatch(r"[0-9a-fA-F]{4}", sau[:4] or "")):
            return m.group(0)
        if c in "bfnrt" and not LENH_DE_NHAM.match(c + sau):
            return m.group(0)
        return "\\\\" + c + sau
    return re.sub(r"\\(\\|.)([A-Za-z]*)", thay, tho)

def doc_tep(duong, ma_dang=None, noi_dung=None):
    """Trả văn bản LaTeX (các khối nối nhau) từ file .tex/.txt/.md/.json."""
    t = noi_dung if noi_dung is not None else open(duong, encoding="utf-8-sig", errors="replace").read()
    ma_dang = chuan_ma_dang(ma_dang)
    duoi = os.path.splitext(duong)[1].lower()
    tho = t.strip()
    if duoi == ".json" or (duoi in (".txt", ".md") and tho[:1] in "[{"):
        tho = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", tho)
        obj = json.loads(sua_gach(tho))
        ra = []
        duyet(obj, ma_dang, ra)
        return "\n\n".join(ra) + "\n"
    t = re.sub(r"```[a-zA-Z]*\n?", "", t)                    # bỏ rào ``` khi chép từ AI
    if ma_dang:
        t = KHOI.sub(lambda m: gan_ma(m.group(0), ma_dang), t)
    return t
