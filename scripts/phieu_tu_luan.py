# -*- coding: utf-8 -*-
"""
PHIẾU HỌC TẬP TỰ LUẬN — mỗi dạng một khối 2 cột:
  trái  : VÍ DỤ MẪU (đề + lời giải đầy đủ, in sẵn cho học sinh đọc)
  phải  : TỰ LUYỆN  — câu 1, 2 tương tự ví dụ (cùng dạng, cùng mức) + câu 3 (và 4) VẬN DỤNG
Nguồn câu: câu tự luận (TL) → trả lời ngắn (TLN) → trắc nghiệm đổi sang tự luận (bỏ phương án, đáp số = phương án đúng;
chỉ nhận câu có đề tự đủ nghĩa, bỏ câu kiểu "khẳng định nào sau đây…").
"""
import re, collections
from k12word import tach_cau

UU_TIEN = {"TL": 0, "TLN": 1, "TN": 2}
THU_TU_MUC = {"N": 0, "H": 1, "V": 2, "C": 3}
TEN_MUC = {"N": "Nhận biết", "H": "Thông hiểu", "V": "Vận dụng", "C": "Vận dụng cao"}
CAM_TN = re.compile(r"nào|sau đây|khẳng định|mệnh đề|phương án|đúng\s*\?|sai\s*\?|hình vẽ|đồ thị|bảng biến thiên|"
                    r"đúng nhất|kết luận|bao nhiêu (?:khẳng|mệnh)", re.I)


def doi_tu_luan(c):
    """Câu trong kho → {de, lg, dap} dạng tự luận, hoặc None nếu không đổi được."""
    try:
        p = tach_cau(c)
    except Exception:
        return None
    de = (p.get("de") or "").strip()
    lg = (p.get("lg") or "").strip()
    if not de:
        return None
    if c["loai"] == "TL":
        return {"de": de, "lg": lg, "dap": ""}
    if c["loai"] == "TLN":
        return {"de": de, "lg": lg, "dap": (c.get("dap_an") or "").strip()}
    if c["loai"] == "TN":
        pa = p.get("pa") or []
        da = (c.get("dap_an") or "").strip()
        if len(pa) != 4 or da not in "ABCD" or not da:
            return None
        if CAM_TN.search(re.sub(r"\$[^$]*\$", " ", de)):
            return None
        de2 = re.sub(r"\s+$", "", de)
        if re.search(r"bằng\s*[:.]?$", de2):
            de2 = re.sub(r"\s*[:.]?$", "", de2) + " bao nhiêu?"
        elif re.search(r"\blà\s*[:.]?$", de2):
            de2 = re.sub(r"\s*[:.]?$", "", de2) + " gì?"
        elif not re.search(r"[.?!)}$]$", de2):
            de2 += "?"
        return {"de": de2, "lg": lg, "dap": pa["ABCD".index(da)].strip()}
    return None


def chon(ds, cac_dang, cfg, rng, khoa_noi_dung, ghi_thieu=None):
    """ds: câu đã lọc phạm vi. → ({dạng: {"vd": câu, "tu_luyen": [câu…]}}, thiếu)."""
    so_tt = int(cfg.get("so_tuong_tu") or 2)
    so_vd = int(cfg.get("so_van_dung") or 1)
    theo = collections.defaultdict(list)
    for c in ds:
        if c["loai"] not in UU_TIEN:
            continue
        t = doi_tu_luan(c)
        if not t:
            continue
        theo[c["dang_key"]].append(dict(c, _tl=t, _k=khoa_noi_dung(c)))
    da_k, kq, thieu = set(), {}, []
    for d in cac_dang:
        v = theo.get(d, [])
        rng.shuffle(v)
        v.sort(key=lambda c: ((c.get("so_lan_dung") or 0) > 0, UU_TIEN[c["loai"]]))
        moi = lambda c: c["_k"] not in da_k
        muc = lambda c: THU_TU_MUC.get(c.get("muc_chuan") or "", 1)
        # ví dụ mẫu: mức thấp, có lời giải
        ung = [c for c in v if moi(c) and c["_tl"]["lg"]]
        if not ung:
            thieu.append(f"{d}: không có câu tự luận có lời giải để làm ví dụ mẫu")
            if ghi_thieu is not None:
                ghi_thieu += [(d, "TL", "H", 1 + so_tt), (d, "TL", "V", so_vd)]
            continue
        vd = min(ung, key=muc)
        da_k.add(vd["_k"])
        # câu tương tự: cùng mức gần nhất
        tl = []
        for _ in range(so_tt):
            u = [c for c in v if moi(c) and muc(c) <= 2]
            if not u:
                break
            c = min(u, key=lambda c: abs(muc(c) - muc(vd)))
            da_k.add(c["_k"]); tl.append(dict(c, _vai="tuong_tu"))
        # vận dụng: mức V/C, cao nhất trước
        for _ in range(so_vd):
            u = [c for c in v if moi(c)]
            u_vd = [c for c in u if muc(c) >= 2]
            if not u:
                break
            c = max(u_vd or u, key=muc)
            da_k.add(c["_k"]); tl.append(dict(c, _vai="van_dung" if muc(c) >= 2 else "nang_cao"))
        if len(tl) < so_tt + so_vd:
            thieu.append(f"{d}: tự luyện cần {so_tt + so_vd} câu, kho có {len(tl)}")
            if ghi_thieu is not None:
                co_tt = sum(c["_vai"] == "tuong_tu" for c in tl); co_vd = len(tl) - co_tt
                if so_tt - co_tt > 0:
                    ghi_thieu.append((d, "TL", "H", so_tt - co_tt))
                if so_vd - co_vd > 0:
                    ghi_thieu.append((d, "TL", "V", so_vd - co_vd))
        elif any(c["_vai"] == "nang_cao" for c in tl):
            thieu.append(f"{d}: kho chưa có câu vận dụng, đã lấy câu mức cao nhất hiện có")
            if ghi_thieu is not None:
                ghi_thieu.append((d, "TL", "V", sum(c["_vai"] == "nang_cao" for c in tl)))
        kq[d] = {"vd": vd, "tu_luyen": tl}
    return kq, thieu


def khoi(kq, cac_dang, ten_dang, loi_giai, so_dong, thoat):
    """Nội dung LaTeX các khối dạng. loi_giai=True: cột phải in lời giải thay cho dòng kẻ."""
    ra, so_bai, so_vd = [], 0, 0
    for j, d in enumerate(cac_dang, 1):
        if d not in kq:
            continue
        vd, tl = kq[d]["vd"], kq[d]["tu_luyen"]
        so_vd += 1
        trai = (r"\textbf{\color{mauDang}Ví dụ " + str(so_vd) + r".}\ " + vd["_tl"]["de"] + "\n\\par\\smallskip\n" +
                r"{\color{mauPhieu}\bfseries\small Lời giải.}\ " + vd["_tl"]["lg"] +
                (("\\par\\noindent\\textbf{Đáp số:} " + vd["_tl"]["dap"]) if vd["_tl"]["dap"] and vd["loai"] != "TL" else ""))
        phai = []
        for c in tl:
            so_bai += 1
            nhan = (r"\ \nhanTL{Vận dụng}" if c["_vai"] == "van_dung" else r"\ \nhanTL{Nâng cao}" if c["_vai"] == "nang_cao" else "")
            s = r"\textbf{\color{mauDang}Bài " + str(so_bai) + r".}" + nhan + r"\ " + c["_tl"]["de"]
            if loi_giai:
                if c["_tl"]["lg"]:
                    s += "\n\\par{\\color{mauPhieu}\\bfseries\\small Lời giải.}\\ " + c["_tl"]["lg"]
                if c["_tl"]["dap"] and c["loai"] != "TL":
                    s += "\\par\\noindent\\textbf{Đáp số:} " + c["_tl"]["dap"]
            elif so_dong:
                s += r"\dongKe{" + str(so_dong + (1 if c["_vai"] != "tuong_tu" else 0)) + "}"
            phai.append(s)
        if not phai:
            phai = [r"{\small\itshape\color{black!55} Kho chưa có câu tương tự cho dạng này — giáo viên cho thêm bài:}" +
                    ("" if loi_giai else r"\dongKe{6}")]
        if loi_giai:
            ra.append(r"\dangPhieu{" + str(j) + "}{" + thoat(ten_dang.get(d, d)) + "}\n" + "\n\\par\\smallskip\n".join(phai))
            continue
        ra.append(r"\khoiDangTL{" + str(j) + "}{" + thoat(ten_dang.get(d, d)) + "}{" + trai + "}{" + "\n\\par\\medskip\n".join(phai) + "}")
    return "\n".join(ra)


MACRO = r"""
%==================== PHIẾU TỰ LUẬN: mỗi dạng trái ví dụ mẫu – phải tự luyện ====================
\newcommand{\nhanTL}[1]{\colorbox{red!75!black}{\color{white}\bfseries\scriptsize\ #1\ }}
% paracol: 2 cột song song, ngắt trang được; nền màu theo cột (paracol tự kéo 2 cột bằng nhau → mép trên, mép dưới trùng nhau)
\usepackage{paracol}\setcolumnwidth{0.49\linewidth,0.49\linewidth}\setlength{\columnsep}{0.02\linewidth}
\setlength{\columnseprule}{0.6pt}\colseprulecolor{mauPhieu!60}
\backgroundcolor{c[0](1.2mm,0.8mm)}{mauDang!6}
\backgroundcolor{c[1](1.2mm,0.8mm)}{mauPhieu!3}
\newcommand{\dauCot}[2]{\noindent\colorbox{#1}{\makebox[\dimexpr\linewidth-2\fboxsep][l]{\color{white}\bfseries\small #2}}\par\smallskip\nhoHinh\setlength{\parindent}{0pt}}
\newcommand{\khoiDangTL}[4]{\par\smallskip\needspace{5\baselineskip}%
  \noindent\colorbox{mauDang}{\makebox[\dimexpr\linewidth-2\fboxsep][l]{\color{white}{\bfseries DẠNG #1.}\ #2}}\par\nopagebreak\vspace{1pt}
  \begin{paracol}{2}
    \dauCot{mauDang!80}{VÍ DỤ MẪU}#3\par\smallskip
  \switchcolumn
    \dauCot{mauPhieu!80}{TỰ LUYỆN}#4\par\smallskip
  \end{paracol}
  \vspace{-\parskip}\noindent{\color{mauPhieu!60}\rule{\linewidth}{0.6pt}}\par}
\usepackage{multicol}\setlength{\columnsep}{0.55cm}\setlength{\columnseprule}{0.3pt}
\IfFileExists{needspace.sty}{\usepackage{needspace}}{\providecommand{\needspace}[1]{}}
\newcommand{\nhoHinh}{\tikzset{every picture/.append style={scale=0.75,transform shape}}}
\renewcommand{\immini}[3][]{{\tieudehinh #2}\par\nopagebreak{\centering #3\par}}
"""
