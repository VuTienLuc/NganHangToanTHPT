# -*- coding: utf-8 -*-
"""
BẢN TRÌNH CHIẾU SỬA BÀI (Beamer 16:9) và BẢN LEFTNOTE (chừa lề ghi chú) cho từng mã đề — như bộ 4 file của phần mềm cũ:
  tex/BeamerTrang_101.tex : nền trắng chữ đen, mỗi slide 1 câu, chữ to — chiếu lên bảng để viết/sửa trực tiếp
  tex/BeamerXanh_101.tex  : nền xanh nhạt, thanh tiêu đề xanh, hiệu ứng chuyển slide — thao giảng, ôn tập
      mỗi câu: slide đề (bấm tiếp → tô đáp án đúng / hiện Đ-S / đáp số) rồi slide(s) lời giải
  tex/Leftnote_101.tex    : đề in 0,7 bề rộng trang, 0,3 bên phải là cột "Ghi chú" có dòng kẻ
Biên dịch bằng nh_core.bien_dich_thu_muc (cùng lúc với De_*.tex).
"""
import os, re, json
from k12word import tach_cau

PHAN = [("TN", "PHẦN I. Trắc nghiệm nhiều phương án lựa chọn"), ("DS", "PHẦN II. Trắc nghiệm đúng sai"),
        ("TLN", "PHẦN III. Trả lời ngắn"), ("TL", "PHẦN IV. Tự luận")]

def tho(s):
    """Chuỗi thường → an toàn trong LaTeX."""
    return re.sub(r"(?<!\\)([&%#_])", r"\\\1", s or "")

# --------------------------------------------------------------------------- phần đầu Beamer
def dau_beamer(thu_muc_tex, kieu, tt, ma_de):
    """Lấy các gói/macro toán từ file đề (KhaibaoToan, Khaibao, tkz…) nhưng bỏ những gì chỉ dành cho sách in."""
    pre = r"""\usepackage[utf8]{vietnam}
\input{Khaibao/KhaibaoToan}
\input{Khaibao/Khaibao}
\colorlet{mausection}{blue!70!black}\colorlet{mauchuong}{blue!70!black}\colorlet{mausubsection}{teal}
\usepackage{tkz-euclide,tkz-tab}
\usetikzlibrary{angles,intersections,shapes.geometric,arrows,decorations.markings,arrows.meta,patterns.meta}
\usetikzlibrary{shadows.blur,patterns,quotes,bending,matrix,positioning,calc}
\tikzset{>=stealth,line join=round,line cap=round}
\newcommand{\khungct}[1]{\tcboxmath[colback=mausection!5,colframe=mausection,boxsep=1pt,boxrule=1pt,arc is angular]{#1}}
\newcommand{\khung}[1]{\tcbox[colback=mausection!5,colframe=mausection,boxsep=1pt,boxrule=1pt,arc is angular]{#1}}
\def\chongbang{\rule[-14pt]{0pt}{33pt}}
\usepackage{bm}
\usepackage{casio580x}
\def\xuongdong{\break}
\IfFileExists{Image/GImage.tex}{\input{Image/GImage.tex}}{}
\usepackage{tikz-3dplot}
"""
    if os.environ.get("NH_THAY_VIETNAM"):
        pre = pre.replace("\\usepackage[utf8]{vietnam}", os.environ["NH_THAY_VIETNAM"])
    ten = tho(tt.get("ten_ky_thi") or "")
    mon = tho(tt.get("mon") or "")
    if kieu == "xanh":
        giao_dien = r"""
\definecolor{xanhDam}{RGB}{13,71,161}\definecolor{xanhNhat}{RGB}{232,242,253}
\setbeamertemplate{background canvas}{\begin{tikzpicture}[remember picture,overlay]
  \shade[top color=xanhNhat,bottom color=white] (current page.south west) rectangle (current page.north east);
  \fill[xanhDam!12] (current page.south west) rectangle ([yshift=0.45cm]current page.south east);\end{tikzpicture}}
\setbeamercolor{frametitle}{fg=white,bg=xanhDam}
\setbeamertemplate{frametitle}{\nointerlineskip\begin{beamercolorbox}[wd=\paperwidth,ht=0.95cm,dp=0.3cm,leftskip=0.5cm]{frametitle}%
  \usebeamerfont{frametitle}\insertframetitle\hfill{\small\insertframesubtitle}\hspace*{0.5cm}\end{beamercolorbox}}
\setbeamercolor{normal text}{fg=black!90}
\setbeamertemplate{footline}{\hspace*{0.5cm}{\scriptsize\color{xanhDam}\TENKY\ -- Mã đề \MADE}\hfill
  {\scriptsize\color{xanhDam}\insertframenumber/\inserttotalframenumber}\hspace*{0.5cm}\vspace*{0.12cm}}
\newcommand{\hieuung}{\transfade[duration=0.3]}
\newcommand{\coChu}{\normalsize}
\colorlet{mauDung}{red!80!black}
"""
    else:
        giao_dien = r"""
\setbeamercolor{frametitle}{fg=black,bg=white}
\setbeamertemplate{frametitle}{\nointerlineskip\vspace*{0.15cm}\hspace*{0.1cm}{\bfseries\insertframetitle}\hfill
  {\small\insertframesubtitle}\hspace*{0.1cm}\par\vspace*{-0.1cm}\rule{\textwidth}{0.6pt}}
\setbeamercolor{normal text}{fg=black}
\setbeamertemplate{footline}{\hspace*{0.4cm}{\scriptsize\color{black!60}\TENKY\ -- Mã đề \MADE}\hfill
  {\scriptsize\color{black!60}\insertframenumber/\inserttotalframenumber}\hspace*{0.4cm}\vspace*{0.1cm}}
\newcommand{\hieuung}{}
\newcommand{\coChu}{\large}
\colorlet{mauDung}{red!80!black}
"""
    return (r"\documentclass[aspectratio=169,12pt,noamsthm]{beamer}" + "\n" + pre + r"""
\usepackage[shortlabels]{enumitem}
\setlist[itemize]{label=\textbullet}
\usepackage{multicol}
\setbeamertemplate{navigation symbols}{}
\setbeamertemplate{frametitle continuation}{}
\setbeamersize{text margin left=0.6cm,text margin right=0.6cm}
\def\TENKY{""" + ten + "}\\def\\MADE{" + ma_de + "}\\def\\MON{" + mon + r"""}
""" + giao_dien + r"""
% ---------- macro thay cho ex_test (đề trong kho dùng các lệnh này)
\providecommand{\immini}{}\renewcommand{\immini}[3][]{\par\noindent\begin{minipage}[t]{0.6\linewidth}\vspace{0pt}#2\end{minipage}\hfill
  \begin{minipage}[t]{0.37\linewidth}\vspace{0pt}\centering #3\end{minipage}\par}
\newenvironment{itemchoice}{\begin{enumerate}[label=\alph*),leftmargin=1.6em,itemsep=2pt]\let\itemch\item}{\end{enumerate}}
\NewDocumentEnvironment{listEX}{O{1}}{\ifnum#1>1 \begin{multicols}{#1}\fi\begin{itemize}[leftmargin=1.2em]}%
  {\end{itemize}\ifnum#1>1 \end{multicols}\fi}
\ExplSyntaxOn
\NewDocumentEnvironment{enumEX}{O{1)} m}{
  \tl_set:Nn \l_tmpa_tl {#1}
  \regex_replace_once:nnN {a} {\c{alph}*} \l_tmpa_tl \regex_replace_once:nnN {A} {\c{Alph}*} \l_tmpa_tl
  \regex_replace_once:nnN {1} {\c{arabic}*} \l_tmpa_tl \regex_replace_once:nnN {I} {\c{Roman}*} \l_tmpa_tl
  \int_compare:nT {#2>1} {\begin{multicols}{#2}}
  \exp_args:NV \enumEXbatdau \l_tmpa_tl
}{\end{enumerate}\int_compare:nT {#2>1} {\end{multicols}}}
\ExplSyntaxOff
\newcommand{\enumEXbatdau}[1]{\begin{enumerate}[label={#1},leftmargin=1.8em]}
\providecommand{\True}{}\providecommand{\loigiai}[1]{}\providecommand{\dapso}[1]{}
% ---------- co nội dung vừa khung: quá cao thì thu nhỏ
\newsavebox\hopCau
\newcommand{\vuaKhung}[2][0.74]{\sbox\hopCau{\begin{minipage}[t]{\linewidth}\vspace{0pt}\coChu #2\end{minipage}}%
  \ifdim\dimexpr\ht\hopCau+\dp\hopCau\relax>#1\textheight\relax\resizebox*{!}{#1\textheight}{\usebox\hopCau}\else\usebox\hopCau\fi}
% ---------- phương án: tự xếp 4 / 2 / 1 cột; slide 2 tô đáp án đúng
\newlength\rongPA\newlength\tamPA
\newcommand{\nhanPA}[2]{\alt<2->{\ifnum#2=1 \tikz[baseline=(n.base)]\node[circle,fill=mauDung,text=white,inner sep=1.2pt,font=\bfseries\small](n){#1};\else\textbf{#1.}\fi}{\textbf{#1.}}}
\newcommand{\phuongAn}[8]{\par\medskip
  \settowidth\rongPA{#1}\settowidth\tamPA{#3}\ifdim\tamPA>\rongPA\rongPA=\tamPA\fi
  \settowidth\tamPA{#5}\ifdim\tamPA>\rongPA\rongPA=\tamPA\fi\settowidth\tamPA{#7}\ifdim\tamPA>\rongPA\rongPA=\tamPA\fi
  \ifdim\rongPA<0.2\linewidth
    \noindent\makebox[0.25\linewidth][l]{\nhanPA{A}{#2}~#1}\makebox[0.25\linewidth][l]{\nhanPA{B}{#4}~#3}%
    \makebox[0.25\linewidth][l]{\nhanPA{C}{#6}~#5}\makebox[0.25\linewidth][l]{\nhanPA{D}{#8}~#7}\par
  \else\ifdim\rongPA<0.44\linewidth
    \noindent\makebox[0.5\linewidth][l]{\nhanPA{A}{#2}~#1}\makebox[0.5\linewidth][l]{\nhanPA{B}{#4}~#3}\par\smallskip
    \noindent\makebox[0.5\linewidth][l]{\nhanPA{C}{#6}~#5}\makebox[0.5\linewidth][l]{\nhanPA{D}{#8}~#7}\par
  \else
    \begin{itemize}[leftmargin=1.6em,label={},itemsep=2pt]\item[\nhanPA{A}{#2}] #1\item[\nhanPA{B}{#4}] #3
    \item[\nhanPA{C}{#6}] #5\item[\nhanPA{D}{#8}] #7\end{itemize}
  \fi\fi}
\newcommand{\yDS}[3]{\item[\textbf{#1)}] #3\only<2->{\hfill\textbf{\textcolor{mauDung}{#2}}}}
\begin{document}
""")

def khung_cau(so, loai, tieu_phan, p, dap_an, xanh):
    de = p["de"].strip()
    than = de
    if loai == "TN" and p["pa"] and len(p["pa"]) == 4:
        args = "".join(f"{{{x}}}{{{1 if 'ABCD'[j] == dap_an else 0}}}" for j, x in enumerate(p["pa"]))
        than += "\n\\phuongAn" + args
    elif loai == "DS" and p["pa"] and len(p["pa"]) == 4:
        than += "\n\\begin{itemize}[leftmargin=1.8em,label={},itemsep=3pt]\n" + "\n".join(
            f"\\yDS{{{'abcd'[j]}}}{{{'Đúng' if j < len(dap_an) and dap_an[j] == 'Đ' else 'Sai'}}}{{{x}}}"
            for j, x in enumerate(p["pa"])) + "\n\\end{itemize}"
    elif loai == "TLN":
        than += f"\n\\par\\medskip\\only<2->{{\\textbf{{\\textcolor{{mauDung}}{{Đáp số: {tho(dap_an)}}}}}}}"
    hai_slide = "<1-2>" if loai in ("TN", "DS", "TLN") else ""
    hu = "\\hieuung" if xanh else ""
    fr = (f"\\begin{{frame}}{hai_slide}[t]{{Câu {so}}}{{{tieu_phan}}}{hu}\n\\vuaKhung{{{than}}}\n\\end{{frame}}\n")
    # lời giải
    if p["y_giai"]:
        dau, ys, cuoi = p["y_giai"]
        lg = dau + "\n\\begin{itemchoice}\n" + "\n".join("\\itemch " + y for y in ys) + "\n\\end{itemchoice}\n" + cuoi
    else:
        lg = p["lg"] or ""
    if lg.strip():
        dap = (f"Đáp án: {dap_an}" if loai == "TN" else
               "Đáp án: " + " ".join(f"{'abcd'[j]}) {x}" for j, x in enumerate(dap_an[:4])) if loai == "DS" else
               f"Đáp số: {tho(dap_an)}" if loai == "TLN" else "")
        fr += (f"\\begin{{frame}}[t,allowframebreaks]{{Lời giải câu {so}}}{{{dap}}}{hu}\n\\coChu\n{lg}\n\\end{{frame}}\n")
    return fr

def tao_beamer(thu_muc_de, kieu="trang"):
    tex = os.path.join(thu_muc_de, "tex")
    du_lieu = json.load(open(os.path.join(tex, "_k12_cau.json"), encoding="utf-8"))
    try:
        tt = json.load(open(os.path.join(tex, "_thong_tin_de.json"), encoding="utf-8"))
    except OSError:
        tt = {}
    ra = []
    for ma_de, ds in du_lieu.items():
        than = [dau_beamer(tex, kieu, tt, ma_de)]
        than.append(r"""\begin{frame}[plain]\centering\vspace*{1.2cm}
{\large """ + tho(tt.get("truong") or "") + r"""}\par\bigskip
{\LARGE\bfseries """ + tho(tt.get("ten_ky_thi") or "") + r"""}\par\medskip
{\Large """ + tho(tt.get("mon") or "") + r"""}\par\bigskip
{\Large\bfseries Mã đề """ + ma_de + r"""}\par\vfill
{\normalsize SỬA BÀI -- ĐÁP ÁN VÀ LỜI GIẢI CHI TIẾT}\par\medskip
{\small GV: """ + tho(tt.get("giao_vien") or "") + r"""}\par\vspace*{0.8cm}
\end{frame}
""")
        for loai, tieu in PHAN:
            cac = [c for c in ds if c["loai"] == loai]
            if not cac:
                continue
            than.append(f"\\begin{{frame}}[plain]\\centering\\vfill{{\\LARGE\\bfseries {tieu}}}\\par\\medskip"
                        f"{{\\large {len(cac)} câu}}\\vfill\\end{{frame}}\n")
            for so, c in enumerate(cac, 1):
                than.append(khung_cau(so, loai, tieu.split(".")[0], tach_cau(c), c.get("dap_an") or "", kieu == "xanh"))
        than.append("\\end{document}\n")
        ten = f"Beamer{'Xanh' if kieu == 'xanh' else 'Trang'}_{ma_de}.tex"
        open(os.path.join(tex, ten), "w", encoding="utf-8").write("".join(than))
        ra.append(ten)
    return ra

# --------------------------------------------------------------------------- LEFTNOTE
LEFTNOTE_BG = r"""
%==================== LEFTNOTE: đề 0,7 trang, cột ghi chú 0,3 bên phải ====================
\usepackage{eso-pic}
\AddToShipoutPictureBG{\begin{tikzpicture}[remember picture,overlay]
  \coordinate (G) at ([xshift=-0.3\paperwidth-0.25cm]current page.north east);
  \draw[gray!60,line width=0.6pt] ([yshift=-1.4cm]G) -- ([yshift=1.5cm]G |- current page.south);
  \node[anchor=north west,font=\small\bfseries\color{gray}] at ([xshift=0.25cm,yshift=-1.35cm]G) {\faPencil\ GHI CHÚ};
  \foreach \i in {1,...,34} \draw[gray!35,dotted,line width=0.5pt]
     ([xshift=0.25cm,yshift=-1.55cm-\i*0.72cm]G) -- ([xshift=-0.8cm,yshift=-1.55cm-\i*0.72cm]G -| current page.east);
\end{tikzpicture}}
"""

def tao_leftnote(thu_muc_de):
    tex = os.path.join(thu_muc_de, "tex")
    ra = []
    for f in sorted(os.listdir(tex)):
        m = re.match(r"De_(\d+)\.tex$", f)
        if not m:
            continue
        t = open(os.path.join(tex, f), encoding="utf-8").read()
        t = re.sub(r"\\usepackage\[[^\]]*\]\{geometry\}",
                   lambda _: "\\usepackage[a4paper,left=1.5cm,right=7.2cm,top=1.5cm,bottom=1.6cm]{geometry}", t, 1)
        t = t.replace("\\begin{multicols}{2}", "").replace("\\end{multicols}", "")
        t = t.replace("\\begin{document}", LEFTNOTE_BG + "\\begin{document}", 1)
        ten = f"Leftnote_{m.group(1)}.tex"
        open(os.path.join(tex, ten), "w", encoding="utf-8").write(t)
        ra.append(ten)
    return ra

def xuat(thu_muc_de, leftnote=True, beamer=True, in_ra=print):
    ds = []
    if leftnote:
        ds += tao_leftnote(thu_muc_de)
    if beamer:
        ds += tao_beamer(thu_muc_de, "trang") + tao_beamer(thu_muc_de, "xanh")
    in_ra(f"Đã tạo {len(ds)} file Leftnote/Beamer trong tex/ (biên dịch cùng đề PDF).")
    return ds
