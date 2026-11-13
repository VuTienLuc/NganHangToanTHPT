# -*- coding: utf-8 -*-
"""
XUẤT ĐỀ RA WORD (.docx) THEO MẪU NHẬP CÂU HỎI CỦA K12ONLINE (dạng 2025).
Công thức toán, bảng biến thiên, hình vẽ được biên dịch bằng LaTeX (cỡ 12pt) rồi chèn vào Word dưới dạng
ảnh SVG sắc nét (kèm PNG 600 dpi dự phòng). Mỗi ảnh được hạ xuống đúng phần nằm dưới đường chân chữ
(baseline) nên công thức thẳng hàng với chữ, không lệch dòng. Chữ thường: Times New Roman 12.

  python3 scripts/k12word.py "de-da-ra/<thư mục đề>"
(tron_de.py tự gọi khi có --word; ứng dụng: tích "Xuất Word K12Online").

Mẫu K12Online (3 phần, đánh số câu lại từ 1 ở mỗi phần):
  Phần I: / Trắc nghiệm nhiều lựa chọn (…) / Câu 1: … / A. B. C. D. (chữ cái đáp án đúng được gạch chân) / Lời giải: …
  Phần II: / Trắc nghiệm đúng – sai (…) / Câu 1: … / a) … (ý đúng gạch chân "a)") / Lời giải: … (sau từng ý)
  Phần III: / Trả lời ngắn (…) / Câu 1: … / Đáp án: / 2024 / Lời giải: …
Công thức toán: mặc định chuyển thành Equation của Word (pandoc) → luôn thẳng dòng, sửa được, K12Online nhận đúng;
công thức pandoc không đọc được và hình vẽ/bảng biến thiên thì dùng ảnh SVG (+PNG). Đặt NH_CONG_THUC=svg để ép dùng ảnh.
Cần: pandoc (brew install pandoc hoặc pip3 install pypandoc_binary); pdflatex + latex + dvisvgm + gs (MacTeX đầy đủ).
"""
import os, sys, re, json, glob, shutil, subprocess, zipfile, hashlib
from xml.sax.saxutils import escape as xe
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nh_core import tim_lenh, doc_tham_so, doc_nhom, tim_pdflatex

MUC_K12 = {"N": "[NB]", "H": "[TH]", "V": "[VDT]", "C": "[VDC]"}
PT = 12700                               # EMU / point
RONG_TOI_DA = 16.0 / 2.54 * 72           # ảnh rộng tối đa 16 cm
VIEN = {"im": 0.6, "dm": 1.5, "env": 1.5, "fig": 14.0}   # viền trắng quanh từng mảnh (pt)

# ======================================================================= LaTeX → đoạn văn
MOI_TRUONG_HINH = {"tikzpicture", "tabular", "tabularx", "tabu", "longtable", "pspicture"}
MOI_TRUONG_TOAN = {"align", "align*", "equation", "equation*", "gather", "gather*", "eqnarray", "eqnarray*",
                   "multline", "multline*", "flalign", "flalign*", "displaymath"}
BO_LENH = {"noindent", "centering", "par", "medskip", "smallskip", "bigskip", "allowdisplaybreaks", "displaystyle",
           "raggedright", "raggedleft", "normalsize", "small", "footnotesize", "large", "Large", "relax", "indent",
           "selectfont", "nopagebreak", "pagebreak", "newpage", "clearpage", "item", "bfseries", "itshape", "sffamily",
           "True", "hfil", "vfill", "break", "linebreak", "null", "xuongdong"}
BO_LENH_TS = {"vspace": 1, "hspace": 1, "vspace*": 1, "hspace*": 1, "label": 1, "setlength": 2, "addtolength": 2,
              "color": 1, "textcolor": 2, "colorbox": 2}
KY_HIEU = {"lq": "“", "rq": "”", "ldots": "…", "dots": "…", "%": "%", "&": "&", "_": "_", "#": "#", "{": "{", "}": "}",
           "$": "$", "quad": "  ", "qquad": "    ", "hfill": " ", ",": " ", ";": " ", " ": " ", ":": " ", "!": "",
           "S": "§", "textdegree": "°", "degree": "°", "-": ""}
DINH_DANG = {"textbf": "b", "textit": "i", "emph": "i", "underline": "u", "text": None, "textrm": None,
             "textup": None, "textsc": None, "mbox": None, "textnormal": None, "textsf": None}

def bo_chu_thich(t):
    return re.sub(r"(?<!\\)%[^\n]*", "", t)

class Doan:
    def __init__(self, can="left"):
        self.can, self.chay = can, []

class BoChuyen:
    """Chuyển một đoạn LaTeX (đề, phương án, lời giải) thành các đoạn văn; công thức/hình thành 'mảnh' để biên dịch."""
    def __init__(self, manh):
        self.manh = manh          # khoá → (loại, mã LaTeX)
        self.doan = []

    def them_manh(self, loai, ma):
        ma = ma.strip()
        k = hashlib.sha1((loai + "|" + ma).encode()).hexdigest()[:12]
        self.manh.setdefault(k, (loai, ma))
        return k

    def doan_hien(self):
        if not self.doan:
            self.doan.append(Doan())
        return self.doan[-1]

    def doan_moi(self, can="left"):
        d = self.doan_hien()
        if not d.chay:
            d.can = can
            return d
        self.doan.append(Doan(can))
        return self.doan[-1]

    def anh_rieng(self, loai, ma):
        k = self.them_manh(loai, ma)
        self.doan_moi("center").chay.append(("m", k))
        self.doan_moi()

    def chuyen(self, t, dd=frozenset()):
        i, n, buf = 0, len(t), []

        def xa():
            if buf:
                s = re.sub(r"[ \t\r\n]+", " ", "".join(buf))
                buf.clear()
                if s:
                    self.doan_hien().chay.append(("t", s, dd))

        while i < n:
            c = t[i]
            if t.startswith("$$", i) or t.startswith("\\[", i):
                ket = "$$" if c == "$" else "\\]"
                j = t.find(ket, i + 2)
                j = n if j < 0 else j
                xa(); self.anh_rieng("dm", t[i + 2:j])
                i = j + 2; continue
            if c == "$" or t.startswith("\\(", i):
                ket = "$" if c == "$" else "\\)"
                j = i + len(ket)
                while j < n and not (t.startswith(ket, j) and t[j - 1] != "\\"):
                    j += 1
                xa()
                k = self.them_manh("im", t[i + len(ket):j])
                self.doan_hien().chay.append(("m", k))
                i = j + len(ket); continue
            if c == "\\":
                m = re.match(r"\\([A-Za-z]+\*?|.)", t[i:])
                ten, j = m.group(1), i + m.end()
                if ten == "\\":
                    xa(); self.doan_hien().chay.append(("br",))
                    i = j + re.match(r"\s*(\[[^\]]*\])?", t[j:]).end(); continue
                if ten == "begin":
                    mm = re.match(r"\{([^}]*)\}", t[j:])
                    env = mm.group(1); dau_trong = j + mm.end()
                    ket = self.tim_end(t, env, dau_trong)
                    trong = t[dau_trong:ket]; sau = min(n, ket + len(f"\\end{{{env}}}"))
                    xa()
                    if env in MOI_TRUONG_HINH:
                        self.anh_rieng("fig", t[i:sau])
                    elif env in MOI_TRUONG_TOAN:
                        self.anh_rieng("env", f"\\begin{{{env}}}{trong}\\end{{{env}}}")
                    elif env == "center":
                        self.doan_moi("center"); self.chuyen(trong, dd); self.doan_moi()
                    elif env in ("itemize", "enumerate", "itemchoice", "enumEX", "tasks"):
                        trong = re.sub(r"^\s*(\[[^\]]*\]|\(\d+\))", "", trong)
                        cac = re.split(r"\\(?:item|itemch|task)(?![A-Za-z])", trong)[1:]
                        for so, it in enumerate(cac):
                            self.doan_moi()
                            nhan = "• " if env == "itemize" else (f"{'abcdefghij'[so % 10]}) " if env != "itemchoice" else "")
                            if nhan:
                                self.doan_hien().chay.append(("t", nhan, dd))
                            self.chuyen(it, dd)
                        self.doan_moi()
                    else:
                        self.chuyen(trong, dd)
                    i = sau; continue
                if ten in DINH_DANG:
                    mm = re.match(r"\s*\{", t[j:])
                    if mm:
                        nd, sau = doc_nhom(t, j + mm.end() - 1)
                        xa()
                        them = DINH_DANG[ten]
                        self.chuyen(nd, (dd | {them}) if them else dd)
                        i = sau; continue
                if ten == "immini":
                    ds, sau = doc_tham_so(t, j, 2)
                    if ds:
                        xa(); self.chuyen(ds[0][2], dd)
                        hinh = ds[1][2].strip()
                        if hinh.startswith("\\begin"):
                            self.doan_moi(); self.chuyen(hinh, dd)
                        elif hinh:
                            self.anh_rieng("fig", hinh)
                        i = sau; continue
                if ten in ("resizebox", "scalebox", "adjustbox", "rotatebox"):
                    so_ts = 3 if ten == "resizebox" else 2
                    ds, sau = doc_tham_so(t, j, so_ts)
                    if ds:
                        xa(); self.anh_rieng("fig", t[i:sau])
                        i = sau; continue
                if ten == "includegraphics":
                    mm = re.match(r"\s*(\[[^\]]*\])?\s*\{[^}]*\}", t[j:])
                    if mm:
                        xa(); self.anh_rieng("fig", t[i:j + mm.end()])
                        i = j + mm.end(); continue
                if ten in KY_HIEU:
                    buf.append(KY_HIEU[ten]); i = j; continue
                if ten == "newline":
                    xa(); self.doan_hien().chay.append(("br",)); i = j; continue
                if ten in BO_LENH_TS:
                    ds, sau = doc_tham_so(t, j, BO_LENH_TS[ten])
                    if ds and ten in ("textcolor", "colorbox"):
                        xa(); self.chuyen(ds[-1][2], dd)
                    i = sau if ds else j; continue
                # lệnh lạ hoặc lệnh bỏ qua: bỏ tên lệnh, giữ nội dung các nhóm {…} theo sau
                i = j; continue
            if c in "{}":
                i += 1; continue
            if c == "~":
                buf.append("\u00a0"); i += 1; continue
            if c == "\n" and re.match(r"\n[ \t]*\n", t[i:]):
                xa(); self.doan_moi(); i += 1; continue
            if t.startswith("``", i) or t.startswith("''", i):
                buf.append("“" if c == "`" else "”"); i += 2; continue
            if t.startswith("---", i):
                buf.append("—"); i += 3; continue
            if t.startswith("--", i):
                buf.append("–"); i += 2; continue
            buf.append(c); i += 1
        xa()
        return self.doan

    @staticmethod
    def tim_end(t, env, tu):
        mo, dong = f"\\begin{{{env}}}", f"\\end{{{env}}}"
        sau, j = 1, tu
        while True:
            a, b = t.find(mo, j), t.find(dong, j)
            if b < 0:
                return len(t)
            if 0 <= a < b:
                sau += 1; j = a + len(mo)
            else:
                sau -= 1
                if sau == 0:
                    return b
                j = b + len(dong)

def chuyen(t, manh):
    bc = BoChuyen(manh)
    bc.chuyen(bo_chu_thich(t or ""))
    kq = []
    for d in bc.doan:
        while d.chay and d.chay[0][0] in ("t", "br") and (d.chay[0][0] == "br" or not d.chay[0][1].strip()):
            d.chay.pop(0)
        while d.chay and d.chay[-1][0] in ("t", "br") and (d.chay[-1][0] == "br" or not d.chay[-1][1].strip()):
            d.chay.pop()
        if d.chay:
            if d.chay[0][0] == "t":
                d.chay[0] = ("t", d.chay[0][1].lstrip(), d.chay[0][2])
            kq.append(d)
    return kq

# ======================================================================= tách một câu
def tach_cau(cau):
    """cau: {loai, noi_dung, dap_an, muc} → {de, pa[4], lg, tln, y_giai}."""
    k = cau["noi_dung"]
    m = re.match(r"\\begin\{(ex|bt)\}[^\n]*\n?", k)
    than = k[m.end():] if m else k
    than = re.sub(r"\\end\{(ex|bt)\}\s*$", "", than.rstrip())
    than = bo_chu_thich(than)
    cat, pa, lg, tln = [], None, "", None
    for ten in ("choiceTF", "choice", "shortans", "loigiai"):
        mm = tim_lenh(than, ten)
        if not mm:
            continue
        ds, cuoi = doc_tham_so(than, mm.end(), 4 if ten in ("choice", "choiceTF") else 1)
        if not ds:
            continue
        cat.append((mm.start(), cuoi))
        if ten in ("choice", "choiceTF"):
            pa = [re.sub(r"\\True(?![A-Za-z])", "", x[2]).strip() for x in ds]
        elif ten == "shortans":
            tln = ds[0][2]
        else:
            lg = ds[0][2]
    de = than
    for a, b in sorted(cat, reverse=True):
        de = de[:a] + de[b:]
    y_giai = None
    if cau["loai"] == "DS" and lg:
        mi = re.search(r"\\begin\{itemchoice\}(.*)\\end\{itemchoice\}", lg, re.S)
        if mi:
            p = re.split(r"\\itemch(?![A-Za-z])", mi.group(1))
            if len(p) == 5:
                y_giai = (lg[:mi.start()], p[1:], lg[mi.end():])
    return {"de": de, "pa": pa, "lg": lg, "tln": tln, "y_giai": y_giai}

# ======================================================================= biên dịch mảnh → SVG + PNG
def tim(cong_cu):
    for c in (shutil.which(cong_cu), f"/Library/TeX/texbin/{cong_cu}", f"/usr/local/bin/{cong_cu}",
              f"/opt/homebrew/bin/{cong_cu}", f"/usr/bin/{cong_cu}"):
        if c and os.path.exists(c):
            return c
    return None

def dau_van_ban(thu_muc_tex):
    """Phần đầu tài liệu lấy từ file đề (đủ macro \\heva, \\hoac, tkz-tab…), ép cỡ chữ 12pt, thêm preview."""
    mau = sorted(glob.glob(os.path.join(thu_muc_tex, "De_*.tex")))[0]
    t = open(mau, encoding="utf-8").read()
    pre = t[:t.index("\\begin{document}")]
    pre = re.sub(r"\\documentclass\[[^\]]*\]\{[^}]*\}", r"\\documentclass[12pt,oneside]{book}", pre, count=1)
    pre = re.sub(r"\\tikzset\{every picture/\.append style=\{scale=[^}]*\}\}", "", pre)
    pre = re.sub(r"\\renewcommand\{\\immini\}[^\n]*\n", "", pre)
    pre = re.sub(r"\\usepackage\{multicol\}[^\n]*\n", "", pre)
    pre = pre.replace("\\usepackage[hidelinks]{hyperref}", "")
    if os.environ.get("NH_THAY_VIETNAM"):          # chỉ dùng khi thử trên máy không có gói vietnam
        pre = pre.replace("\\usepackage[utf8]{vietnam}", os.environ["NH_THAY_VIETNAM"])
    # công thức dùng phông Times (mathptmx) cho hợp với chữ Times New Roman của Word; giữ nguyên phông chữ thường
    pre += ("\\let\\rmgocKW\\rmdefault\\usepackage{mathptmx}\\let\\rmdefault\\rmgocKW\n")
    pre += ("\\usepackage[active,tightpage]{preview}\n\\setlength\\PreviewBorder{0pt}\n"
            "\\pagestyle{empty}\n\\newsavebox\\hopmanh\n")
    return pre

def ma_manh(loai, ma):
    if loai == "im":
        return f"$\\textstyle {ma}$"
    if loai == "dm":
        return f"$\\displaystyle {ma}$"
    if loai == "env":
        m = re.match(r"\\begin\{([^}]*)\}(.*)\\end\{\1\}", ma, re.S)
        env, nd = m.group(1).rstrip("*"), m.group(2)
        nd = re.sub(r"\\(label\{[^}]*\}|nonumber|notag)", "", nd)
        if env in ("align", "flalign", "multline"):
            return f"$\\displaystyle\\begin{{aligned}}{nd}\\end{{aligned}}$"
        if env == "gather":
            return f"$\\displaystyle\\begin{{gathered}}{nd}\\end{{gathered}}$"
        if env == "eqnarray":
            return f"$\\displaystyle\\begin{{array}}{{rcl}}{nd}\\end{{array}}$"
        return f"$\\displaystyle {nd}$"
    return ma                                        # hình: tikzpicture, tabular, includegraphics…

def chay_lenh(lenh, cwd, env):
    try:
        subprocess.run(lenh, cwd=cwd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1200)
    except Exception:
        pass

def bien_dich_manh(manh, thu_muc_tex, in_ra=print):
    """Trả {khoá: {svg, png, w, h, d}} — kích thước theo point, h = cao trên baseline, d = sâu dưới baseline."""
    tm = os.path.join(thu_muc_tex, "_k12")
    os.makedirs(tm, exist_ok=True)
    for f in glob.glob(os.path.join(tm, "*")):
        try:
            os.remove(f)
        except OSError:
            pass
    khoa = list(manh)
    pre = dau_van_ban(thu_muc_tex)
    # viền trắng quanh mảnh (pt): công thức trong dòng sát chữ; hình/bảng chừa rộng vì nét vẽ hay tràn ra ngoài hộp
    vien = {k: VIEN.get(manh[k][0], 1.0) for k in khoa}
    than = "\n".join(f"\\sbox\\hopmanh{{{ma_manh(*manh[k])}}}"
                     f"\\typeout{{KICHTHUOC {i + 1}:\\the\\wd\\hopmanh,\\the\\ht\\hopmanh,\\the\\dp\\hopmanh}}"
                     f"\\setlength\\PreviewBorder{{{vien[k]}pt}}"
                     f"\\begin{{preview}}\\usebox\\hopmanh\\end{{preview}}\\newpage" for i, k in enumerate(khoa))
    env = dict(os.environ)
    if os.environ.get("NH_TEXINPUTS"):
        env["TEXINPUTS"] = os.environ["NH_TEXINPUTS"]
    kq = {k: {} for k in khoa}
    pdfl = tim_pdflatex()
    if not pdfl:
        raise RuntimeError("Không tìm thấy pdflatex (MacTeX) — cần LaTeX để vẽ công thức.")
    # 1) pdflatex: đo kích thước từng mảnh + PDF để tạo PNG
    open(os.path.join(thu_muc_tex, "_k12_pdf.tex"), "w", encoding="utf-8").write(
        pre + "\\begin{document}\n" + than + "\n\\end{document}\n")
    chay_lenh([pdfl, "-interaction=nonstopmode", "_k12_pdf.tex"], thu_muc_tex, env)
    log = open(os.path.join(thu_muc_tex, "_k12_pdf.log"), encoding="latin-1").read()
    for so, w, h, d in re.findall(r"KICHTHUOC (\d+):(-?[\d.]+)pt,(-?[\d.]+)pt,(-?[\d.]+)pt", log):
        i = int(so) - 1
        if i < len(khoa) and float(w) > 0:
            b = vien[khoa[i]]          # ảnh gồm cả viền: rộng w+2b, cao h+d+2b, phần dưới baseline d+b
            bp = 72 / 72.27            # pt của TeX → pt của Word/SVG (big point)
            kq[khoa[i]].update(w=(float(w) + 2 * b) * bp, h=(float(h) + b) * bp,
                               d=(max(0.0, float(d)) + b) * bp, b=b * bp)
    pdf = os.path.join(thu_muc_tex, "_k12_pdf.pdf")
    if not os.path.exists(pdf):
        raise RuntimeError("Biên dịch công thức thất bại — xem tex/_k12_pdf.log")
    gs, pdc = tim("gs"), tim("pdftocairo")
    if gs:
        chay_lenh([gs, "-q", "-dNOPAUSE", "-dBATCH", "-dSAFER", "-sDEVICE=pngalpha", "-r600",
                   "-dTextAlphaBits=4", "-dGraphicsAlphaBits=4", "-o", os.path.join(tm, "p%04d.png"), pdf], thu_muc_tex, env)
    elif pdc:
        chay_lenh([pdc, "-png", "-r", "600", "-transp", pdf, os.path.join(tm, "p")], thu_muc_tex, env)
    for i, k in enumerate(khoa):
        for ten in (f"p{i + 1:04d}.png", f"p-{i + 1}.png", f"p-{i + 1:02d}.png", f"p-{i + 1:03d}.png", f"p-{i + 1:04d}.png"):
            if os.path.exists(os.path.join(tm, ten)):
                kq[k]["png"] = os.path.join(tm, ten); break
    # 2) SVG: latex (DVI) + dvisvgm --no-fonts → chữ trong công thức thành nét vẽ, sắc nét, không phụ thuộc phông
    lt, dv = tim("latex"), tim("dvisvgm")
    co_svg = False
    if lt and dv:
        open(os.path.join(thu_muc_tex, "_k12_dvi.tex"), "w", encoding="utf-8").write(
            "\\def\\pgfsysdriver{pgfsys-dvisvgm.def}\n" + pre + "\\begin{document}\n" + than + "\n\\end{document}\n")
        chay_lenh([lt, "-interaction=nonstopmode", "_k12_dvi.tex"], thu_muc_tex, env)
        dvi = os.path.join(thu_muc_tex, "_k12_dvi.dvi")
        if os.path.exists(dvi):
            chay_lenh([dv, "--no-fonts", "--page=1-", "-o", os.path.join(tm, "s%4p.svg"), dvi], thu_muc_tex, env)
            for i, k in enumerate(khoa):
                p = os.path.join(tm, f"s{i + 1:04d}.svg")
                if os.path.exists(p) and os.path.getsize(p) > 100:
                    m = kq[k]
                    if "w" in m:   # khung SVG = đúng hộp TeX (gốc toạ độ tại điểm đầu baseline) → không lệch dòng
                        sv = open(p, encoding="utf-8").read()
                        sv = re.sub(r"<svg([^>]*?)\swidth='[^']*'\sheight='[^']*'\sviewBox='[^']*'",
                                    lambda x: f"<svg{x.group(1)} width='{m['w']:.4f}pt' height='{m['h'] + m['d']:.4f}pt' "
                                              f"viewBox='{-m['b']:.4f} {-m['h']:.4f} {m['w']:.4f} {m['h'] + m['d']:.4f}'", sv, count=1)
                        open(p, "w", encoding="utf-8").write(sv)
                    kq[k]["svg"] = p; co_svg = True
    if not co_svg and pdc:                           # dự phòng: PDF → SVG bằng pdftocairo
        for i, k in enumerate(khoa):
            p = os.path.join(tm, f"c{i + 1:04d}.svg")
            chay_lenh([pdc, "-svg", "-f", str(i + 1), "-l", str(i + 1), pdf, p], thu_muc_tex, env)
            if os.path.exists(p):
                kq[k]["svg"] = p; co_svg = True
    loi = [k for k in khoa if "w" not in kq[k] or not (kq[k].get("svg") or kq[k].get("png"))]
    in_ra(f"  Công thức/hình: {len(khoa)} mảnh · SVG: {'có' if co_svg else 'KHÔNG (thiếu latex/dvisvgm)'} · "
          f"PNG 600dpi: {'có' if any('png' in v for v in kq.values()) else 'KHÔNG (thiếu Ghostscript)'}"
          + (f" · {len(loi)} mảnh lỗi (xem tex/_k12_pdf.log)" if loi else ""))
    return kq

# ======================================================================= công thức → Equation (OMML) bằng pandoc
MACRO_PANDOC = ("\\newcommand{\\heva}[1]{\\left\\{\\begin{aligned}#1\\end{aligned}\\right.}\n"
                "\\newcommand{\\hoac}[1]{\\left[\\begin{aligned}#1\\end{aligned}\\right.}\n"
                "\\newcommand{\\vv}[1]{\\overrightarrow{#1}}\n\\newcommand{\\Bbb}[1]{\\mathbb{#1}}\n"
                "\\newcommand{\\rm}{}\n\\newcommand{\\allowdisplaybreaks}{}\n\n")

def tim_pandoc():
    p = tim("pandoc")
    if p:
        return p
    try:
        import pypandoc
        return pypandoc.get_pandoc_path()
    except Exception:
        return None

def ma_toan_tran(loai, ma):
    """Mã TeX của công thức (bỏ $…$) để đưa cho pandoc."""
    t = ma_manh(loai, ma).strip()
    t = t[1:-1] if t.startswith("$") and t.endswith("$") else t
    t = re.sub(r"^\\textstyle\s*", "", t)
    return " ".join(t.split())

def omml_cong_thuc(manh, in_ra=print, cong_thuc="equation"):
    """{khoá: '<m:oMath>…</m:oMath>'} cho các công thức pandoc chuyển được."""
    if (os.environ.get("NH_CONG_THUC") or cong_thuc or "").lower() == "svg":
        return {}
    pd = tim_pandoc()
    if not pd:
        in_ra("  (Không thấy pandoc → công thức dùng ảnh SVG. Cài: brew install pandoc  hoặc  pip3 install pypandoc_binary)")
        return {}
    khoa = [k for k, (l, _) in manh.items() if l in ("im", "dm", "env")]
    if not khoa:
        return {}
    md = MACRO_PANDOC + "\n\n".join("$" + (ma_toan_tran(*manh[k]) or "{}") + "$" for k in khoa) + "\n"
    import tempfile
    with tempfile.TemporaryDirectory() as tm:
        ra = os.path.join(tm, "ct.docx")
        try:
            subprocess.run([pd, "-f", "markdown", "-o", ra], input=md.encode("utf-8"),
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)
            x = zipfile.ZipFile(ra).read("word/document.xml").decode("utf-8")
        except Exception as e:
            in_ra(f"  (pandoc lỗi: {e} → công thức dùng ảnh SVG)")
            return {}
    doan = re.findall(r"<w:p>(.*?)</w:p>", x, re.S)
    if len(doan) != len(khoa):
        in_ra("  (pandoc trả về sai số đoạn → công thức dùng ảnh SVG)")
        return {}
    kq = {}
    for k, d in zip(khoa, doan):
        m = re.findall(r"<m:oMath>.*?</m:oMath>", d, re.S)
        ngoai = re.sub(r"<m:oMath>.*?</m:oMath>", "", d, flags=re.S)
        if len(m) == 1 and "<w:t" not in ngoai:
            kq[k] = m[0]
    return kq

# ======================================================================= ghi DOCX
NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
      'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" '
      'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"')

class Docx:
    def __init__(self, co_chu=12, le=(1134, 1134, 1134, 1418), chan_trang=None):
        """co_chu: cỡ chữ (pt); le: lề (trên, phải, dưới, trái) twip; chan_trang: XML các đoạn của chân trang."""
        self.p, self.media, self.so = [], {}, 0
        self.co_chu, self.le, self.chan_trang = co_chu, le, chan_trang
        self.ti_le = co_chu / 12.0             # ảnh công thức vẽ ở 12pt → co giãn theo cỡ chữ

    def rel_anh(self, duong):
        if duong not in self.media:
            self.so += 1
            self.media[duong] = (f"rId{100 + self.so}", f"media/a{self.so}{os.path.splitext(duong)[1]}")
        return self.media[duong][0]

    def anh(self, m, ha_xuong=True):
        w, h, d = m["w"], m["h"] + m["d"], m["d"]
        tl0 = getattr(self, "ti_le", 1.0)
        w, h, d = w * tl0, h * tl0, d * tl0
        if w > RONG_TOI_DA:
            tl = RONG_TOI_DA / w; w, h, d = w * tl, h * tl, d * tl
        cx, cy = max(1, int(round(w * PT))), max(1, int(round(h * PT)))
        self.so += 1; sid = self.so
        rid = self.rel_anh(m.get("png") or m["svg"])
        ext = ""
        if m.get("svg") and m.get("png"):
            rs = self.rel_anh(m["svg"])
            ext = ('<a:extLst><a:ext uri="{96DAC541-7B7A-43D3-8B79-37D633B846F1}">'
                   f'<asvg:svgBlip xmlns:asvg="http://schemas.microsoft.com/office/drawing/2016/SVG/main" r:embed="{rs}"/>'
                   '</a:ext></a:extLst>')
        vt = f'<w:position w:val="{-int(round(d * 2))}"/>' if ha_xuong and d > 0.05 else ""
        return (f'<w:r><w:rPr>{vt}</w:rPr><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
                f'<wp:extent cx="{cx}" cy="{cy}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>'
                f'<wp:docPr id="{sid}" name="CongThuc{sid}"/>'
                '<wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
                '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic>'
                f'<pic:nvPicPr><pic:cNvPr id="{sid}" name="CongThuc{sid}"/><pic:cNvPicPr/></pic:nvPicPr>'
                f'<pic:blipFill><a:blip r:embed="{rid}">{ext}</a:blip><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
                f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
                '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
                '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>')

    @staticmethod
    def chu(s, dd=()):
        rp = "".join(x for x, c in (("<w:b/>", "b"), ("<w:i/>", "i"), ('<w:u w:val="single"/>', "u")) if c in dd)
        return f'<w:r>{"<w:rPr>" + rp + "</w:rPr>" if rp else ""}<w:t xml:space="preserve">{xe(s)}</w:t></w:r>'

    def doan(self, runs_xml, can="left", sau=40):
        jc = '<w:jc w:val="center"/>' if can == "center" else ""
        self.p.append(f'<w:p><w:pPr><w:spacing w:before="0" w:after="{sau}"/>{jc}</w:pPr>{runs_xml}</w:p>')

    def bang(self, o, so_cot=5):
        vien = "".join(f'<w:{b} w:val="single" w:sz="4" w:space="0" w:color="808080"/>'
                       for b in ("top", "left", "bottom", "right", "insideH", "insideV"))
        x = (f'<w:tbl><w:tblPr><w:tblW w:w="5000" w:type="pct"/><w:tblBorders>{vien}</w:tblBorders></w:tblPr><w:tblGrid>'
             + "".join('<w:gridCol w:w="1870"/>' for _ in range(so_cot)) + "</w:tblGrid>")
        for i in range(0, len(o), so_cot):
            d = o[i:i + so_cot] + [""] * (so_cot - len(o[i:i + so_cot]))
            x += "<w:tr>" + "".join(f'<w:tc><w:tcPr><w:tcW w:w="1000" w:type="pct"/></w:tcPr><w:p>{self.chu(c) if c else ""}</w:p></w:tc>'
                                    for c in d) + "</w:tr>"
        self.p.append(x + "</w:tbl>")

    def luu(self, duong):
        tren, phai, duoi, trai = self.le
        chan = '<w:footerReference w:type="default" r:id="rIdChan"/>' if self.chan_trang else ""
        body = "".join(self.p) + (f'<w:sectPr>{chan}<w:pgSz w:w="11906" w:h="16838"/>'
                                  f'<w:pgMar w:top="{tren}" w:right="{phai}" w:bottom="{duoi}" w:left="{trai}" w:header="454" w:footer="397" w:gutter="0"/></w:sectPr>')
        doc = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {NS}><w:body>{body}</w:body></w:document>'
        styles = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                  '<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="Times New Roman" w:cs="Times New Roman"/>'
                  f'<w:sz w:val="{int(self.co_chu * 2)}"/><w:szCs w:val="{int(self.co_chu * 2)}"/><w:lang w:val="vi-VN"/></w:rPr></w:rPrDefault>'
                  '<w:pPrDefault><w:pPr><w:spacing w:after="40" w:line="264" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>'
                  '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style></w:styles>')
        rels = ['<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>']
        if self.chan_trang:
            rels.append('<Relationship Id="rIdChan" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>')
        rels += [f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="{ten}"/>'
                 for rid, ten in self.media.values()]
        with zipfile.ZipFile(duong, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("[Content_Types].xml",
                       '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                       '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                       '<Default Extension="xml" ContentType="application/xml"/>'
                       '<Default Extension="png" ContentType="image/png"/><Default Extension="svg" ContentType="image/svg+xml"/>'
                       '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                       '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
                       + ('<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>'
                          if self.chan_trang else "") + '</Types>')
            z.writestr("_rels/.rels",
                       '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                       '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
            z.writestr("word/document.xml", doc)
            z.writestr("word/styles.xml", styles)
            if self.chan_trang:
                z.writestr("word/footer1.xml", f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr {NS}>{self.chan_trang}</w:ftr>')
            z.writestr("word/_rels/document.xml.rels",
                       '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                       + "".join(rels) + "</Relationships>")
            for duong_anh, (rid, ten) in self.media.items():
                z.write(duong_anh, "word/" + ten)

OMML = {}

def chay_xml(doc, doan, anh):
    x = []
    for r in doan.chay:
        if r[0] == "t":
            x.append(Docx.chu(r[1], r[2]))
        elif r[0] == "br":
            x.append("<w:r><w:br/></w:r>")
        elif r[1] in OMML:
            x.append(OMML[r[1]])
        else:
            m = anh.get(r[1]) or {}
            if "w" in m and (m.get("png") or m.get("svg")):
                x.append(doc.anh(m, ha_xuong=doan.can != "center"))
            else:
                x.append(Docx.chu("[công thức lỗi]"))
    return "".join(x)

def ghi_cac_doan(doc, ds, anh, dau_xml=""):
    """Ghi danh sách đoạn; dau_xml gắn vào đầu đoạn đầu tiên (nếu đoạn đầu không phải ảnh căn giữa)."""
    ds = list(ds or [])
    if dau_xml:
        if ds and ds[0].can != "center":
            doc.doan(dau_xml + chay_xml(doc, ds[0], anh)); ds = ds[1:]
        else:
            doc.doan(dau_xml)
    for d in ds:
        doc.doan(chay_xml(doc, d, anh), d.can)

# ======================================================================= ghép đề
PHAN_K12 = [
    ("TN", "Phần I:", "Trắc nghiệm nhiều lựa chọn (Thí sinh trả lời các câu hỏi 1 đến {n}; mỗi câu hỏi chỉ chọn 1 đáp án)."),
    ("DS", "Phần II:", "Trắc nghiệm đúng – sai (Thí sinh trả lời các câu hỏi 1 đến câu hỏi {n}. Trong mỗi câu hỏi, "
                       "thí sinh trả lời đúng hoặc sai cho mỗi ý (mệnh đề))."),
    ("TLN", "Phần III:", "Trả lời ngắn (Thí sinh trả lời các câu hỏi 1 đến câu hỏi {n}. Trong mỗi câu hỏi, "
                         "thí sinh trả lời câu hỏi bằng cách nhập câu trả lời cho câu hỏi)."),
    ("TL", "Phần IV:", "Tự luận (Thí sinh trình bày lời giải các câu hỏi 1 đến câu hỏi {n})."),
]

def dap_so_tln(q, da):
    v = (q["tln"] or da or "").replace("$", "").replace("{,}", ",").replace("\\,", "").replace(" ", "").replace(".", ",")
    return v.replace("−", "-").replace("–", "-")

def xuat(thu_muc_de, in_ra=print, cong_thuc="equation"):
    """cong_thuc = "equation" (Equation của Word) hoặc "svg" (ảnh SVG sắc nét, hạ đúng baseline → thẳng dòng)."""
    tex = os.path.join(thu_muc_de, "tex")
    du_lieu = json.load(open(os.path.join(tex, "_k12_cau.json"), encoding="utf-8"))
    manh, cau_tach = {}, {}
    for ma_de, ds in du_lieu.items():
        for i, c in enumerate(ds):
            p = tach_cau(c)
            q = {"de": chuyen(p["de"], manh), "pa": [chuyen(x, manh) for x in (p["pa"] or [])],
                 "lg": None, "y_giai": None, "tln": p["tln"]}
            if p["y_giai"]:
                dau, ys, cuoi = p["y_giai"]
                q["y_giai"] = (chuyen(dau, manh), [chuyen(y, manh) for y in ys], chuyen(cuoi, manh))
            else:
                q["lg"] = chuyen(p["lg"], manh)
            cau_tach[(ma_de, i)] = q
    in_ra(f"Xuất Word K12Online cho {len(du_lieu)} mã đề…")
    OMML.clear()
    OMML.update(omml_cong_thuc(manh, in_ra, cong_thuc))
    con_lai = {k: v for k, v in manh.items() if k not in OMML}
    so_ct = sum(1 for l, _ in manh.values() if l != "fig")
    in_ra(f"  Công thức → Equation của Word: {len(OMML)}/{so_ct}" if OMML else
          f"  Công thức → ảnh SVG thẳng hàng chữ: {so_ct}")
    anh = bien_dich_manh(con_lai, tex, in_ra) if con_lai else {}
    B, BU = ("b",), ("b", "u")
    for ma_de, ds in du_lieu.items():
        doc = Docx()
        for loai, ten_phan, gioi_thieu in PHAN_K12:
            cac = [(i, c) for i, c in enumerate(ds) if c["loai"] == loai]
            if not cac:
                continue
            doc.doan(Docx.chu(ten_phan, B))
            doc.doan(Docx.chu(gioi_thieu.format(n=len(cac))))
            for so, (i, c) in enumerate(cac, 1):
                q, da = cau_tach[(ma_de, i)], c.get("dap_an") or ""
                ghi_cac_doan(doc, q["de"], anh, Docx.chu(f"Câu {so}:", B) + Docx.chu(" "))
                if loai == "TN":
                    for j, pa in enumerate(q["pa"]):
                        ghi_cac_doan(doc, pa or [Doan()], anh,
                                     Docx.chu(f"{'ABCD'[j]}.", BU if 'ABCD'[j] == da else B) + Docx.chu(" "))
                    doc.doan(Docx.chu("Lời giải:", B))
                    ghi_cac_doan(doc, q["lg"] or ([] if not q["y_giai"] else q["y_giai"][0]), anh)
                elif loai == "DS":
                    for j, pa in enumerate(q["pa"]):
                        dung = j < len(da) and da[j] == "Đ"
                        ghi_cac_doan(doc, pa or [Doan()], anh,
                                     Docx.chu(f"{'abcd'[j]})", BU if dung else B) + Docx.chu(" "))
                        if q["y_giai"]:
                            dau, ys, cuoi = q["y_giai"]
                            doc.doan(Docx.chu("Lời giải:", B))
                            ghi_cac_doan(doc, (dau if j == 0 else []) + (ys[j] if j < len(ys) else [])
                                         + (cuoi if j == 3 else []), anh)
                        elif j == len(q["pa"]) - 1 and q["lg"]:
                            doc.doan(Docx.chu("Lời giải:", B))
                            ghi_cac_doan(doc, q["lg"], anh)
                else:
                    if loai == "TLN":
                        doc.doan(Docx.chu("Đáp án:", B))
                        doc.doan(Docx.chu(dap_so_tln(q, da)))
                    doc.doan(Docx.chu("Lời giải:", B))
                    ghi_cac_doan(doc, q["lg"] or [], anh)
        ra = os.path.join(thu_muc_de, f"Word_K12Online_{ma_de}.docx")
        doc.luu(ra)
        in_ra(f"  ✓ {os.path.basename(ra)}")

if __name__ == "__main__":
    # python3 scripts/k12word.py "<thư mục đề>" [svg|equation]
    xuat(sys.argv[1], cong_thuc=(sys.argv[2] if len(sys.argv) > 2 else "equation"))
