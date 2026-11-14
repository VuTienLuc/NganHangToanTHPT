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
    r"\\let\s*\\([A-Za-z]+)\s*=?\s*\\",
    r"\\(?:def|gdef|edef|xdef|newcommand\*?|renewcommand\*?|providecommand\*?|DeclareMathOperator\*?|"
    r"NewDocumentCommand|RenewDocumentCommand|newlength|newcounter|newif|pgfmathsetmacro|pgfmathtruncatemacro|"
    r"pgfmathsetlengthmacro|newsavebox|tikzmath)\s*\{?\s*\\([A-Za-z]+)(?=\s*[{}#(\[=])",
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

def lop_tu_so(l):
    """Chữ số lớp trong mã dạng → lớp: 0→10, 1→11, 2→12; 6…9 → lớp 6…9 (THCS, KNTT)."""
    l = int(l)
    return l if l >= 6 else 10 + l

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
        info.update(id=f"{l}{mon}{ch}{muc}{bai}-{dg}", lop=lop_tu_so(l), mon=mon, chuong=int(ch), muc=muc,
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

# ---------------------------------------------------------------- xuất Excel (không cần cài openpyxl)
def ghi_xlsx(duong_dan, cac_sheet):
    """cac_sheet: [(ten_sheet, rows, {"do_rong": [..], "kieu": "bang"|"van_ban"})]. Mọi ô ghi dạng chữ.
    Bảng: dòng 1 và cột A in đậm nền xanh nhạt, mọi ô có viền, căn giữa, ô trống tô vàng. Phông Times New Roman."""
    import zipfile
    from xml.sax.saxutils import escape as xe
    def ten_cot(i):
        s = ""
        i += 1
        while i:
            i, r = divmod(i - 1, 26); s = chr(65 + r) + s
        return s
    styles = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<numFmts count="0"/>
<fonts count="3"><font><sz val="12"/><name val="Times New Roman"/></font><font><b/><sz val="12"/><name val="Times New Roman"/></font><font><b/><sz val="14"/><name val="Times New Roman"/></font></fonts>
<fills count="4"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFE8ECF9"/><bgColor indexed="64"/></patternFill></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFFCEFD5"/><bgColor indexed="64"/></patternFill></fill></fills>
<borders count="2"><border><left/><right/><top/><bottom/><diagonal/></border>
<border><left style="thin"><color rgb="FF9AA3AF"/></left><right style="thin"><color rgb="FF9AA3AF"/></right><top style="thin"><color rgb="FF9AA3AF"/></top><bottom style="thin"><color rgb="FF9AA3AF"/></bottom><diagonal/></border></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="6">
<xf numFmtId="49" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>
<xf numFmtId="49" fontId="1" fillId="2" borderId="1" xfId="0" applyNumberFormat="1" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>
<xf numFmtId="49" fontId="0" fillId="0" borderId="1" xfId="0" applyNumberFormat="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>
<xf numFmtId="49" fontId="0" fillId="3" borderId="1" xfId="0" applyNumberFormat="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>
<xf numFmtId="49" fontId="2" fillId="0" borderId="0" xfId="0" applyNumberFormat="1" applyFont="1"/>
<xf numFmtId="49" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1" applyAlignment="1"><alignment wrapText="1" vertical="top"/></xf>
</cellXfs>
<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>"""
    sheets_xml = []
    for ten, rows, opt in cac_sheet:
        bang = opt.get("kieu", "bang") == "bang"
        cols = "".join(f'<col min="{i + 1}" max="{i + 1}" width="{w}" customWidth="1"/>' for i, w in enumerate(opt.get("do_rong", [])))
        sd = []
        for r, row in enumerate(rows):
            cells = []
            for c, v in enumerate(row):
                v = "" if v is None else str(v)
                if bang:
                    st = 1 if (r == 0 or c == 0) else (3 if v == "" else 2)
                else:
                    st = 4 if r == 0 else 5
                ref = f"{ten_cot(c)}{r + 1}"
                if v == "":
                    cells.append(f'<c r="{ref}" s="{st}"/>')
                else:
                    cells.append(f'<c r="{ref}" s="{st}" t="inlineStr"><is><t xml:space="preserve">{xe(v)}</t></is></c>')
            sd.append(f'<row r="{r + 1}">{"".join(cells)}</row>')
        pane = ('<sheetViews><sheetView workbookViewId="0"><pane xSplit="1" ySplit="1" topLeftCell="B2" activePane="bottomRight" state="frozen"/></sheetView></sheetViews>'
                if bang else '<sheetViews><sheetView workbookViewId="0"/></sheetViews>')
        sheets_xml.append(f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">{pane}'
                          + (f"<cols>{cols}</cols>" if cols else "") + f'<sheetData>{"".join(sd)}</sheetData></worksheet>')
    n = len(cac_sheet)
    with zipfile.ZipFile(duong_dan, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
                   + "".join(f'<Override PartName="/xl/worksheets/sheet{i + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(n)) + "</Types>")
        z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr("xl/workbook.xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
                   + "".join(f'<sheet name="{xe(cac_sheet[i][0])}" sheetId="{i + 1}" r:id="rId{i + 1}"/>' for i in range(n)) + "</sheets></workbook>")
        z.writestr("xl/_rels/workbook.xml.rels", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   + "".join(f'<Relationship Id="rId{i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i + 1}.xml"/>' for i in range(n))
                   + f'<Relationship Id="rId{n + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>')
        z.writestr("xl/styles.xml", styles)
        for i, x in enumerate(sheets_xml):
            z.writestr(f"xl/worksheets/sheet{i + 1}.xml", x)

# ---------------------------------------------------------------- biên dịch PDF
def tim_pdflatex():
    import shutil as _sh
    for c in (_sh.which("pdflatex"), "/Library/TeX/texbin/pdflatex", "/opt/homebrew/bin/pdflatex",
              "/usr/local/texlive/2026/bin/universal-darwin/pdflatex", "/usr/local/texlive/2025/bin/universal-darwin/pdflatex"):
        if c and os.path.exists(c):
            return c
    return None

def bien_dich_thu_muc(thu_muc_de, in_ra=print):
    """Biên dịch tex/De_*.tex (2 lần để đúng số trang) rồi chép PDF ra thư mục đề."""
    import subprocess, shutil as _sh, time as _t
    pdfl = tim_pdflatex()
    if not pdfl:
        in_ra("Không tìm thấy pdflatex (MacTeX/MiKTeX) — mở các file trong thư mục tex/ bằng TeXstudio để biên dịch.")
        return False
    tex = os.path.join(thu_muc_de, "tex")
    tep = sorted(f for f in os.listdir(tex) if f.startswith("De_") and f.endswith(".tex"))
    if tep:
        in_ra(f"Biên dịch {len(tep)} file PDF…")
    ok_het = True
    for f in tep:
        bat_dau = _t.time()
        for _ in range(2):
            subprocess.run([pdfl, "-interaction=nonstopmode", f], cwd=tex, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=900)
        pdf = os.path.join(tex, f[:-4] + ".pdf")
        ok = os.path.exists(pdf) and os.path.getmtime(pdf) >= bat_dau - 1
        if ok:
            ten_ra = f[:-4].replace("De_", "LoiGiai_", 1).replace("_LoiGiai", "") if f.endswith("_LoiGiai.tex") else f[:-4]
            _sh.copyfile(pdf, os.path.join(thu_muc_de, ten_ra + ".pdf"))
        ok_het &= ok
        in_ra(f"  {'✓' if ok else '✗ lỗi (xem tex/' + f[:-4] + '.log)'} {f[:-4]}")
    # bản Leftnote (lề ghi chú) và Beamer trình chiếu sửa bài (trắng / xanh) cho từng mã đề
    phu = sorted(f for f in os.listdir(tex) if re.match(r"(Leftnote|BeamerTrang|BeamerXanh)_\d+\.tex$", f))
    if phu:
        in_ra(f"Biên dịch {len(phu)} file Leftnote / Beamer…")
    for f in phu:
        bat_dau = _t.time()
        for _ in range(2):
            subprocess.run([pdfl, "-interaction=nonstopmode", f], cwd=tex, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=1800)
        pdf = os.path.join(tex, f[:-4] + ".pdf")
        ok = os.path.exists(pdf) and os.path.getmtime(pdf) >= bat_dau - 1
        if ok:
            _sh.copyfile(pdf, os.path.join(thu_muc_de, f[:-4] + ".pdf"))
        ok_het &= ok
        in_ra(f"  {'✓' if ok else '✗ lỗi (xem tex/' + f[:-4] + '.log)'} {f[:-4]}")
    # phiếu bài học / chuyên đề / ôn tập chương (3 lần cho đúng "Trang x/y")
    if os.path.exists(os.path.join(tex, "PhieuBaiHoc.tex")):
        try:
            ten_p = open(os.path.join(tex, "_ten_phieu.txt"), encoding="utf-8").read().strip() or "Phieu bai hoc"
        except OSError:
            ten_p = "Phieu bai hoc"
        for f, duoi in (("PhieuBaiHoc.tex", ""), ("PhieuBaiHoc_LoiGiai.tex", " - Lời giải"),
                        ("PhieuTrenLop.tex", " - Trên lớp"), ("PhieuTrenLop_LoiGiai.tex", " - Trên lớp - Lời giải"),
                        ("PhieuVeNha.tex", " - Về nhà"), ("PhieuVeNha_LoiGiai.tex", " - Về nhà - Lời giải"),
                        ("PhieuBeamer.tex", " - Trình chiếu")):
            if not os.path.exists(os.path.join(tex, f)):
                continue
            in_ra(f"Biên dịch {ten_p}{duoi}…")
            bat_dau = _t.time()
            for _ in range(3):
                subprocess.run([pdfl, "-interaction=nonstopmode", f], cwd=tex, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, timeout=1800)
            pdf = os.path.join(tex, f[:-4] + ".pdf")
            ok = os.path.exists(pdf) and os.path.getmtime(pdf) >= bat_dau - 1
            if ok:
                _sh.copyfile(pdf, os.path.join(thu_muc_de, f"{ten_p}{duoi}.pdf"))
            ok_het &= ok
            in_ra(f"  {'✓' if ok else '✗ lỗi (xem tex/' + f[:-4] + '.log)'} {ten_p}{duoi}.pdf")
    # quyển đề cương ôn tập: 2 file riêng (Câu hỏi / Lời giải) — biên dịch 3 lần cho đúng mục lục, số trang
    ten = "De cuong on tap"
    try:
        ten = open(os.path.join(tex, "_ten_de_cuong.txt"), encoding="utf-8").read().strip() or ten
    except OSError:
        pass
    for f, duoi in (("DeCuong_CauHoi.tex", "Câu hỏi"), ("DeCuong_LoiGiai.tex", "Lời giải")):
        if not os.path.exists(os.path.join(tex, f)):
            continue
        in_ra(f"Biên dịch quyển đề cương – {duoi}…")
        bat_dau = _t.time()
        for _ in range(3):
            subprocess.run([pdfl, "-interaction=nonstopmode", f], cwd=tex, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=1800)
        pdf = os.path.join(tex, f[:-4] + ".pdf")
        ok = os.path.exists(pdf) and os.path.getmtime(pdf) >= bat_dau - 1
        if ok:
            _sh.copyfile(pdf, os.path.join(thu_muc_de, f"{ten} - {duoi}.pdf"))
        ok_het &= ok
        in_ra(f"  {'✓' if ok else '✗ lỗi (xem tex/' + f[:-4] + '.log)'} {ten} - {duoi}.pdf")
    return ok_het
