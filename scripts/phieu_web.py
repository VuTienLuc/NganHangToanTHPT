# -*- coding: utf-8 -*-
"""
PHIẾU HỌC TẬP → TRANG HTML (một file, mở trên web/điện thoại/máy chiếu)
  I. Kiến thức trọng tâm  ·  bài tập trắc nghiệm (chọn → chấm ngay), Đúng/Sai, trả lời ngắn
  bài tập tự luận (ví dụ mẫu có lời giải, tự luyện: bấm xem đáp số / lời giải)
Dữ liệu: <thư mục phiếu>/tex/phieu_web.json do phieu_bai_hoc.py ghi khi tạo phiếu.
Dùng:  python3 phieu_web.py "de-da-ra/Phiếu Bài Học - …"
"""
import html, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nh_core import GOC, doc_nhom  # noqa: E402

E = lambda s: html.escape(str(s or ""), quote=True)


# ---------------------------------------------------------------- LaTeX (chữ) → HTML; công thức để MathJax hiển thị
MOI_TRUONG_TOAN = r"(?:align|alignat|gather|equation|eqnarray|multline|flalign)\*?"
TOAN = re.compile(r"\$\$.*?\$\$|\\\[.*?\\\]|\\\(.*?\\\)|\$(?:\\.|[^$\\])+\$|\\begin\{(" + MOI_TRUONG_TOAN + r")\}.*?\\end\{\1\}", re.S)
HINH = re.compile(r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}|<svg\b[^>]*>.*?</svg>", re.S | re.I)
BO_LENH = ("noindent", "hfill", "centering", "par", "smallskip", "medskip", "bigskip", "newline", "allowdisplaybreaks",
           "footnotesize", "small", "scriptsize", "normalsize", "large", "Large", "LARGE", "huge", "tiny", "bfseries",
           "itshape", "mdseries", "upshape", "normalfont", "selectfont", "break", "displaystyle", "nopagebreak",
           "pagebreak", "newpage", "clearpage", "True", "dotfill", "indent", "raggedright", "raggedleft", "protect",
           "relax", "linebreak", "vfill", "hrule", "hline", "nhoHinh", "tieudehinh", "maketitle")
GIU_CHU = {"textbf": "b", "textit": "i", "emph": "i", "underline": "u", "textsl": "i", "textsc": "span",
           "text": "span", "textrm": "span", "mbox": "span", "fbox": "span class=\"khung\"", "framebox": "span class=\"khung\"",
           "textsuperscript": "sup", "textsubscript": "sub", "texttt": "code", "textup": "span", "uline": "u"}


def _cat_nhom(s, i):
    while i < len(s) and s[i] in " \t":
        i += 1
    if i < len(s) and s[i] == "{":
        return doc_nhom(s, i)
    return None, i


def _bang_html(t):
    """tabular → <table> (khi chưa thành SVG)."""
    m = re.match(r"\\begin\{tabular\}\s*(\{(?:[^{}]|\{[^{}]*\})*\})?(.*)\\end\{tabular\}\s*$", t, re.S)
    than = m.group(2) if m else t
    dong = [d for d in re.split(r"\\\\(?:\[[^\]]*\])?", than)]
    ra = []
    for d in dong:
        d = re.sub(r"\\(?:hline|cline\{[^}]*\})", "", d).strip()
        if not d:
            continue
        o = []
        for c in re.split(r"(?<!\\)&", d):
            mc = re.match(r"\s*\\multicolumn\{(\d+)\}\{[^}]*\}\{(.*)\}\s*$", c, re.S)
            if mc:
                o.append(f'<td colspan="{mc.group(1)}">{chu(mc.group(2))}</td>')
            else:
                o.append(f"<td>{chu(c.strip())}</td>")
        ra.append("<tr>" + "".join(o) + "</tr>")
    return '<div class="bang"><table>' + "".join(ra) + "</table></div>"


def _tach_bang(s, giu):
    out, i = "", 0
    while True:
        a = s.find("\\begin{tabular}", i)
        if a < 0:
            return out + s[i:]
        muc, j = 1, a + 15
        while muc and j < len(s):
            x, y = s.find("\\begin{tabular}", j), s.find("\\end{tabular}", j)
            if y < 0:
                break
            if 0 <= x < y:
                muc += 1; j = x + 15
            else:
                muc -= 1; j = y + 13
        if muc:
            return out + s[i:]
        giu.append(_bang_html(s[a:j]))
        out += s[i:a] + f"\x00G{len(giu) - 1}\x00"
        i = j


def bo_immini(s):
    out, p = "", 0
    for m in re.finditer(r"\\immini\s*(?:\[[^\]]*\])?", s):
        if m.start() < p:
            continue
        a, i = _cat_nhom(s, m.end())
        if a is None:
            continue
        b, j = _cat_nhom(s, i)
        if b is None:
            continue
        out += s[p:m.start()] + b + "\n" + bo_immini(a)
        p = j
    return out + s[p:]


def chu(s, hinh=None, ten_truong="stem"):
    """Đoạn LaTeX → HTML. hinh: {"<truong>:<i>": svg} cho các tikzpicture theo thứ tự."""
    s = str(s or "")
    s = re.sub(r"(?<!\\)%[^\n]*", "", s)
    s = bo_immini(s)
    giu = []
    dem = [0]

    def gh(m):
        k = f"{ten_truong}:{dem[0]}"; dem[0] += 1
        svg = (hinh or {}).get(k) or (m.group(0) if m.group(0).lstrip().startswith("<svg") else "")
        giu.append(f'<figure class="hinh">{svg}</figure>' if svg else '<div class="thieu-hinh">[Hình minh hoạ — xem bản PDF]</div>')
        return f"\x00G{len(giu) - 1}\x00"
    s = HINH.sub(gh, s)
    s = _tach_bang(s, giu)

    def gt(m):
        x = m.group(0).replace(r"\allowdisplaybreaks", "")
        giu.append(E(x)); return f"\x00G{len(giu) - 1}\x00"
    s = TOAN.sub(gt, s)
    for a, b in ((r"\lq\lq", "“"), (r"\rq\rq", "”"), ("``", "“"), ("''", "”"), (r"\lq", "‘"), (r"\rq", "’"),
                 ("---", "—"), ("--", "–"), (r"\%", "%"), (r"\&", "&"), (r"\_", "_"), (r"\#", "#"), (r"\{", "{"), (r"\}", "}")):
        s = s.replace(a, b)
    s = E(s)
    s = s.replace("~", "\u00a0")
    # danh sách
    s = re.sub(r"\\begin\{(itemize|enumerate|itemchoice)\}(\[[^\]]*\])?",
               lambda m: "\x01" + {"itemize": "<ul>", "itemchoice": '<ul class="pa-list">'}.get(m.group(1), _ol(m.group(2))) + "\x01", s)
    s = re.sub(r"\\end\{(itemize|enumerate|itemchoice)\}", lambda m: "\x01</li>" + ("</ol>" if m.group(1) == "enumerate" else "</ul>") + "\x01", s)
    s = re.sub(r"\\item(?:ch)?\b(?:\[([^\]]*)\])?\s*",
               lambda m: "\x01</li><li" + (f' data-nhan="{m.group(1)}" class="co-nhan"' if m.group(1) else "") + ">\x01", s)
    s = re.sub(r"(<(?:ul|ol)[^>]*>)\x01\s*\x01</li>", lambda m: m.group(1) + "\x01\x01", s)
    # khối
    s = re.sub(r"\\begin\{center\}", "\x01<div class=\"giua\">\x01", s)
    s = re.sub(r"\\end\{center\}", "\x01</div>\x01", s)
    s = re.sub(r"\\begin\{(?:tcolorbox|mdframed|framed)\}(?:\[[^\]]*\])?", "\x01<div class=\"hop\">\x01", s)
    s = re.sub(r"\\end\{(?:tcolorbox|mdframed|framed)\}", "\x01</div>\x01", s)
    s = re.sub(r"\\begin\{minipage\}(?:\[[^\]]*\])?\{[^}]*\}", "", s)
    s = re.sub(r"\\(?:begin|end)\{[a-zA-Z*]+\}(?:\[[^\]]*\])?", "", s)
    s = re.sub(r"\\(?:sub)*section\*?\{([^{}]*)\}", "\x01<h4>\\1</h4>\x01", s)
    # lệnh có đối số
    for _ in range(6):
        s2 = re.sub(r"\\(textcolor|colorbox)\{[^{}]*\}\{((?:[^{}]|\{[^{}]*\})*)\}",
                    lambda m: f"<mark>{m.group(2)}</mark>" if m.group(1) == "colorbox" else m.group(2), s)
        s2 = re.sub(r"\\(" + "|".join(GIU_CHU) + r")\{((?:[^{}]|\{[^{}]*\})*)\}",
                    lambda m: f"<{GIU_CHU[m.group(1)]}>{m.group(2)}</{GIU_CHU[m.group(1)].split()[0]}>", s2)
        s2 = re.sub(r"\{\\(?:bf|bfseries)\s+((?:[^{}]|\{[^{}]*\})*)\}", r"<b>\1</b>", s2)
        s2 = re.sub(r"\{\\(?:it|itshape|em)\s+((?:[^{}]|\{[^{}]*\})*)\}", r"<i>\1</i>", s2)
        s2 = re.sub(r"\\href\{([^{}]*)\}\{([^{}]*)\}", r'<a href="\1" target="_blank" rel="noopener">\2</a>', s2)
        if s2 == s:
            break
        s = s2
    s = re.sub(r"\\(?:vspace|hspace|color|setlength|addtolength|rule|label|ref|phantom|vphantom)\*?(?:\[[^\]]*\])?(?:\{[^{}]*\})*", "", s)
    s = re.sub(r"\\(?:quad|qquad|enspace|,|;|:|!| )", " ", s)
    s = re.sub(r"\\\\(?:\[[^\]]*\])?", "<br>", s)
    s = re.sub(r"\\(" + "|".join(BO_LENH) + r")(?![A-Za-z])\s*", "", s)
    s = re.sub(r"\\[A-Za-z]+\*?(?:\[[^\]]*\])?", "", s)   # lệnh lạ: bỏ tên lệnh, giữ chữ
    s = s.replace("{", "").replace("}", "")
    # đoạn văn
    s = _doan(s)
    s = re.sub(r"<p>\s*</p>", "", s)
    s = re.sub(r"<li>\s*</li>", "", s)
    s = re.sub(r"\x00G(\d+)\x00", lambda m: giu[int(m.group(1))], s)
    s = re.sub(r"\x00G(\d+)\x00", lambda m: giu[int(m.group(1))], s)
    return s.strip()


def _doan(s):
    """Chia đoạn văn: chữ ngoài danh sách bọc <p>, mỗi dòng trống là một đoạn; thẻ khối giữ nguyên."""
    ra, sau = [], 0
    for i, m in enumerate(s.split("\x01")):
        if i % 2:                      # thẻ khối
            for t in re.findall(r"<(/?)(ul|ol)\b", m):
                sau += -1 if t[0] else 1
            ra.append(m); continue
        if sau > 0:
            ra.append(m); continue
        ra += [f"<p>{p.strip()}</p>" for p in re.split(r"\n\s*\n", m) if p.strip()]
    return "".join(ra)


def _ol(opt):
    o = (opt or "").strip("[]")
    t = "a" if "a" in o else "A" if "A" in o else "i" if "i" in o else "1"
    return f'<ol type="{t}">'


# ---------------------------------------------------------------- dữ liệu câu
def _cau_tn(ma, kho):
    import trinh_chieu
    c = kho.get(ma)
    return trinh_chieu.cau_json(c) if c else None


def lap(thu_muc, in_ra=print, ve=True):
    """→ (thông tin phiếu, danh sách khối) — khối: {"tieu", "cau": [q…]} với q đã có figures SVG nếu vẽ được."""
    p = os.path.join(thu_muc, "tex", "phieu_web.json")
    if not os.path.exists(p):
        raise RuntimeError("Phiếu này tạo từ bản cũ, chưa có dữ liệu web — thầy tạo lại phiếu rồi đăng.")
    P = json.load(open(p, encoding="utf-8"))
    kt = (P.get("kien_thuc") or "").strip()
    if not kt and P.get("bai"):
        try:
            import kho_kien_thuc
            kt = kho_kien_thuc.doc_pham_vi(P["bai"]).strip()
        except Exception:
            kt = ""
    tat_ca, khoi = [], []
    kq_kt = {"stem": kt, "solution": "", "options": [], "type": "kt"}
    tat_ca.append(kq_kt)
    if P["kieu"] == "tu_luan":
        for d in P.get("dang") or []:
            v = d["vi_du"]
            vd = {"type": "essay", "vai": "vi_du", "stem": v["de"], "solution": v.get("lg") or "", "answer": v.get("dap") or "", "options": []}
            tl = [{"type": "essay", "vai": c.get("vai") or "tuong_tu", "stem": c["de"], "solution": c.get("lg") or "",
                   "answer": c.get("dap") or "", "options": []} for c in d.get("tu_luyen") or []]
            khoi.append({"tieu": d["ten"], "vi_du": vd, "cau": tl}); tat_ca += [vd] + tl
    else:
        import trinh_chieu
        kho = trinh_chieu.kho()
        for ph in P.get("phan") or []:
            nhom = []
            for n in ph["nhom"]:
                ds = []
                for x in n["cau"]:
                    q = _cau_tn(x["ma"], kho)
                    if q:
                        q["dang"] = x.get("dang") or ""; q["nhan"] = x.get("nhan") or ""
                        ds.append(q)
                if ds:
                    nhom.append({"tieu": n["tieu"], "cau": ds}); tat_ca += ds
            if nhom:
                khoi.append({"tieu": ph["tieu"], "nhom": nhom})
    if ve:
        try:
            import trinh_chieu
            for q in tat_ca:
                q.setdefault("options", [])
                q.setdefault("solution", "")
            n, ok = trinh_chieu.ve_hinh(tat_ca, in_ra)
            if n:
                in_ra(f"  Hình/bảng: {ok}/{n} đã thành SVG")
        except Exception as e:
            in_ra(f"  Chưa vẽ được hình ({e}) — hình hiện chữ 'xem bản PDF'.")
    P["_kt"] = kq_kt
    return P, khoi


# ---------------------------------------------------------------- trang HTML
def _q_html(q, so, id_):
    f = q.get("figures") or {}
    h = lambda t, k: chu(t, f, k)
    dau = f'<div class="cau" id="{id_}" data-loai="{q["type"]}"'
    nhan = f'<span class="nhan-nc">{E(q.get("nhan"))}</span>' if q.get("nhan") else ""
    lg = h(q.get("solution"), "solution")
    if q["type"] == "mcq":
        pa = "".join(f'<button class="pa" data-i="{i}"><b>{"ABCD"[i]}.</b> <span>{h(o, f"option{i}")}</span></button>'
                     for i, o in enumerate(q["options"]))
        return (dau + f' data-da="{q["answer"]}"><div class="de"><span class="so">Câu {so}.</span>{nhan} {h(q["stem"], "stem")}</div>'
                f'<div class="ds-pa">{pa}</div><div class="kq" role="status"></div>' + _lg(lg, "ABCD"[q["answer"]]) + "</div>")
    if q["type"] == "tf":
        y = "".join(f'<div class="y" data-i="{i}"><span class="nd"><b>{"abcd"[i]})</b> {h(o, f"option{i}")}</span>'
                    f'<span class="ds"><button data-v="1">Đ</button><button data-v="0">S</button></span></div>'
                    for i, o in enumerate(q["options"]))
        da = "".join("Đ" if x else "S" for x in q["answer"])
        return (dau + f' data-da="{da}"><div class="de"><span class="so">Câu {so}.</span>{nhan} {h(q["stem"], "stem")}</div>'
                f'<div class="ds-y">{y}</div><div class="hang"><button class="nut kiem">Kiểm tra</button><span class="kq" role="status"></span></div>'
                + _lg(lg, " ".join(f"{'abcd'[i]}) {c}" for i, c in enumerate(da))) + "</div>")
    if q["type"] == "short":
        return (dau + f' data-da="{E(q["answer"])}"><div class="de"><span class="so">Câu {so}.</span>{nhan} {h(q["stem"], "stem")}</div>'
                f'<div class="hang"><input class="tl" inputmode="decimal" placeholder="Nhập đáp số" aria-label="Đáp số câu {so}">'
                f'<button class="nut kiem">Kiểm tra</button><span class="kq" role="status"></span></div>' + _lg(lg, q["answer"]) + "</div>")
    # tự luận
    vai = {"van_dung": "Vận dụng", "nang_cao": "Nâng cao"}.get(q.get("vai"), "")
    tieu = "Ví dụ" if q.get("vai") == "vi_du" else "Bài"
    dap = f'<p class="dap"><b>Đáp số:</b> {chu(q["answer"])}</p>' if q.get("answer") else ""
    if q.get("vai") == "vi_du":
        return (f'<div class="cau vi-du" id="{id_}"><div class="de"><span class="so">{tieu} {so}.</span> {h(q["stem"], "stem")}</div>'
                f'<div class="loi-giai mo"><div class="lg-tieu">Lời giải</div>{lg}{dap}</div></div>')
    return (f'<div class="cau" id="{id_}" data-loai="essay"><div class="de"><span class="so">{tieu} {so}.</span>'
            + (f'<span class="nhan-nc">{vai}</span>' if vai else "") + f' {h(q["stem"], "stem")}</div>'
            + ('<details class="goi-y"><summary>Xem đáp số</summary>' + dap + "</details>" if dap else "")
            + (f'<details class="lg"><summary>Xem lời giải</summary><div class="loi-giai">{lg}</div></details>' if lg else "") + "</div>")


def _lg(lg, dap):
    return (f'<details class="lg"><summary>Đáp án &amp; lời giải</summary><div class="loi-giai"><p class="dap"><b>Đáp án:</b> {chu(str(dap))}</p>'
            f'{lg}</div></details>')


def tao_html(thu_muc, in_ra=print, ve=True):
    P, khoi = lap(thu_muc, in_ra, ve)
    muc, than, so = [], [], 0
    if P["_kt"]["stem"]:
        muc.append(("kt", "I. Kiến thức trọng tâm", 0))
        than.append(f'<section id="kt" class="phan"><h2>I. Kiến thức trọng tâm</h2><div class="kien-thuc">{chu(P["_kt"]["stem"], P["_kt"].get("figures"))}</div></section>')
    co_kt = bool(P["_kt"]["stem"])
    if P["kieu"] == "tu_luan":
        tieu = ("II" if co_kt else "I") + ". Các dạng toán – ví dụ mẫu và tự luyện"
        k = [f'<section id="dang" class="phan"><h2>{tieu}</h2>']
        muc.append(("dang", tieu, 0))
        so_vd = 0
        for j, d in enumerate(khoi, 1):
            so_vd += 1
            k.append(f'<div class="dang" id="d{j}"><h3>{E(d["tieu"])}</h3>')
            muc.append((f"d{j}", d["tieu"], 1))
            k.append(_q_html(d["vi_du"], so_vd, f"vd{j}"))
            if d["cau"]:
                k.append('<div class="tu-luyen-tieu">Tự luyện</div>')
            for q in d["cau"]:
                so += 1
                k.append(_q_html(q, so, f"c{so}"))
            k.append("</div>")
        than.append("".join(k) + "</section>")
    else:
        for i, ph in enumerate(khoi):
            pid = f"p{i}"
            muc.append((pid, ph["tieu"], 0))
            k = [f'<section id="{pid}" class="phan"><h2>{E(ph["tieu"])}</h2>']
            for j, n in enumerate(ph["nhom"], 1):
                k.append(f'<h3 id="{pid}n{j}">{j}. {E(n["tieu"])} <small>({len(n["cau"])} câu)</small></h3>')
                muc.append((f"{pid}n{j}", f'{j}. {n["tieu"]}', 1))
                dang_cu = None
                for q in n["cau"]:
                    if q.get("dang") and q["dang"] != dang_cu:
                        dang_cu = q["dang"]; k.append(f'<div class="dang-nhan">{E(dang_cu)}</div>')
                    so += 1
                    k.append(_q_html(q, so, f"c{so}"))
            than.append("".join(k) + "</section>")
    ten = P.get("ten") or "Phiếu học tập"
    nhan = (P.get("nhan") or "PHIẾU HỌC TẬP") + (" – TỰ LUẬN" if P["kieu"] == "tu_luan" else "")
    nav = "".join(f'<a href="#{a}" class="m{c}">{E(b)}</a>' for a, b, c in muc)
    phu = " · ".join(x for x in (f"Toán {P.get('lop')}" if P.get("lop") else "", P.get("chuong") or "",
                                 f"{P.get('thoi_luong')} phút" if P.get("thoi_luong") else "") if x)
    trang = (TRANG.replace("__TIEU__", E(ten)).replace("__NHAN__", E(nhan)).replace("__PHU__", E(phu))
             .replace("__GV__", E(P.get("giao_vien") or "")).replace("__NAV__", nav).replace("__THAN__", "".join(than))
             .replace("__TONG__", str(so)))
    return trang, P


def ghi(thu_muc, in_ra=print, ve=True):
    goc = os.path.join(GOC, thu_muc) if not os.path.isabs(thu_muc) else thu_muc
    t, P = tao_html(goc, in_ra, ve)
    p = os.path.join(goc, "PhieuHocTap_Web.html")
    open(p, "w", encoding="utf-8").write(t)
    in_ra(f"  ✓ {os.path.relpath(p, GOC)}")
    return p, P


TRANG = r"""<!DOCTYPE html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>__TIEU__</title>
<script>window.MathJax={tex:{inlineMath:[['$','$'],['\\(','\\)']],displayMath:[['$$','$$'],['\\[','\\]']],processEnvironments:true,
macros:{heva:['\\left\\{\\begin{aligned}#1\\end{aligned}\\right.',1],hoac:['\\left[\\begin{aligned}#1\\end{aligned}\\right.',1],
dfrac:['\\frac{#1}{#2}',2],R:'\\mathbb{R}',N:'\\mathbb{N}',Z:'\\mathbb{Z}',Q:'\\mathbb{Q}'}},options:{enableMenu:false},chtml:{scale:1.02}};</script>
<script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml-full.js"></script>
<style>
:root{--bg:#f4f6fb;--mat:#fff;--mat2:#f8fafc;--chu:#0f172a;--nhat:#64748b;--vien:#e2e8f0;--chinh:#1e40af;--chinh-nhat:#dbeafe;--dung:#15803d;--dung-nhat:#dcfce7;
--sai:#b91c1c;--sai-nhat:#fee2e2;--vang:#b45309;--vang-nhat:#fef3c7;--bo:14px;--co:17px}
@media (prefers-color-scheme:dark){:root{--bg:#0b1120;--mat:#111827;--mat2:#0f172a;--chu:#e5e7eb;--nhat:#94a3b8;--vien:#1f2937;--chinh:#93c5fd;--chinh-nhat:#1e3a8a66;
--dung:#86efac;--dung-nhat:#14532d66;--sai:#fca5a5;--sai-nhat:#7f1d1d66;--vang:#fcd34d;--vang-nhat:#78350f66}figure.hinh svg{background:#fff;border-radius:8px}}
body.toi{--bg:#0b1120;--mat:#111827;--mat2:#0f172a;--chu:#e5e7eb;--nhat:#94a3b8;--vien:#1f2937;--chinh:#93c5fd;--chinh-nhat:#1e3a8a66}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--chu);font:var(--co)/1.65 "Be Vietnam Pro",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
header.dau{background:linear-gradient(135deg,#1e3a8a,#2563eb);color:#fff;padding:22px 16px 18px}
header.dau .vo{max-width:1180px;margin:0 auto}header.dau .nhan{font-size:12.5px;font-weight:800;letter-spacing:.08em;opacity:.85}
header.dau h1{margin:4px 0 2px;font-size:clamp(22px,3.4vw,30px);line-height:1.25}header.dau .phu{opacity:.9;font-size:14.5px}
.thanh{position:sticky;top:0;z-index:20;background:var(--mat);border-bottom:1px solid var(--vien)}
.thanh .vo{max-width:1180px;margin:0 auto;display:flex;gap:8px;align-items:center;padding:8px 16px;flex-wrap:wrap}
.tien{flex:1;min-width:160px;font-size:13.5px;color:var(--nhat)}.tien .vach{height:6px;background:var(--vien);border-radius:9px;margin-top:3px;overflow:hidden}
.tien .vach i{display:block;height:100%;width:0;background:var(--dung);transition:width .25s ease-out}
.nut{font:inherit;font-size:14px;font-weight:600;min-height:40px;padding:7px 13px;border-radius:10px;border:1px solid var(--vien);background:var(--mat);color:var(--chu);cursor:pointer}
.nut:hover{border-color:var(--chinh)}.nut:focus-visible,.pa:focus-visible,.ds button:focus-visible,summary:focus-visible{outline:3px solid #60a5fa;outline-offset:2px}
.luoi{max-width:1180px;margin:0 auto;padding:18px 16px 60px;display:grid;grid-template-columns:minmax(0,1fr);gap:20px}
@media (min-width:1024px){.luoi{grid-template-columns:250px minmax(0,1fr)}}
nav.muc{display:none}@media (min-width:1024px){nav.muc{display:block;position:sticky;top:70px;align-self:start;max-height:calc(100vh - 90px);overflow:auto;font-size:14px}}
nav.muc a{display:block;padding:6px 10px;border-radius:8px;color:var(--chu);text-decoration:none;line-height:1.35}nav.muc a:hover{background:var(--chinh-nhat)}
nav.muc a.m0{font-weight:700;margin-top:8px}nav.muc a.m1{padding-left:20px;color:var(--nhat);font-size:13.5px}nav.muc a.dang-o{background:var(--chinh-nhat);color:var(--chinh)}
.phan{background:var(--mat);border:1px solid var(--vien);border-radius:var(--bo);padding:18px clamp(14px,2.4vw,26px);margin-bottom:20px;scroll-margin-top:70px}
.phan h2{margin:0 0 12px;color:var(--chinh);font-size:1.25em}.phan h3{margin:22px 0 10px;font-size:1.06em;scroll-margin-top:70px}.phan h3 small{color:var(--nhat);font-weight:500}
.kien-thuc{line-height:1.75}.kien-thuc ul,.kien-thuc ol{padding-left:1.4em}.kien-thuc li{margin:4px 0}.kien-thuc mjx-container[display=true]{margin:.5em 0}
.dang{border-top:1px dashed var(--vien);padding-top:6px;scroll-margin-top:70px}.dang:first-of-type{border-top:0}
.dang-nhan{display:inline-block;margin:14px 0 6px;font-size:13px;font-weight:700;color:#0f766e;background:#ccfbf1;border-radius:7px;padding:2px 9px}
.cau{border:1px solid var(--vien);border-radius:12px;padding:12px 14px;margin:10px 0;background:var(--mat2);scroll-margin-top:70px}
.cau.vi-du{background:var(--vang-nhat);border-color:transparent}.cau .so{font-weight:800;color:var(--chinh);margin-right:4px}
.nhan-nc{font-size:12px;font-weight:800;color:#fff;background:#b91c1c;border-radius:6px;padding:1px 7px;margin:0 4px;vertical-align:2px}
.de p{margin:.35em 0}.de>p:first-of-type{display:inline}.ds-pa{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,230px),1fr));gap:8px;margin-top:10px}
.pa{font:inherit;text-align:left;display:flex;gap:6px;align-items:baseline;padding:9px 12px;border:1.5px solid var(--vien);border-radius:10px;background:var(--mat);color:var(--chu);cursor:pointer;min-height:44px}
.pa:hover{border-color:var(--chinh)}.pa p{display:inline;margin:0}.pa.dung{border-color:var(--dung);background:var(--dung-nhat)}.pa.sai{border-color:var(--sai);background:var(--sai-nhat)}
.pa[disabled]{cursor:default}.y{display:flex;gap:10px;align-items:center;justify-content:space-between;padding:7px 0;border-bottom:1px solid var(--vien)}
.y:last-child{border-bottom:0}.y .nd p{display:inline;margin:0}.ds{display:flex;gap:6px;flex-shrink:0}
.ds button{font:inherit;font-weight:800;width:44px;height:40px;border-radius:9px;border:1.5px solid var(--vien);background:var(--mat);color:var(--chu);cursor:pointer}
.ds button[aria-pressed=true]{background:var(--chinh);border-color:var(--chinh);color:#fff}.y.dung .ds button[aria-pressed=true]{background:var(--dung);border-color:var(--dung)}
.y.sai .ds button[aria-pressed=true]{background:var(--sai);border-color:var(--sai)}
.hang{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:10px}
input.tl{font:inherit;padding:8px 11px;border:1.5px solid var(--vien);border-radius:10px;width:170px;background:var(--mat);color:var(--chu);min-height:42px}
.kq{font-weight:700;font-size:14.5px}.kq.dung{color:var(--dung)}.kq.sai{color:var(--sai)}
details.lg,details.goi-y{margin-top:10px}details>summary{cursor:pointer;color:var(--chinh);font-weight:600;font-size:14.5px;list-style:none;display:inline-flex;align-items:center;gap:6px;min-height:36px}
details>summary::-webkit-details-marker{display:none}details>summary::before{content:"▸";transition:transform .15s}details[open]>summary::before{transform:rotate(90deg)}
.loi-giai{border-left:3px solid var(--chinh);background:var(--mat);border-radius:0 10px 10px 0;padding:8px 12px;margin-top:6px}
.loi-giai.mo{border-left-color:var(--vang)}.lg-tieu{font-weight:800;color:var(--vang);font-size:14px}.dap{margin:.2em 0}
.tu-luyen-tieu{margin:14px 0 2px;font-weight:800;color:var(--nhat);text-transform:uppercase;font-size:12.5px;letter-spacing:.06em}
figure.hinh{margin:10px auto;text-align:center;max-width:100%;overflow-x:auto}figure.hinh svg{max-width:100%;height:auto}
.thieu-hinh{color:var(--nhat);font-style:italic;font-size:14px;margin:6px 0}.giua{text-align:center}
.bang{overflow-x:auto;margin:8px 0}.bang table{border-collapse:collapse;margin:0 auto}.bang td{border:1px solid var(--vien);padding:5px 10px;text-align:center}
.hop{border:1px solid var(--vien);border-radius:10px;padding:8px 12px;margin:8px 0}ol.pa-list,ul.pa-list{list-style:none;padding-left:0}
.khung{border:1px solid currentColor;padding:0 4px;border-radius:4px}mark{background:#fde68a;color:inherit;border-radius:3px;padding:0 2px}
footer.cuoi{text-align:center;color:var(--nhat);font-size:13px;padding:10px 16px 30px}
.an-lg details.lg,.an-lg details.goi-y{display:none}
@media print{.thanh,nav.muc,details.lg,details.goi-y,.hang .nut,.kq{display:none!important}body{background:#fff;--co:13pt}.phan{border:0;padding:0}
.luoi{display:block;padding:0}.cau{break-inside:avoid;background:#fff}header.dau{background:none;color:#000;padding:0 0 10px}}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style></head><body>
<header class="dau"><div class="vo"><div class="nhan">__NHAN__</div><h1>__TIEU__</h1><div class="phu">__PHU__</div></div></header>
<div class="thanh"><div class="vo"><div class="tien"><span id="tien-chu">Đã làm 0/__TONG__ câu</span><div class="vach"><i id="tien-vach"></i></div></div>
<button class="nut" id="nut-lg" title="Mở / đóng mọi lời giải">Hiện lời giải</button><button class="nut" id="nut-lam-lai">Làm lại</button>
<button class="nut" id="nho" aria-label="Chữ nhỏ hơn">A−</button><button class="nut" id="to" aria-label="Chữ to hơn">A+</button>
<button class="nut" id="nut-in" title="In phiếu (không kèm lời giải)">In</button></div></div>
<div class="luoi"><nav class="muc" aria-label="Mục lục phiếu">__NAV__</nav><main>__THAN__</main></div>
<footer class="cuoi">__GV__</footer>
<script>
(()=>{const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];const KEY='phieu:'+location.pathname;
let L={};try{L=JSON.parse(localStorage.getItem(KEY)||'{}')}catch(_){}const luu=()=>{try{localStorage.setItem(KEY,JSON.stringify(L))}catch(_){}};
const cham=$$('.cau[data-loai]').filter(c=>c.dataset.loai!=='essay'),tong=cham.length;
function tien(){const da=cham.filter(c=>L[c.id]).length,dung=cham.filter(c=>L[c.id]&&L[c.id].ok).length;
 $('#tien-chu').textContent=tong?`Đã làm ${da}/${tong} câu · đúng ${dung}`:'Phiếu tự luận: bấm “Xem đáp số / lời giải” sau khi tự làm';$('#tien-vach').style.width=(tong?da/tong*100:0)+'%'}
const so=s=>String(s).trim().replace(/\s|\$/g,'').replace(',','.').replace(/^\+/,'');
function apMcq(c,i){const da=+c.dataset.da;c.querySelectorAll('.pa').forEach((b,j)=>{b.disabled=true;b.classList.toggle('dung',j===da);b.classList.toggle('sai',j===i&&i!==da)});
 const k=c.querySelector('.kq');k.textContent=i===da?'✓ Chính xác!':'✗ Chưa đúng — đáp án '+'ABCD'[da];k.className='kq '+(i===da?'dung':'sai');return i===da}
function apTf(c,ch){const da=c.dataset.da;let d=0;c.querySelectorAll('.y').forEach((y,i)=>{const v=ch[i];y.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.v===v)));
  if(v!=null){const ok=(v==='1')===(da[i]==='Đ');y.classList.toggle('dung',ok);y.classList.toggle('sai',!ok);d+=ok}});
 const k=c.querySelector('.kq');k.textContent=`Đúng ${d}/4 ý`+(d<4?' — đáp án '+[...da].map((x,i)=>'abcd'[i]+') '+x).join(' '):'');k.className='kq '+(d===4?'dung':'sai');return d===4}
function apShort(c,v){const ds=c.dataset.da.split(/\s*[;|]\s*/).map(so),ok=ds.includes(so(v));c.querySelector('input').value=v;
 const k=c.querySelector('.kq');k.textContent=ok?'✓ Chính xác!':'✗ Chưa đúng — đáp số '+c.dataset.da;k.className='kq '+(ok?'dung':'sai');return ok}
for(const c of cham){const t=c.dataset.loai,s=L[c.id];
 if(t==='mcq'){c.querySelectorAll('.pa').forEach((b,i)=>b.onclick=()=>{L[c.id]={v:i,ok:apMcq(c,i)};luu();tien()});if(s)apMcq(c,s.v)}
 if(t==='tf'){const ch=s?s.v:[null,null,null,null];c.querySelectorAll('.y').forEach((y,i)=>y.querySelectorAll('button').forEach(b=>b.onclick=()=>{ch[i]=b.dataset.v;
   y.querySelectorAll('button').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));y.classList.remove('dung','sai')}));
  c.querySelector('.kiem').onclick=()=>{if(ch.some(x=>x==null)){c.querySelector('.kq').textContent='Chọn Đ hoặc S cho đủ 4 ý.';c.querySelector('.kq').className='kq';return}
   L[c.id]={v:ch.slice(),ok:apTf(c,ch)};luu();tien()};if(s)apTf(c,s.v)}
 if(t==='short'){const i=c.querySelector('input'),go=()=>{if(!i.value.trim())return;L[c.id]={v:i.value,ok:apShort(c,i.value)};luu();tien()};
  c.querySelector('.kiem').onclick=go;i.onkeydown=e=>{if(e.key==='Enter')go()};if(s)apShort(c,s.v)}}
tien();
let mo=false;$('#nut-lg').onclick=()=>{mo=!mo;$$('details.lg,details.goi-y').forEach(d=>d.open=mo);$('#nut-lg').textContent=mo?'Ẩn lời giải':'Hiện lời giải'};
$('#nut-lam-lai').onclick=()=>{if(confirm('Xoá các câu đã làm trên phiếu này?')){L={};luu();location.reload()}};
let co=+(localStorage.getItem('phieu:co')||17);const datCo=()=>{document.documentElement.style.setProperty('--co',co+'px');try{localStorage.setItem('phieu:co',co)}catch(_){}};datCo();
$('#nho').onclick=()=>{co=Math.max(14,co-1);datCo()};$('#to').onclick=()=>{co=Math.min(30,co+2);datCo()};$('#nut-in').onclick=()=>print();
const ls=$$('nav.muc a'),io=new IntersectionObserver(es=>{for(const e of es)if(e.isIntersecting){ls.forEach(a=>a.classList.toggle('dang-o',a.getAttribute('href')==='#'+e.target.id))}},{rootMargin:'-80px 0px -70% 0px'});
ls.forEach(a=>{const t=document.getElementById(a.getAttribute('href').slice(1));if(t)io.observe(t)});
})();
</script></body></html>"""


if __name__ == "__main__":
    ghi(sys.argv[1], ve="--khong-ve" not in sys.argv)
