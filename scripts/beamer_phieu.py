# -*- coding: utf-8 -*-
"""
BEAMER TRÌNH CHIẾU KÈM PHIẾU BÀI HỌC (16:9, màu sắc theo từng dạng):
  • Slide bìa: tên phiếu, lớp, thời lượng, GV
  • Nội dung: danh sách các dạng (huy hiệu màu)
  • Kiến thức trọng tâm (phần chung của ô "Kiến thức trọng tâm")
  • Mỗi dạng:  slide mở dạng  →  slide PHƯƠNG PHÁP (thiết kế nổi bật, các bước đánh số)
               →  Câu 1 – Ví dụ mẫu (đề → bấm tiếp hiện đáp án → lời giải)
               →  Câu 2 – Học sinh tự làm (đề, chừa chỗ viết → bấm tiếp hiện đáp án → lời giải để chữa)
  • Slide kết: giao bài tập về nhà
Câu 1, câu 2 lấy từ phần II. LUYỆN TẬP của phiếu (cùng dạng), nên chiếu đúng câu học sinh đang có trên phiếu.

Phương pháp từng dạng lấy theo thứ tự ưu tiên:
  1) trong ô Kiến thức trọng tâm có dòng  %% DANG <mã dạng>  (prompt AI đã yêu cầu), nội dung tới dòng %% DANG kế tiếp;
  2) hoặc các mục \\textbf{Dạng n. …} trong ô Kiến thức trọng tâm;
  3) hoặc bản đã lưu ở du-lieu/phuong_phap/<mã>.tex (tự lưu mỗi lần tạo phiếu có phương pháp);
  4) không có → slide "Phương pháp" với các bước để trống cho thầy ghi bảng.
"""
import os, re
from k12word import tach_cau
from beamer_de import dau_beamer, khung_cau, tho, boc_hinh

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THU_MUC_PP = os.path.join(GOC, "du-lieu", "phuong_phap")
# bảng màu tươi cho từng dạng (đậm, nhạt)
MAU = [("1565C0", "E3F2FD"), ("E65100", "FFF3E0"), ("2E7D32", "E8F5E9"), ("6A1B9A", "F3E5F5"),
       ("C2185B", "FCE4EC"), ("00838F", "E0F7FA"), ("AD1457", "FDE7EF"), ("EF6C00", "FFF8E1"),
       ("283593", "E8EAF6"), ("558B2F", "F1F8E9")]
TEN_LOAI = {"TN": "Trắc nghiệm", "DS": "Đúng/Sai", "TLN": "Trả lời ngắn"}


def tep_pp(dang_key):
    return os.path.join(THU_MUC_PP, dang_key.replace("?", "_") + ".tex")


def can_bang(t):
    """Bỏ \\end{itemize|enumerate} thừa ở đầu và \\begin{…} chưa đóng ở cuối của một đoạn cắt ra."""
    for env in ("itemize", "enumerate"):
        b = r"\begin{" + env + "}"; e = r"\end{" + env + "}"
        # \end thừa
        while True:
            mo = dong = 0; xoa = None
            for m in re.finditer(re.escape(b) + "|" + re.escape(e), t):
                if m.group(0) == b:
                    mo += 1
                elif mo > 0:
                    mo -= 1
                else:
                    xoa = m; break
            if not xoa:
                break
            t = t[:xoa.start()] + t[xoa.end():]
        # \begin chưa đóng (lấy cái sau cùng)
        while t.count(b) > t.count(e):
            i = t.rfind(b)
            t = t[:i] + t[i + len(b):]
    return t.strip()


def tach_phuong_phap(kt, cac_dang):
    """→ (phần chung, {mã dạng: phương pháp})."""
    kt = kt or ""
    pp = {}
    phan = re.split(r"^[ \t]*%%[ \t]*DANG[ \t]+(\S+)[ \t]*$", kt, flags=re.M)
    if len(phan) > 1:
        chung = phan[0]
        for i in range(1, len(phan) - 1, 2):
            pp[phan[i].strip()] = can_bang(re.sub(r"^\s*(?:\\item\s*)?\\textbf\{\s*Dạng[^}]*\}\s*[.:]?", "", phan[i + 1]))
        # bỏ tiêu đề "2. Phương pháp giải các dạng" còn sót ở cuối phần chung
        chung = re.sub(r"\\textbf\{\s*\d*\.?\s*Phương pháp[^}]*\}\s*$", "", chung.strip())
        return can_bang(chung), pp
    ms = list(re.finditer(r"(?:\\item\s*)?\\textbf\{\s*Dạng\s+(\d+)\s*[.:]?[^}]*\}\s*[.:]?", kt))
    if not ms:
        return can_bang(kt), pp
    chung = kt[:ms[0].start()]
    chung = re.sub(r"\\textbf\{\s*\d*\.?\s*Phương pháp[^}]*\}\s*(\\begin\{(?:itemize|enumerate)\}\s*)?$", "", chung.strip())
    for j, m in enumerate(ms):
        n = int(m.group(1))
        doan = kt[m.end(): ms[j + 1].start() if j + 1 < len(ms) else len(kt)]
        if 1 <= n <= len(cac_dang):
            pp[cac_dang[n - 1]] = can_bang(doan)
    return can_bang(chung), pp


def luu_pp(pp):
    os.makedirs(THU_MUC_PP, exist_ok=True)
    for k, v in pp.items():
        if v.strip():
            open(tep_pp(k), "w", encoding="utf-8").write(v.strip() + "\n")


def doc_pp(k):
    try:
        return open(tep_pp(k), encoding="utf-8").read().strip()
    except OSError:
        return ""


GIAO_DIEN = r"""
%==================== GIAO DIỆN PHIẾU BÀI HỌC (màu theo dạng) ====================
\tcbuselibrary{skins}
\definecolor{mauHT}{HTML}{1565C0}\definecolor{mauNhat}{HTML}{E3F2FD}
\newcommand{\datMau}[2]{\definecolor{mauHT}{HTML}{#1}\definecolor{mauNhat}{HTML}{#2}}
\setbeamertemplate{background canvas}{\begin{tikzpicture}[remember picture,overlay]
  \shade[top color=mauNhat,bottom color=white] (current page.south west) rectangle (current page.north east);
  \fill[mauHT] (current page.south west) rectangle ([yshift=0.07cm]current page.south east);\end{tikzpicture}}
\setbeamercolor{frametitle}{fg=white,bg=mauHT}
\setbeamertemplate{frametitle}{\nointerlineskip\begin{beamercolorbox}[wd=\paperwidth,ht=0.42cm,dp=0.14cm,leftskip=0.3cm]{frametitle}%
  {\small\bfseries\insertframetitle}\hfill{\scriptsize\insertframesubtitle}\hspace*{0.3cm}\end{beamercolorbox}\vspace*{0.05cm}}
\setbeamertemplate{footline}{\hspace*{0.3cm}{\fontsize{5}{6}\selectfont\color{mauHT}\TENKY}\hfill
  {\fontsize{5}{6}\selectfont\color{mauHT}\insertframenumber/\inserttotalframenumber}\hspace*{0.3cm}\vspace*{0.1cm}}
\renewcommand{\hieuung}{\transfade[duration=0.3]}
\DeclareRobustCommand{\soBuoc}[1]{\tikz[baseline=(n.base)]\node[circle,fill=mauHT,text=white,inner sep=1.3pt,minimum size=1.15em,font=\bfseries\scriptsize](n){#1};}
\newcommand{\nhanTuLam}{\tikz[baseline=(n.base)]\node[rounded corners=2pt,fill=orange!90!red,text=white,inner sep=2pt,font=\bfseries\tiny](n){HỌC SINH TỰ LÀM};}
\newcommand{\nhanViDu}{\tikz[baseline=(n.base)]\node[rounded corners=2pt,fill=mauHT,text=white,inner sep=2pt,font=\bfseries\tiny](n){VÍ DỤ MẪU};}
% khung phương pháp: viền trái đậm, nhãn "PHƯƠNG PHÁP" gắn trên, các bước đánh số tròn màu
\newtcolorbox{hopPP}{enhanced,colback=white,colframe=mauHT,boxrule=0.8pt,arc=3mm,
  borderline west={5pt}{0pt}{mauHT},left=4mm,right=3mm,top=3.5mm,bottom=2mm,
  attach boxed title to top left={xshift=5mm,yshift=-2.6mm},
  boxed title style={colback=mauHT,colframe=mauHT,arc=2mm,boxrule=0pt},
  title={\bfseries\footnotesize\tikz[baseline=-0.6ex]{\fill[yellow!90!orange](0,0)circle(0.75ex);\fill[white](0,0)circle(0.35ex);}\ PHƯƠNG PHÁP GIẢI},
  drop fuzzy shadow=mauHT!40}
\DeclareRobustCommand{\muiTen}{\textcolor{mauHT}{$\blacktriangleright$}}
\DeclareRobustCommand{\chamKT}{\textcolor{mauHT}{$\bullet$}}
\newcommand{\kieuPP}{\setlist[enumerate,1]{label=\protect\soBuoc{\arabic*},leftmargin=1.9em,itemsep=3pt}%
  \setlist[itemize,1]{label=\protect\muiTen,leftmargin=1.4em,itemsep=2pt}}
\newcommand{\kieuKT}{\setlist[itemize,1]{label=\protect\chamKT,leftmargin=1.2em,itemsep=1pt}}
\newtcolorbox{hopKT}{enhanced,colback=white,colframe=mauHT,boxrule=0.6pt,arc=2mm,left=3mm,right=3mm,top=2mm,bottom=2mm,
  drop fuzzy shadow=mauHT!30}
\newcommand{\nenTrangTri}{\begin{tikzpicture}[remember picture,overlay]
  \fill[mauHT!14] ([xshift=-0.7cm,yshift=0.6cm]current page.south east) circle (1.15cm);
  \fill[mauHT!9] ([xshift=0.2cm,yshift=0.5cm]current page.south west) circle (1.2cm);
  \fill[mauHT!24] ([xshift=-2.2cm,yshift=1.5cm]current page.south east) circle (0.28cm);\end{tikzpicture}}
"""


def frame_pp(j, ten, noi):
    if not noi.strip():
        noi = (r"\begin{enumerate}" + "".join(r"\item \textit{Bước " + str(i) + r":}\ \textcolor{black!35}{\dotfill}" for i in (1, 2, 3))
               + r"\end{enumerate}" + "\n\\par\\smallskip{\\scriptsize\\itshape\\color{black!55} (Thầy ghi phương pháp lên bảng / dán vào ô Kiến thức trọng tâm để hiện ở đây)}")
    return (r"\begin{frame}[t]{Dạng " + str(j) + r" \textendash{} Phương pháp}{" + tho(ten) + "}\\hieuung\n\\nenTrangTri\n"
            r"\vspace*{-0.2cm}{\centering\begin{tcolorbox}[enhanced,colback=mauHT,colframe=mauHT,coltext=white,arc=3mm,boxrule=0pt,"
            r"interior style={left color=mauHT,right color=mauHT!55!white},halign=center,left=2mm,right=2mm,top=1mm,bottom=1mm,width=0.94\linewidth,drop fuzzy shadow=mauHT!50]"
            r"{\footnotesize\bfseries DẠNG " + str(j) + r"}\quad{\normalsize\bfseries " + tho(ten) + r"}\end{tcolorbox}\par}" "\n"
            r"\vspace*{0.05cm}\begin{hopPP}{\setlength\caoToiDa{0.47\textheight}\vuaKhung{\kieuPP " + noi + "}}\\end{hopPP}\n\\end{frame}\n")


def frame_mo_dang(j, ten, so_cau):
    return (r"\begin{frame}[plain]\hieuung\nenTrangTri\centering\vfill" "\n"
            r"\tikz\node[circle,fill=mauHT,text=white,minimum size=2.1cm,font=\bfseries\Huge,drop shadow]{" + str(j) + r"};\par\medskip" "\n"
            r"{\Large\bfseries\color{mauHT} DẠNG " + str(j) + r"}\par\smallskip"
            r"\begin{minipage}{0.8\linewidth}\centering\Large\bfseries " + tho(ten) + r"\end{minipage}\par\medskip"
            r"{\small\color{black!60} Phương pháp \,·\, " + str(so_cau) + r" câu luyện tập}\vfill\end{frame}" "\n")


def tao(out_tex, ten, nhan, tt, lop, tl, cac_dang, ten_dang, kq, kien_thuc, cac_loai=("TN", "DS", "TLN")):
    """Ghi out_tex/PhieuBeamer.tex. ten_dang: {mã: tên}. kq: {LT:{loai:[câu]}, …}."""
    chung, pp = tach_phuong_phap(kien_thuc, cac_dang)
    luu_pp(pp)
    tt2 = dict(tt, ten_ky_thi=f"GV: {tt.get('giao_vien') or ''}  ·  {nhan.title()}: {ten}")
    dau = dau_beamer(out_tex, "xanh", tt2, "", "2/3")
    dau = dau.replace(r"\begin{document}", GIAO_DIEN + r"\begin{document}", 1)
    # chân trang: chỉ \TENKY (không "Mã đề")
    dau = re.sub(r"\\setbeamertemplate\{footline\}\{\\hspace\*\{0\.3cm\}\{\\fontsize\{5\}\{6\}\\selectfont\\color\{xanhDam\}\\TENKY\\ -- Mã đề \\MADE\}.*?\n.*?\n",
                 "", dau, count=1, flags=re.S)
    f = [dau]
    # ---------- bìa
    f.append(r"\begin{frame}[plain]\nenTrangTri\centering\vfill" "\n"
             r"{\small " + tho(tt.get("truong") or "") + r"}\par\bigskip" "\n"
             r"\begin{tcolorbox}[enhanced,colback=mauHT,colframe=mauHT,coltext=white,arc=4mm,boxrule=0pt,interior style={left color=mauHT,right color=mauHT!55!white},halign=center,width=0.86\linewidth,drop fuzzy shadow]"
             r"{\large\bfseries " + nhan + r"}\par\smallskip{\LARGE\bfseries " + tho(ten.upper()) + r"}\end{tcolorbox}\par\medskip" "\n"
             r"{\normalsize Toán " + str(lop) + r" \,·\, Thời lượng " + str(tl) + r" phút \,·\, " + str(len(cac_dang)) + r" dạng toán}\par\vfill" "\n"
             r"{\small GV: " + tho(tt.get("giao_vien") or "") + r"}\par\vspace*{0.6cm}\end{frame}" "\n")
    # ---------- nội dung: các dạng
    dong = []
    for j, d in enumerate(cac_dang, 1):
        dm, dn = MAU[(j - 1) % len(MAU)]
        dong.append(r"\definecolor{mauMuc}{HTML}{" + dm + r"}\item[{\tikz[baseline=(n.base)]\node[rounded corners=2pt,fill=mauMuc,text=white,font=\bfseries\scriptsize,inner sep=2.5pt](n){Dạng "
                    + str(j) + "};}] " + tho(ten_dang.get(d, d)))
    f.append(r"\begin{frame}[t]{Nội dung bài học}{" + tho(ten) + r"}\hieuung\nenTrangTri" "\n"
             r"\vuaKhung{\begin{itemize}[leftmargin=3.6em,itemsep=4pt,label={}]" + "\n".join(dong) + r"\end{itemize}}" "\n\\end{frame}\n")
    # ---------- kiến thức trọng tâm (phần chung)
    if chung.strip():
        if len(chung) > 1800:
            f.append(r"\begin{frame}[t,allowframebreaks]{Kiến thức trọng tâm}{" + tho(ten) + "}\n\\small\n" + chung + "\n\\end{frame}\n")
        else:
            f.append(r"\begin{frame}[t]{Kiến thức trọng tâm}{" + tho(ten) + r"}\hieuung\nenTrangTri" "\n"
                     r"\begin{hopKT}{\setlength\caoToiDa{0.66\textheight}\vuaKhung{\kieuKT " + chung + r"}}\end{hopKT}" "\n\\end{frame}\n")
    # ---------- từng dạng
    lt = [c for l in cac_loai for c in kq["LT"].get(l, [])]
    for j, d in enumerate(cac_dang, 1):
        dm, dn = MAU[(j - 1) % len(MAU)]
        f.append(r"\datMau{" + dm + "}{" + dn + "}\n")
        cau = [c for c in lt if c["dang_key"] == d]
        tdg = ten_dang.get(d, d)
        f.append(frame_mo_dang(j, tdg, len(cau)))
        f.append(frame_pp(j, tdg, pp.get(d) or doc_pp(d)))
        for so, c in enumerate(cau[:2], 1):
            tieu = (r"\nhanViDu" if so == 1 else r"\nhanTuLam") + r"\ Dạng " + str(j) + " · " + TEN_LOAI.get(c["loai"], "")
            fr = khung_cau(so, c["loai"], tieu, tach_cau(c), c.get("dap_an") or "", True)
            fr = fr.replace(f"[t]{{Câu {so}}}", f"[t]{{Câu {so} \\textendash{{}} " + ("Ví dụ mẫu" if so == 1 else "Học sinh tự làm") + "}", 1)
            fr = fr.replace(f"{{Lời giải câu {so}", f"{{Dạng {j} \\textendash{{}} Lời giải câu {so}")
            f.append(fr)
    # ---------- kết
    so_bt = sum(len(v) for v in kq["BTVN"].values())
    f.append(r"\datMau{" + MAU[0][0] + "}{" + MAU[0][1] + "}\n")
    f.append(r"\begin{frame}[plain]\nenTrangTri\centering\vfill{\LARGE\bfseries\color{mauHT} BÀI TẬP VỀ NHÀ}\par\bigskip" "\n"
             r"{\large Làm phần \textbf{III} trên phiếu" + (f" ({so_bt} câu)" if so_bt else "") + r" \,·\, các câu luyện tập còn lại}\par\bigskip"
             r"{\normalsize\itshape Chúc các em học tốt!}\vfill\end{frame}" "\n\\end{document}\n")
    open(os.path.join(out_tex, "PhieuBeamer.tex"), "w", encoding="utf-8").write("".join(f))
    return pp
