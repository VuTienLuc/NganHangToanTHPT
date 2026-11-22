# -*- coding: utf-8 -*-
"""MẪU TRÌNH BÀY PHIẾU BÀI HỌC (PDF) — mỗi mẫu là một bộ định nghĩa LaTeX cho cùng các lệnh:
  \\dauPhieuKhung{trường}{năm học}{tiêu đề}{tên bài (đã định dạng)}{dòng phụ}{1 = có dòng Họ tên}
  \\phanPhieu[biểu tượng]{I. KIẾN THỨC…}   \\phanCon{…}   \\dangPhieu{số}{tên dạng}   \\nhanMuc{Vận dụng}{số dạng}
  \\dongKe{n}   môi trường khungKT (ô kiến thức trọng tâm)   màu mauPhieu, mauDang
Nội dung phiếu không đổi — chỉ đổi giao diện.
"""
import re

MAU = {
    "hien_dai": {"ten": "Hiện đại — xanh dương", "mo_ta": "Thanh màu bên trái, tiêu đề chữ không chân, nhãn dạng bo tròn; sáng sủa, chuyên nghiệp",
                 "mau": ["#1e40af", "#0d9488", "#eff6ff"]},
    "tuoi_sang": {"ten": "Tươi sáng — tím cam", "mo_ta": "Nhiều màu, biểu tượng từng mục, số dạng trong vòng tròn; vui mắt cho học sinh THCS",
                  "mau": ["#6d28d9", "#ea580c", "#faf5ff"]},
    "toi_gian": {"ten": "Tối giản — in đen trắng", "mo_ta": "Chữ Palatino, kẻ đôi thanh lịch, gần như không tô nền; photo đen trắng vẫn đẹp, tiết kiệm mực",
                 "mau": ["#262626", "#7f1d1d", "#ffffff"]},
    "co_dien": {"ten": "Cổ điển (như trước)", "mo_ta": "Mẫu cũ: khung xanh đậm, ô dạng màu xanh lục",
                "mau": ["#15438c", "#00796b", "#f3f6fb"]},
}
MAC_DINH = "hien_dai"

CHUNG = r"""
\usepackage{tcolorbox}\tcbuselibrary{skins,breakable}
\providecommand{\sanS}{\fontfamily{phv}\selectfont}
"""

DINH_NGHIA = {
# ------------------------------------------------------------------ cổ điển (giữ nguyên dáng cũ)
"co_dien": r"""
\definecolor{mauPhieu}{RGB}{21,67,140}\definecolor{mauDang}{RGB}{0,121,107}\colorlet{mauNhan}{red!75!black}
\newcommand{\phanPhieu}[2][]{\par\medskip\noindent{\color{mauPhieu}\rule[0.3ex]{0.6em}{0.6em}\ \large\bfseries #2}\par\vspace{-2pt}\noindent{\color{mauPhieu}\rule{\linewidth}{0.6pt}}\par\smallskip}
\newcommand{\phanCon}[1]{\par\smallskip\noindent{\bfseries\color{mauPhieu}#1}\par}
\newcommand{\dangPhieu}[2]{\par\smallskip\noindent{\colorbox{mauDang!12}{\color{mauDang}\bfseries\small\ Dạng #1\ }\ \textit{#2}}\par\nopagebreak}
\newcommand{\nhanMuc}[2]{\par\smallskip\noindent{\colorbox{mauNhan}{\color{white}\bfseries\scriptsize\ #1\ }\ {\scriptsize\itshape\color{black!60}Dạng #2}}\par\nopagebreak}
\newcommand{\dongKe}[1]{\par\foreach \i in {1,...,#1}{\noindent\makebox[\linewidth]{\rule{0pt}{8mm}\color{black!35}\dotfill}\par}}
\newtcolorbox{khungKT}{colback=white,colframe=mauPhieu!60,boxrule=0.5pt,arc=1mm,left=3mm,right=3mm,top=1.5mm,bottom=1.5mm,breakable,width=\linewidth}
\newcommand{\dauPhieuKhung}[6]{\begin{tcolorbox}[colback=mauPhieu!4,colframe=mauPhieu,boxrule=0.8pt,arc=2mm,left=3mm,right=3mm,top=1.5mm,bottom=1.5mm]
{\small #1\hfill #2}\par\smallskip
\begin{center}{\Large\bfseries\color{mauPhieu} #3}\\[2pt]#4\\[2pt]{\small #5}\end{center}
\ifnum#6=1 {\small Họ và tên: \makebox[6cm]{\dotfill}\hfill Lớp: \makebox[1.8cm]{\dotfill}\hfill Ngày: \makebox[2.4cm]{\dotfill}}\fi
\end{tcolorbox}}
""",
# ------------------------------------------------------------------ 1. hiện đại — xanh dương
"hien_dai": r"""
\definecolor{mauPhieu}{RGB}{30,64,175}\definecolor{mauDang}{RGB}{13,148,136}\definecolor{mauNen}{RGB}{239,246,255}\definecolor{mauNhan}{RGB}{234,88,12}
\newcommand{\phanPhieu}[2][\faStar]{\par\medskip\noindent
  \tikz[reset cm,baseline=(c.base)]\node[fill=mauPhieu,text=white,circle,inner sep=0pt,minimum size=6.2mm,font=\footnotesize](c){#1};%
  \hspace{1.6mm}{\sanS\bfseries\large\color{mauPhieu}#2}\hspace{2mm}{\color{mauPhieu!25}\leaders\hrule height 0.55ex depth -0.38ex\hfill\kern0pt}\par\smallskip}
\newcommand{\phanCon}[1]{\par\smallskip\noindent{\color{mauPhieu}\rule[-0.2ex]{2.6pt}{2.2ex}}\hspace{1.4mm}{\sanS\bfseries\color{mauPhieu!85!black}#1}\par}
\newcommand{\dangPhieu}[2]{\par\smallskip\noindent\tikz[reset cm,baseline=(d.base)]\node[fill=mauDang,text=white,rounded corners=1.6mm,inner xsep=2.2mm,inner ysep=1.6pt,font=\sanS\bfseries\scriptsize](d){DẠNG #1};\ {\color{mauDang!65!black}\itshape #2}\par\nopagebreak}
\newcommand{\nhanMuc}[2]{\par\smallskip\noindent\tikz[reset cm,baseline=(m.base)]\node[fill=mauNhan,text=white,rounded corners=1.6mm,inner xsep=2mm,inner ysep=1.4pt,font=\sanS\bfseries\scriptsize](m){#1};\ {\scriptsize\itshape\color{black!55}Dạng #2}\par\nopagebreak}
\newcommand{\dongKe}[1]{\par\foreach \i in {1,...,#1}{\noindent\makebox[\linewidth]{\rule{0pt}{8mm}{\color{mauPhieu!22}\leaders\hrule height 0.45pt\hfill}}\par}}
\newtcolorbox{khungKT}{enhanced,breakable,colback=mauNen,colframe=mauNen,boxrule=0pt,sharp corners=west,arc=2.5mm,
  borderline west={2.4pt}{0pt}{mauPhieu},left=4mm,right=3mm,top=2mm,bottom=2mm,width=\linewidth}
\newcommand{\dauPhieuKhung}[6]{\begin{tcolorbox}[enhanced,colback=mauNen,colframe=mauNen,boxrule=0pt,sharp corners=west,arc=3mm,
  borderline west={5pt}{0pt}{mauPhieu},left=5mm,right=4mm,top=2.2mm,bottom=2.2mm]
{\sanS\footnotesize\color{mauPhieu!75!black}#1\hfill #2}\par\vspace{3pt}
{\centering{\sanS\bfseries\LARGE\color{mauPhieu}#3}\par\vspace{2pt}{\color{black!85}#4}\par\vspace{3pt}
{\sanS\footnotesize\color{black!60}#5}\par}
\ifnum#6=1 \vspace{4pt}{\small{\color{mauPhieu}\faUser}\ Họ và tên: \makebox[5.4cm]{\dotfill}\hfill Lớp: \makebox[1.8cm]{\dotfill}\hfill{\color{mauPhieu}\faCalendar}\ Ngày: \makebox[2.3cm]{\dotfill}}\fi
\end{tcolorbox}}
\renewcommand{\footrule}{{\color{mauPhieu!35}\hrule width\headwidth height 0.5pt}\vskip 2pt}
""",
# ------------------------------------------------------------------ 2. tươi sáng — tím cam
"tuoi_sang": r"""
\definecolor{mauPhieu}{RGB}{109,40,217}\definecolor{mauDang}{RGB}{234,88,12}\definecolor{mauPhu}{RGB}{16,185,129}\definecolor{mauNen}{RGB}{250,245,255}\colorlet{mauNhan}{mauPhu!85!black}
\newcommand{\phanPhieu}[2][\faStar]{\par\medskip\noindent
  \tikz[reset cm,baseline=(t.base)]\node[fill=mauPhieu,text=white,rounded corners=2.2mm,inner xsep=3mm,inner ysep=2.4pt,font=\sanS\bfseries](t){#1\hspace{1.6mm}#2};\par
  \vspace{-1.5pt}\noindent{\color{mauPhieu}\rule{\linewidth}{1.3pt}}\par\smallskip}
\newcommand{\phanCon}[1]{\par\smallskip\noindent{\sanS\bfseries\color{mauDang}\faChevronCircleRight\ #1}\par}
\newcommand{\dangPhieu}[2]{\par\smallskip\noindent\tikz[reset cm,baseline=(n.base)]\node[circle,fill=mauDang,text=white,inner sep=0pt,minimum size=5.4mm,font=\sanS\bfseries\footnotesize](n){#1};\ {\sanS\bfseries\color{mauDang!80!black}#2}\par\nopagebreak}
\newcommand{\nhanMuc}[2]{\par\smallskip\noindent\tikz[reset cm,baseline=(m.base)]\node[fill=mauNhan,text=white,rounded corners=2mm,inner xsep=2mm,inner ysep=1.4pt,font=\sanS\bfseries\scriptsize](m){\faStar\ #1};\ {\scriptsize\itshape\color{black!55}Dạng #2}\par\nopagebreak}
\newcommand{\dongKe}[1]{\par\foreach \i in {1,...,#1}{\noindent\makebox[\linewidth]{\rule{0pt}{8mm}\color{mauPhieu!30}\dotfill}\par}}
\newtcolorbox{khungKT}{enhanced,breakable,colback=mauNen,colframe=mauPhieu!45,boxrule=0.9pt,arc=3mm,left=4mm,right=4mm,top=3mm,bottom=2mm,width=\linewidth,
  overlay unbroken and first={\node[circle,fill=mauDang,text=white,inner sep=0pt,minimum size=6mm,font=\small] at ([xshift=5mm]frame.north west){\faLightbulbO};}}
\newcommand{\dauPhieuKhung}[6]{\begin{tcolorbox}[enhanced,colback=white,colframe=mauPhieu,boxrule=1pt,arc=4mm,left=4mm,right=4mm,top=1.5mm,bottom=2mm,
  title={\sanS\bfseries\LARGE #3},halign title=center,colbacktitle=mauPhieu,coltitle=white,toptitle=1.5mm,bottomtitle=1.5mm,
  overlay={\fill[mauDang] ([xshift=-9mm,yshift=-5.5mm]frame.north east) circle (2.4mm);\fill[mauPhu] ([xshift=-15.5mm,yshift=-5.5mm]frame.north east) circle (1.6mm);
           \fill[mauDang] ([xshift=9mm,yshift=-5.5mm]frame.north west) circle (2.4mm);\fill[mauPhu] ([xshift=15.5mm,yshift=-5.5mm]frame.north west) circle (1.6mm);}]
{\sanS\footnotesize\color{mauPhieu}#1\hfill #2}\par\vspace{2pt}
{\centering{\color{mauDang!85!black}#4}\par\vspace{2pt}{\sanS\footnotesize\color{black!60}\faBook\ #5}\par}
\ifnum#6=1 \vspace{4pt}{\small{\color{mauDang}\faPencil}\ Họ và tên: \makebox[5.4cm]{\dotfill}\hfill Lớp: \makebox[1.8cm]{\dotfill}\hfill{\color{mauDang}\faCalendar}\ Ngày: \makebox[2.3cm]{\dotfill}}\fi
\end{tcolorbox}}
\renewcommand{\footrule}{{\color{mauDang}\hrule width\headwidth height 0.8pt}\vskip 2pt}
""",
# ------------------------------------------------------------------ 3. tối giản — in đen trắng
"toi_gian": r"""
\renewcommand{\rmdefault}{ppl}\normalfont
\definecolor{mauPhieu}{RGB}{38,38,38}\definecolor{mauDang}{RGB}{127,29,29}\colorlet{mauNhan}{black!80}
\newcommand{\phanPhieu}[2][]{\par\medskip\noindent{\bfseries\large\color{mauDang}#2}\par\nointerlineskip\vspace{2pt}\noindent{\color{mauPhieu}\rule{\linewidth}{0.8pt}}\par\smallskip}
\newcommand{\phanCon}[1]{\par\smallskip\noindent{\bfseries\itshape\color{mauPhieu}#1}\par}
\newcommand{\dangPhieu}[2]{\par\smallskip\noindent{\color{mauDang}\rule[-0.25ex]{1.2pt}{2.1ex}}\hspace{1.4mm}{\bfseries\color{mauDang}Dạng #1.}\ {\itshape #2}\par\nopagebreak}
\newcommand{\nhanMuc}[2]{\par\smallskip\noindent{\setlength{\fboxsep}{1.4pt}\setlength{\fboxrule}{0.5pt}\framebox{\scriptsize\bfseries\MakeUppercase{#1}}}\ {\scriptsize\itshape Dạng #2}\par\nopagebreak}
\newcommand{\dongKe}[1]{\par\foreach \i in {1,...,#1}{\noindent\makebox[\linewidth]{\rule{0pt}{8mm}{\color{black!28}\leaders\hrule height 0.4pt\hfill}}\par}}
\newtcolorbox{khungKT}{breakable,colback=white,colframe=black!75,boxrule=0.45pt,sharp corners,left=3mm,right=3mm,top=1.8mm,bottom=1.8mm,width=\linewidth}
\newcommand{\dauPhieuKhung}[6]{\par\noindent{\color{mauPhieu}\rule{\linewidth}{1.6pt}}\par\nointerlineskip\vspace{4pt}
{\footnotesize\MakeUppercase{#1}\hfill\MakeUppercase{#2}}\par\vspace{3pt}
{\centering{\LARGE\bfseries\color{mauDang}#3}\par\vspace{3pt}#4\par\vspace{2pt}{\small\itshape #5}\par}
\ifnum#6=1 \vspace{5pt}{\small Họ và tên: \makebox[6cm]{\dotfill}\hfill Lớp: \makebox[1.8cm]{\dotfill}\hfill Ngày: \makebox[2.4cm]{\dotfill}}\par\fi
\nointerlineskip\vspace{4pt}\noindent{\color{mauPhieu}\rule{\linewidth}{0.4pt}}\par\nointerlineskip\vspace{1.4pt}\noindent{\color{mauPhieu}\rule{\linewidth}{0.4pt}}\par\medskip}
""",
}

# phiếu tự luận (paracol): đổi đầu dạng / đầu cột cho mẫu tối giản để không tô nền đậm
TU_LUAN_THEM = {
    "toi_gian": r"""
\renewcommand{\dauCot}[2]{\noindent{\color{mauDang}\bfseries\small #2}\par\nointerlineskip\vspace{1.5pt}\noindent{\color{black!40}\rule{\linewidth}{0.4pt}}\par\smallskip\nhoHinh\setlength{\parindent}{0pt}}
\backgroundcolor{c[0](1.2mm,0.8mm)}{black!3}\backgroundcolor{c[1](1.2mm,0.8mm)}{white}
\renewcommand{\khoiDangTL}[4]{\par\smallskip\needspace{5\baselineskip}%
  \noindent{\bfseries\color{mauDang}DẠNG #1.}\ {\itshape #2}\par\nointerlineskip\vspace{2pt}\noindent{\color{mauDang}\rule{\linewidth}{0.7pt}}\par\nopagebreak\vspace{2pt}
  \begin{paracol}{2}\dauCot{}{VÍ DỤ MẪU}#3\par\smallskip\switchcolumn\dauCot{}{TỰ LUYỆN}#4\par\smallskip\end{paracol}
  \vspace{-\parskip}\noindent{\color{black!30}\rule{\linewidth}{0.4pt}}\par}
\renewcommand{\khoiDangDoc}[4]{\par\smallskip\needspace{6\baselineskip}%
  \noindent{\bfseries\color{mauDang}DẠNG #1.}\ {\itshape #2}\par\nointerlineskip\vspace{2pt}\noindent{\color{mauDang}\rule{\linewidth}{0.7pt}}\par\nopagebreak\vspace{3pt}
  {\setlength{\parindent}{0pt}\dauDoc{mauDang}{VÍ DỤ MẪU}#3\par\medskip\dauDoc{mauPhieu}{TỰ LUYỆN}#4\par\smallskip}
  \vspace{-\parskip}\noindent{\color{black!30}\rule{\linewidth}{0.4pt}}\par}
\renewcommand{\nhanTL}[1]{{\setlength{\fboxsep}{1.2pt}\framebox{\scriptsize\bfseries\MakeUppercase{#1}}}}
""",
    "tuoi_sang": r"""
\renewcommand{\nhanTL}[1]{\tikz[reset cm,baseline=(m.base)]\node[fill=mauNhan,text=white,rounded corners=1.6mm,inner xsep=1.6mm,inner ysep=1pt,font=\sanS\bfseries\scriptsize](m){\faStar\ #1};}
\backgroundcolor{c[0](1.2mm,0.8mm)}{mauDang!5}\backgroundcolor{c[1](1.2mm,0.8mm)}{mauPhieu!4}
""",
    "hien_dai": r"""
\renewcommand{\nhanTL}[1]{\tikz[reset cm,baseline=(m.base)]\node[fill=mauNhan,text=white,rounded corners=1.6mm,inner xsep=1.6mm,inner ysep=1pt,font=\sanS\bfseries\scriptsize](m){#1};}
\backgroundcolor{c[0](1.2mm,0.8mm)}{mauDang!6}\backgroundcolor{c[1](1.2mm,0.8mm)}{mauNen}
""",
}

BIEU_TUONG = [("KIẾN THỨC", r"\faLightbulbO"), ("LUYỆN TẬP", r"\faPencil"), ("VỀ NHÀ", r"\faHome"), ("ĐÁP ÁN", r"\faKey"),
              ("LỜI GIẢI", r"\faCheckSquareO"), ("DẠNG", r"\faListOl"), ("BÀI TẬP", r"\faListOl")]


def chon(ma):
    return ma if ma in DINH_NGHIA else MAC_DINH


def mo_dau(ma):
    """Đoạn preamble của mẫu (đặt sau phần cài đặt chung của phiếu)."""
    return CHUNG + DINH_NGHIA[chon(ma)]


def tu_luan_them(ma):
    return TU_LUAN_THEM.get(chon(ma), "")


def gan_bieu_tuong(t):
    """\\phanPhieu{II. LUYỆN TẬP} → \\phanPhieu[\\faPencil]{II. LUYỆN TẬP} (mẫu nào không dùng biểu tượng thì bỏ qua)."""
    def thay(m):
        ten = m.group(1)
        bt = next((b for k, b in BIEU_TUONG if k in ten.upper()), r"\faStar")
        return r"\phanPhieu[" + bt + "]{" + ten + "}"
    return re.sub(r"\\phanPhieu\{([^{}]*)\}", thay, t)


def danh_sach():
    return [{"ma": k, **v} for k, v in MAU.items()]
