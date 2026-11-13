# -*- coding: utf-8 -*-
"""Thư viện dùng chung cho Ngân hàng cá nhân (gỡ lệnh rác, tách câu, đọc mã)."""
import re, json, hashlib, os, glob, collections

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))      # .../NganHangCaNhan
KHO_GOC = os.path.dirname(GOC)                                          # .../NganHangTHPT1.3

LOAI_TEN = {"TN": "Trắc nghiệm 4 phương án", "DS": "Đúng/Sai", "TLN": "Trả lời ngắn", "TL": "Tự luận"}
LOAI_THU_TU = {"TN": 0, "DS": 1, "TLN": 2, "TL": 3}

def doc(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()

def ghi(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def cau_hinh():
    p = os.path.join(GOC, "cau_hinh.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}

# ---------------------------------------------------------------- gỡ lệnh rác
TOKEN = re.compile(r"\\\\|\\([A-Za-z]+)(?=(.?))", re.S)
DEF_PATS = [
    r"\\(?:def|gdef|edef|xdef|let|newcommand\*?|renewcommand\*?|providecommand\*?|DeclareMathOperator\*?|"
    r"NewDocumentCommand|RenewDocumentCommand|newlength|newcounter|newif|pgfmathsetmacro|pgfmathtruncatemacro|"
    r"pgfmathsetlengthmacro|newsavebox|tikzmath)\s*\{?\s*\\([A-Za-z]+)",
    r"(?:count|remember)\s*=\s*\\([A-Za-z]+)", r"\bas\s*\\([A-Za-z]+)\s*(?:using|\]|,)",
    r"\\foreach\s*(?:\[[^\]]*\]\s*)?((?:\\[A-Za-z]+\s*/\s*)*\\[A-Za-z]+)\s*(?:\[[^\]]*\]\s*)?in\b",
]

def lenh_hop_le(cac_van_ban, them_file=()):
    """Tập tên lệnh chắc chắn là lệnh thật: lệnh TeX chuẩn + lệnh khai báo trong sty/Khaibao + lệnh tự định nghĩa trong dữ liệu."""
    hop_le = set()
    cac_van_ban = list(cac_van_ban)
    p = os.path.join(GOC, "scripts", "lenh_tex_chuan.txt")
    if os.path.exists(p):
        hop_le |= {l.strip().lstrip("\\") for l in open(p, encoding="utf-8") if l.strip()}
    for f in them_file:
        hop_le |= set(re.findall(r"\\([A-Za-z]+)", doc(f)))
    for t in cac_van_ban:
        hop_le |= lenh_tu_dinh_nghia(t)
    return hop_le

def tim_lenh_rac(cac_van_ban, hop_le):
    """Lệnh rác: tên chữ thường 3–6 ký tự, không bao giờ đứng sát ký tự khác khoảng trắng, và
    - không phải lệnh thật đã biết; hoặc
    - trùng tên lệnh thật nhưng >=80% số lần xuất hiện nằm ở 'vị trí rác' (theo sau là 2 dấu cách / cách+xuống dòng)."""
    dem, sat, vt_rac = collections.Counter(), collections.Counter(), collections.Counter()
    for t in cac_van_ban:
        for m in re.finditer(r"\\\\|\\([A-Za-z]+)(?=(.{0,2}))", t, re.S):
            k = m.group(1)
            if not k:
                continue
            dem[k] += 1
            nx = m.group(2)
            if nx[:1] and not nx[:1].isspace():
                sat[k] += 1
            elif re.match(r" [ \n\t]|\n| ?$", nx):
                vt_rac[k] += 1
    rac, nghi_van = set(), set()
    for k in dem:
        if not re.fullmatch(r"[a-z]{3,6}", k) or sat[k]:
            continue
        if k not in hop_le:
            rac.add(k)
        elif dem[k] >= 3 and vt_rac[k] >= 0.8 * dem[k]:
            rac.add(k)
        else:
            nghi_van.add(k)
    return rac, nghi_van, dem

def lenh_tu_dinh_nghia(text):
    """Tên lệnh được định nghĩa ngay trong đoạn văn bản (\\def, \\newcommand, biến \\foreach...)."""
    s = set()
    for pat in DEF_PATS:
        for g in re.findall(pat, text):
            s |= set(re.findall(r"[A-Za-z]+", g)) if "\\" in g else {g}
    return s

def go_rac_trong_cau(khoi, lenh_du_lieu):
    """Lệnh tự định nghĩa ở câu KHÁC (vd \\cau) mà xuất hiện trong câu này không có định nghĩa → là rác, xoá.
    Chỉ xét tên dạng rác (chữ thường 3–6 ký tự)."""
    co = {k for k in set(re.findall(r"\\([A-Za-z]+)", khoi)) & lenh_du_lieu if re.fullmatch(r"[a-z]{3,6}", k)}
    if not co:
        return khoi
    xoa = co - lenh_tu_dinh_nghia(khoi)
    # an toàn: chỉ xoá tên KHÔNG bao giờ đứng sát ký tự khác trong câu này, và chỉ xoá ở vị trí rác
    xoa = {k for k in xoa if not re.search(r"\\" + k + r"(?=[^A-Za-z\s])", khoi)}
    if not xoa:
        return khoi
    return re.sub(r"\\\\|\\([A-Za-z]+) (?=[ \t\n]|$)", lambda m: "" if m.group(1) in xoa else m.group(0), khoi)

def go_rac(text, rac):
    def thay(m):
        k = m.group(1)
        if k and k in rac:
            return ""
        return m.group(0)
    # xoá "\xxxx" + đúng MỘT dấu cách theo sau (dấu cách do bộ mã hoá chèn vào)
    return re.sub(r"\\\\|\\([A-Za-z]+) ?", thay, text)

# ---------------------------------------------------------------- tách câu
KHOI = re.compile(r"\\begin\{(ex|bt)\}(.*?)\\end\{\1\}", re.S)
MA_DANG = re.compile(r"%\[\s*(\d)([A-Z])(\d+)([A-Z?])(\d+)-(\d+)\s*\]")
MA_CAU = re.compile(r"%\[ma:([0-9a-f]{8})\]")

def doc_nhom(text, i):
    """Đọc nhóm {...} cân bằng bắt đầu tại text[i]=='{'. Trả (nội dung, vị trí sau '}')."""
    assert text[i] == "{"
    sau = 0; j = i
    while j < len(text):
        c = text[j]
        if c == "\\":
            j += 2; continue
        if c == "%":
            k = text.find("\n", j); j = len(text) if k < 0 else k; continue
        if c == "{":
            sau += 1
        elif c == "}":
            sau -= 1
            if sau == 0:
                return text[i + 1:j], j + 1
        j += 1
    raise ValueError("ngoặc không cân")

def bo_trang(text, j):
    while j < len(text):
        if text[j].isspace():
            j += 1
        elif text[j] == "%":
            k = text.find("\n", j); j = len(text) if k < 0 else k + 1
        else:
            break
    return j

def doc_tham_so(text, j, so):
    """Sau tên lệnh: bỏ [tuỳ chọn], đọc `so` nhóm {}. Trả (danh sách (đầu,cuối,nội dung), vị trí cuối)."""
    j = bo_trang(text, j)
    if j < len(text) and text[j] == "[":
        k = text.find("]", j); j = bo_trang(text, k + 1)
    ds = []
    for _ in range(so):
        j = bo_trang(text, j)
        if j >= len(text) or text[j] != "{":
            return None, j
        nd, sau = doc_nhom(text, j)
        ds.append((j, sau, nd)); j = sau
    return ds, j

def tim_lenh(text, ten):
    m = re.search(r"\\" + ten + r"(?![A-Za-z])", text)
    return m

def phan_tich_cau(khoi_text):
    """khoi_text: toàn bộ '\\begin{ex}...\\end{ex}'. Trả dict thông tin."""
    m = re.match(r"\\begin\{(ex|bt)\}", khoi_text)
    moi_truong = m.group(1)
    dong_dau = khoi_text[m.end():].split("\n", 1)[0]
    info = {"moi_truong": moi_truong, "id": None, "lop": None, "mon": None, "chuong": None,
            "muc": None, "bai": None, "dang": None, "dang_key": None, "ma": None}
    md = MA_DANG.search(dong_dau)
    if md:
        l, mon, ch, muc, bai, dg = md.groups()
        info.update(id=f"{l}{mon}{ch}{muc}{bai}-{dg}", lop=10 + int(l), mon=mon, chuong=int(ch), muc=muc,
                    bai=int(bai), dang=int(dg), dang_key=f"{l}{mon}{ch}?{bai}-{dg}")
    mc = MA_CAU.search(dong_dau)
    if mc:
        info["ma"] = mc.group(1)
    # loại câu + đáp án
    dap_an = None
    if tim_lenh(khoi_text, "choiceTF"):
        loai = "DS"
        mm = tim_lenh(khoi_text, "choiceTF"); ds, _ = doc_tham_so(khoi_text, mm.end(), 4)
        if ds:
            dap_an = "".join("Đ" if re.search(r"\\True(?![A-Za-z])", x[2]) else "S" for x in ds)
    elif tim_lenh(khoi_text, "choice"):
        loai = "TN"
        mm = tim_lenh(khoi_text, "choice"); ds, _ = doc_tham_so(khoi_text, mm.end(), 4)
        if ds:
            dung = [i for i, x in enumerate(ds) if re.search(r"\\True(?![A-Za-z])", x[2])]
            dap_an = "".join("ABCD"[i] for i in dung) or None
    elif tim_lenh(khoi_text, "shortans"):
        loai = "TLN"
        mm = tim_lenh(khoi_text, "shortans"); ds, _ = doc_tham_so(khoi_text, mm.end(), 1)
        if ds:
            dap_an = ds[0][2].strip().strip("$").strip()
    else:
        loai = "TL"
    info["loai"] = loai
    info["dap_an"] = dap_an
    ml = tim_lenh(khoi_text, "loigiai")
    co_lg = False
    if ml:
        ds, _ = doc_tham_so(khoi_text, ml.end(), 1)
        co_lg = bool(ds and ds[0][2].strip())
    info["co_loi_giai"] = co_lg
    info["co_hinh"] = bool(re.search(r"\\begin\{tikzpicture\}|\\includegraphics", khoi_text))
    return info

def chuan_hoa_de_so_sanh(khoi_text):
    """Dạng rút gọn để phát hiện câu trùng: bỏ chú thích, lời giải, \\True, khoảng trắng; phương án xếp lại."""
    t = re.sub(r"(?<!\\)%[^\n]*", "", khoi_text)
    ml = tim_lenh(t, "loigiai")
    if ml:
        ds, j = doc_tham_so(t, ml.end(), 1)
        if ds:
            t = t[:ml.start()] + t[j:]
    for ten in ("choiceTF", "choice"):
        mm = tim_lenh(t, ten)
        if mm:
            ds, j = doc_tham_so(t, mm.end(), 4)
            if ds:
                pa = sorted(re.sub(r"\\True(?![A-Za-z])", "", x[2]) for x in ds)
                t = t[:mm.start()] + "|".join(pa) + t[j:]
            break
    t = re.sub(r"\\True(?![A-Za-z])", "", t)
    return re.sub(r"\s+", "", t)

def ma_bam(khoi_text):
    return hashlib.sha1(chuan_hoa_de_so_sanh(khoi_text).encode("utf-8")).hexdigest()[:8]

def gan_ma(khoi_text, ma):
    """Chèn %[ma:xxxxxxxx] vào cuối dòng \\begin{..} (nếu chưa có)."""
    if MA_CAU.search(khoi_text.split("\n", 1)[0]):
        return khoi_text
    dau, _, sau = khoi_text.partition("\n")
    return f"{dau.rstrip()}%[ma:{ma}]\n{sau}"

def tach_khoi(text):
    return [m.group(0) for m in KHOI.finditer(text)]

def ten_khong_dau(s, toi_da=45):
    import unicodedata
    s = s.replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")
    return s[:toi_da].rstrip("_")

def tai_id_map():
    p = os.path.join(GOC, "du-lieu", "id_map.json")
    if not os.path.exists(p):
        p = os.path.join(KHO_GOC, "id_map.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}

def duong_dan_dang(info, id_map):
    """Thư mục/tên file chứa câu theo dạng."""
    if not info["dang_key"]:
        return None
    k = info["dang_key"]
    lop = f"lop{info['lop']}"
    chuong = f"{k[:3]}"
    ten = id_map.get(k)
    if ten:
        chuong += "_" + ten_khong_dau(ten["chap_name"], 40)
        f = f"{k[:3]}-{info['bai']}-{info['dang']}_{ten_khong_dau(ten['type_name'], 45)}.tex"
    else:
        f = f"{k[:3]}-{info['bai']}-{info['dang']}.tex"
    return os.path.join(lop, chuong, f)
