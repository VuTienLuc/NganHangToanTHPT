# -*- coding: utf-8 -*-
"""
PHIẾU BÀI HỌC / CHUYÊN ĐỀ / ÔN TẬP CHƯƠNG — tự lấy câu trong ngân hàng, xếp theo DẠNG.

Cấu trúc phiếu:
  Đầu phiếu (tên phiếu, lớp, chương, thời lượng, họ tên HS)
  I.  KIẾN THỨC TRỌNG TÂM  (nội dung thầy soạn / dán từ AI, lưu lại để dùng lần sau; để trống → khung có dòng kẻ
                            và danh sách các dạng kèm chỗ ghi phương pháp)
  II. LUYỆN TẬP            Phần Trắc nghiệm / Đúng–Sai / Trả lời ngắn, trong mỗi phần chia "Dạng 1, Dạng 2…"
  III. BÀI TẬP VỀ NHÀ      cùng số câu, cùng dạng, cùng mức với phần luyện tập nhưng là câu khác
Xuất: PhieuBaiHoc.tex (học sinh) + PhieuBaiHoc_LoiGiai.tex (lời giải + bảng đáp án), in tiết kiệm (chữ 10/11, 2 cột),
chân trang "GV: … | tên phiếu | Trang x/y".

  python3 scripts/phieu_bai_hoc.py cau_hinh_phieu.json [--bien-dich]
cau_hinh_phieu.json: {"pham_vi": ["0D1?1", "0D1?2"] (bài) hoặc ["0D1"] (cả chương), "dang": [...] (tuỳ chọn),
  "ten": "...", "loai_phieu": "bai_hoc|chuyen_de|on_tap_chuong", "thoi_luong": 45|90,
  "so_cau": {"TN": 8, "DS": 2, "TLN": 2}, "so_cau_btvn": {...} (mặc định = so_cau), "kien_thuc": "LaTeX…",
  "co_chu": 11, "hai_cot": true, "giao_vien": "Vũ Tiến Lực", "truong": "...", "nam_hoc": "..."}
"""
import os, sys, re, json, time, random, shutil, collections, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nh_core import GOC, doc, ghi, cau_hinh, tai_id_map

CAC_LOAI = ["TN", "DS", "TLN"]
TEN_PHAN = {"TN": "Trắc nghiệm nhiều phương án lựa chọn", "DS": "Trắc nghiệm đúng sai", "TLN": "Trả lời ngắn"}
MOI_TRUONG = {"TN": ("ex", "ans", "Ans"), "DS": ("ex", "ansbook", "Ansbook"), "TLN": ("bt", "ansbt", "Ansbook")}
THU_TU_MUC = {"N": 0, "H": 1, "V": 2, "C": 3}
MAC_DINH_SO_CAU = {45: {"TN": 8, "DS": 2, "TLN": 2}, 90: {"TN": 12, "DS": 4, "TLN": 6}}
P_KIEN_THUC = os.path.join(GOC, "du-lieu", "kien_thuc")

def thoat(v):
    return re.sub(r"(?<!\\)([&%#_])", r"\\\1", v or "")

def ten_tep(s, n=60):
    s = unicodedata.normalize("NFC", s or "")
    s = re.sub(r'[\\/:*?"<>|\n\r\t]+', " ", s)
    return re.sub(r"\s+", " ", s).strip(" .")[:n] or "Phieu"

def khoa_kien_thuc(pham_vi):
    return re.sub(r"[^0-9A-Za-z]+", "_", "+".join(sorted(pham_vi)))

def doc_kien_thuc(pham_vi):
    p = os.path.join(P_KIEN_THUC, khoa_kien_thuc(pham_vi) + ".tex")
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""

def luu_kien_thuc(pham_vi, noi_dung):
    os.makedirs(P_KIEN_THUC, exist_ok=True)
    p = os.path.join(P_KIEN_THUC, khoa_kien_thuc(pham_vi) + ".tex")
    if (noi_dung or "").strip():
        open(p, "w", encoding="utf-8").write(noi_dung.strip() + "\n")

def hop_le(c):
    da = c.get("dap_an") or ""
    return {"TN": len(da) == 1, "DS": len(da) == 4, "TLN": bool(da)}.get(c["loai"], False)

def thuoc(c, pham_vi):
    k = c.get("dang_key") or ""
    for p in pham_vi:
        if "?" in p and k.startswith(p + "-"):           # bài: 0D1?1
            return True
        if "?" not in p and k.startswith(p + "?"):       # chương: 0D1
            return True
    return False

def khoa_noi_dung(c):
    """Khoá nội dung đề (bỏ mã, khoảng trắng, lời giải, phương án) — để không lấy 2 câu trùng đề vào cùng một phiếu."""
    t = c.get("noi_dung") or ""
    t = re.sub(r"%[^\n]*", "", t)
    t = re.split(r"\\(?:choice|choiceTF|loigiai|shortans)\b", t)[0]
    t = re.sub(r"\\begin\{(?:ex|bt)\}", "", t)
    return re.sub(r"[\s{}\\$~.,;:]+", "", t).lower()


def chon_cau(cau_hinh_phieu, rng):
    """→ (dạng theo thứ tự, {LT|BTVN: {loai: [câu…]}}, thiếu)."""
    pv, chon_dang = cau_hinh_phieu["pham_vi"], set(cau_hinh_phieu.get("dang") or [])
    ds = []
    for l in open(os.path.join(GOC, "du-lieu", "chi_muc.jsonl"), encoding="utf-8"):
        c = json.loads(l)
        if c["loai"] in CAC_LOAI and thuoc(c, pv) and hop_le(c) and (not chon_dang or c["dang_key"] in chon_dang):
            ds.append(c)
    def khoa_dang(k):
        m = re.match(r"(\d)([A-Z])(\d+)\?(\d+)-(\d+)", k)
        return tuple(int(x) if x.isdigit() else x for x in m.groups()) if m else (k,)
    cac_dang = sorted({c["dang_key"] for c in ds}, key=khoa_dang)
    theo = collections.defaultdict(list)                  # (loai, dạng) → câu (chưa dùng trước, mức tăng dần)
    for c in ds:
        theo[(c["loai"], c["dang_key"])].append(c)
    for v in theo.values():
        rng.shuffle(v)
        v.sort(key=lambda c: ((c.get("so_lan_dung") or 0) > 0, THU_TU_MUC.get(c.get("muc_chuan") or "", 1)))
    da_lay, kq, thieu = set(), {"LT": {}, "BTVN": {}}, []
    for c in ds:
        c["_k"] = khoa_noi_dung(c)
    da_nd = set()
    moi = lambda c: c["ma"] not in da_lay and c["_k"] not in da_nd
    def lay(c):
        da_lay.add(c["ma"]); da_nd.add(c["_k"])
    so = {"LT": cau_hinh_phieu["so_cau"], "BTVN": cau_hinh_phieu.get("so_cau_btvn") or cau_hinh_phieu["so_cau"]}
    # 0) bổ sung câu VẬN DỤNG / VẬN DỤNG CAO (nếu chọn) — mỗi phần (luyện tập, về nhà) một bộ riêng, rải đều các dạng
    nc = cau_hinh_phieu.get("nang_cao") or {}
    for muc_phan in ("LT", "BTVN"):
        kq[muc_phan]["VD"] = []
    for muc_cau, ten_muc in (("V", "Vận dụng"), ("C", "Vận dụng cao")):
        can = int(nc.get(muc_cau) or 0)
        if can <= 0:
            continue
        nhom = collections.defaultdict(list)
        for c in ds:
            if (c.get("muc_chuan") or "") == muc_cau:
                nhom[c["dang_key"]].append(c)
        for v in nhom.values():
            rng.shuffle(v); v.sort(key=lambda c: (c.get("so_lan_dung") or 0) > 0)
        for muc_phan, ten_phan in (("LT", "Luyện tập"), ("BTVN", "Bài tập về nhà")):
            lay_duoc, vong = [], 0
            while len(lay_duoc) < can:
                con = [d for d in cac_dang if any(moi(c) for c in nhom.get(d, []))]
                if not con:
                    break
                d = con[vong % len(con)]; vong += 1
                c = next(c for c in nhom[d] if moi(c))
                lay(c); lay_duoc.append(dict(c, _muc_nc=ten_muc))
            if len(lay_duoc) < can:
                thieu.append(f"{ten_phan} – {ten_muc}: cần {can}, kho chỉ có {len(lay_duoc)} câu phù hợp")
            kq[muc_phan]["VD"] += sorted(lay_duoc, key=lambda c: (CAC_LOAI.index(c["loai"]), cac_dang.index(c["dang_key"])))
    for loai in CAC_LOAI:
        dang_co = [d for d in cac_dang if theo.get((loai, d))]
        # 1) luyện tập: rải đều các dạng (vòng tròn), mỗi dạng lấy dần từ mức thấp đến cao
        lt, vong = [], 0
        while len(lt) < int(so["LT"].get(loai) or 0) and dang_co:
            con = [d for d in dang_co if any(moi(c) for c in theo[(loai, d)])]
            if not con:
                break
            d = con[vong % len(con)]; vong += 1
            c = next(c for c in theo[(loai, d)] if moi(c))
            lay(c); lt.append(c)
        # 2) bài tập về nhà: cùng dạng, gần cùng mức với từng câu luyện tập (câu khác)
        btvn = []
        mau = lt * (1 + int(so["BTVN"].get(loai) or 0) // max(1, len(lt))) if lt else []
        for m in mau:
            if len(btvn) >= int(so["BTVN"].get(loai) or 0):
                break
            ung = [c for c in theo[(loai, m["dang_key"])] if moi(c)]
            if not ung:
                ung = [c for d in dang_co for c in theo[(loai, d)] if moi(c)]
            if not ung:
                break
            muc = THU_TU_MUC.get(m.get("muc_chuan") or "", 1)
            c = min(ung, key=lambda x: abs(THU_TU_MUC.get(x.get("muc_chuan") or "", 1) - muc))
            lay(c); btvn.append(c)
        sap = lambda v: sorted(v, key=lambda c: (cac_dang.index(c["dang_key"]), THU_TU_MUC.get(c.get("muc_chuan") or "", 1)))
        kq["LT"][loai], kq["BTVN"][loai] = sap(lt), sap(btvn)
        for phan, v in (("Luyện tập", lt), ("Bài tập về nhà", btvn)):
            can = int(so["LT" if phan == "Luyện tập" else "BTVN"].get(loai) or 0)
            if len(v) < can:
                thieu.append(f"{phan} – {TEN_PHAN[loai]}: cần {can}, kho chỉ có {len(v)} câu phù hợp")
    return cac_dang, kq, thieu

def tao(cfg, in_ra=print):
    CH = cau_hinh()
    tt = {**CH.get("thong_tin_de", {}), **{k: v for k, v in cfg.items() if v not in (None, "")}}
    id_map = tai_id_map()
    rng = random.Random(cfg.get("seed") or time.time())
    tl = int(cfg.get("thoi_luong") or 45)
    cfg.setdefault("so_cau", MAC_DINH_SO_CAU.get(tl, MAC_DINH_SO_CAU[45]))
    tu_luan = cfg.get("kieu_cau") == "tu_luan"
    if tu_luan:
        import phieu_tu_luan
        cfg["hai_cot"] = False          # khối 2 cột tự dựng, không dùng multicols
        ds = [c for c in map(json.loads, open(os.path.join(GOC, "du-lieu", "chi_muc.jsonl"), encoding="utf-8"))
              if c["loai"] in ("TL", "TLN", "TN") and thuoc(c, cfg["pham_vi"]) and (c["loai"] == "TL" or hop_le(c))
              and (not cfg.get("dang") or c["dang_key"] in cfg["dang"])]
        def khoa_dang(k):
            m = re.match(r"(\d)([A-Z])(\d+)\?(\d+)-(\d+)", k or "")
            return tuple(int(x) if x.isdigit() else x for x in m.groups()) if m else (k or "",)
        cac_dang = sorted({c["dang_key"] for c in ds if c.get("dang_key")}, key=khoa_dang)
        kq_tl, thieu = phieu_tu_luan.chon(ds, cac_dang, cfg, rng, khoa_noi_dung)
        cac_dang = [d for d in cac_dang if d in kq_tl]
        if not kq_tl:
            raise RuntimeError("Không tìm thấy câu tự luận nào (có lời giải) trong phạm vi đã chọn.")
        kq = {"LT": {l: [] for l in CAC_LOAI}, "BTVN": {l: [] for l in CAC_LOAI}}
    else:
        cac_dang, kq, thieu = chon_cau(cfg, rng)
    if not tu_luan and not any(kq["LT"][l] for l in CAC_LOAI):
        raise RuntimeError("Không tìm thấy câu nào trong phạm vi đã chọn.")
    loai_phieu = cfg.get("loai_phieu") or ("on_tap_chuong" if all("?" not in p for p in cfg["pham_vi"])
                                           else "bai_hoc" if len(cfg["pham_vi"]) == 1 else "chuyen_de")
    nhan = {"bai_hoc": "PHIẾU BÀI HỌC", "chuyen_de": "PHIẾU CHUYÊN ĐỀ", "on_tap_chuong": "PHIẾU ÔN TẬP CHƯƠNG"}[loai_phieu]
    vd = id_map.get(cac_dang[0], {}) if cac_dang else {}
    ten = cfg.get("ten") or (vd.get("chap_name") if loai_phieu == "on_tap_chuong" else vd.get("lesson_name")) or "Bài học"
    lop = 10 + int(cac_dang[0][0]) if cac_dang else ""
    gv = tt.get("giao_vien") or "Vũ Tiến Lực"
    # ---------- thư mục ra
    ngay = time.strftime("%d-%m-%Y")
    goc_ten = ten_tep(f"{nhan.title()}{' Tự Luận' if tu_luan else ''} - {ten} - {ngay}", 90)
    out_goc, i = os.path.join(GOC, "de-da-ra", goc_ten), 2
    while os.path.exists(out_goc):
        out_goc = os.path.join(GOC, "de-da-ra", f"{goc_ten} ({i})"); i += 1
    out = os.path.join(out_goc, "tex")
    os.makedirs(out_goc)
    src = os.path.join(GOC, "khung", "DeThiChinhThuc")
    shutil.copytree(src, out, ignore=shutil.ignore_patterns("mau_de.tex", "*.bat"))
    mau = doc(os.path.join(src, "mau_de.tex"))
    for k, v in {"<<SO_GD>>": tt.get("so_gd", ""), "<<TRUONG>>": tt.get("truong", ""), "<<TEN_KY_THI>>": ten,
                 "<<NAM_HOC>>": tt.get("nam_hoc", ""), "<<MON>>": f"TOÁN – Lớp {lop}", "<<THOI_GIAN>>": f"{tl} phút",
                 "<<CHAN_TRANG>>": ten}.items():
        mau = mau.replace(k, thoat(v))
    # ---------- in tiết kiệm, đẹp mắt
    co = str(int(cfg.get("co_chu") or 11)); co = co if co in ("10", "11", "12") else "11"
    hai_cot = bool(cfg.get("hai_cot", True))
    mau = re.sub(r"\\documentclass\[\d+pt,", f"\\\\documentclass[{co}pt,", mau, count=1)
    mau = re.sub(r"\\usepackage\[a4paper,[^\]]*\]\{geometry\}",
                 lambda m: "\\usepackage[a4paper,left=1.1cm,right=1.0cm,top=0.9cm,bottom=1.3cm,footskip=0.6cm]{geometry}", mau, count=1)
    mau = mau.replace("\\setstretch{1.1}", "\\setstretch{1.0}").replace("\\setlength{\\parskip}{6pt}", "\\setlength{\\parskip}{1pt}")
    them = [r"%==================== PHIẾU BÀI HỌC ====================",
            r"\makeatletter\g@addto@macro\normalsize{\setlength{\abovedisplayskip}{2pt}\setlength{\belowdisplayskip}{2pt}"
            r"\setlength{\abovedisplayshortskip}{1pt}\setlength{\belowdisplayshortskip}{1pt}}\makeatother",
            r"\definecolor{mauPhieu}{RGB}{21,67,140}\definecolor{mauDang}{RGB}{0,121,107}",
            r"\newcommand{\phanPhieu}[1]{\par\medskip\noindent{\color{mauPhieu}\rule[0.3ex]{0.6em}{0.6em}\ \large\bfseries #1}\par"
            r"\vspace{-2pt}\noindent{\color{mauPhieu}\rule{\linewidth}{0.6pt}}\par\smallskip}",
            r"\newcommand{\phanCon}[1]{\par\smallskip\noindent{\bfseries\color{mauPhieu}#1}\par}",
            r"\newcommand{\dangPhieu}[2]{\par\smallskip\noindent{\colorbox{mauDang!12}{\color{mauDang}\bfseries\small\ Dạng #1\ }\ \textit{#2}}\par\nopagebreak}",
            r"\newcommand{\nhanMuc}[2]{\par\smallskip\noindent{\colorbox{red!75!black}{\color{white}\bfseries\scriptsize\ #1\ }\ {\scriptsize\itshape\color{black!60}Dạng #2}}\par\nopagebreak}",
            r"\newcommand{\dongKe}[1]{\par\foreach \i in {1,...,#1}{\noindent\makebox[\linewidth]{\color{black!35}\dotfill}\par}}",
            r"\pagestyle{fancy}\fancyhf{}\renewcommand{\headrulewidth}{0pt}\renewcommand{\footrulewidth}{0.4pt}",
            r"\fancyfoot[L]{\footnotesize GV: " + thoat(gv) + r"}\fancyfoot[C]{\footnotesize " + thoat(f"{nhan.title()}: {ten}") + r"}"
            r"\fancyfoot[R]{\footnotesize Trang \thepage/\pageref{trangCuoiPhieu}}",
            r"\fancypagestyle{plain}{\fancyhf{}\fancyfoot[L]{\footnotesize GV: " + thoat(gv) + r"}\fancyfoot[R]{\footnotesize Trang \thepage/\pageref{trangCuoiPhieu}}}"]
    if hai_cot:
        them += [r"\usepackage{multicol}\setlength{\columnsep}{0.55cm}\setlength{\columnseprule}{0.3pt}",
                 r"\tikzset{every picture/.append style={scale=0.75,transform shape}}",
                 r"\renewcommand{\immini}[3][]{{\tieudehinh #2}\par\nopagebreak{\centering #3\par}}"]
    mau = mau.replace("\\begin{document}", "\n".join(them) + "\n\\begin{document}", 1)
    # ---------- đầu phiếu
    chuong = (vd.get("chap_name") or "").strip()
    def dau_phieu(tieu_de, ho_ten=True):
        return (r"\begin{tcolorbox}[colback=mauPhieu!4,colframe=mauPhieu,boxrule=0.8pt,arc=2mm,left=3mm,right=3mm,top=1.5mm,bottom=1.5mm]" "\n"
           r"{\small " + thoat(tt.get("truong") or "") + r"\hfill " + thoat(tt.get("nam_hoc") or "") + r"}\par\smallskip" "\n"
           r"\begin{center}{\Large\bfseries\color{mauPhieu} " + tieu_de + r"}\\[2pt]{\large\bfseries " + thoat(ten.upper()) + r"}\\[2pt]"
           r"{\small Toán " + str(lop) + (" · " + thoat(chuong) if chuong and loai_phieu != "on_tap_chuong" else "") +
           r" · Thời lượng: " + str(tl) + r" phút}\end{center}" "\n" +
           (r"{\small Họ và tên: \makebox[6cm]{\dotfill}\hfill Lớp: \makebox[1.8cm]{\dotfill}\hfill Ngày: \makebox[2.4cm]{\dotfill}}" "\n" if ho_ten else "") +
           r"\end{tcolorbox}")
    dau = dau_phieu(nhan)
    # ---------- I. kiến thức trọng tâm
    kt = (cfg.get("kien_thuc") or "").strip()
    if kt:
        luu_kien_thuc(cfg["pham_vi"], kt)
    # in_san: in sẵn nội dung đã soạn; dong_trong: khung dòng kẻ để học sinh tự ghi (nội dung soạn vẫn dùng cho Beamer)
    in_san = (cfg.get("kien_thuc_in") or "in_san") != "dong_trong"
    if kt and in_san:
        kien = r"\begin{tcolorbox}[colback=white,colframe=mauPhieu!60,boxrule=0.5pt,arc=1mm,left=2mm,right=2mm,top=1mm,bottom=1mm,breakable]" + "\n" + kt + "\n\\end{tcolorbox}"
    else:
        dong = [r"\par\smallskip{\small\bfseries Kiến thức cần nhớ (định nghĩa, tính chất, công thức):}\dongKe{" + ("6" if tl >= 90 else "4") + "}"]
        so_ke = "3" if tl >= 90 else "2"
        for j, d in enumerate(cac_dang, 1):
            dong.append(r"\dangPhieu{" + str(j) + "}{" + thoat((id_map.get(d, {}).get("type_name") or d).strip()) + r"}" "\n"
                        r"{\small Phương pháp:}\dongKe{" + so_ke + "}")
        kien = (r"\begin{tcolorbox}[colback=white,colframe=mauPhieu!60,boxrule=0.5pt,arc=1mm,left=2mm,right=2mm,top=1mm,bottom=1mm,breakable]"
                "\n{\\small\\itshape Học sinh tự ghi: tóm tắt kiến thức và phương pháp giải từng dạng.}\n" + "\n".join(dong) + "\n\\end{tcolorbox}")
    if tu_luan:
        return _ghi_tu_luan(locals())
    # ---------- II, III: câu hỏi theo phần, chia dạng
    so_dang = {d: j for j, d in enumerate(cac_dang, 1)}
    bang = []
    def khoi_phan(muc, nhan_muc):
        k = [r"\phanPhieu{" + nhan_muc + "}"]
        so_phan = 0
        for loai in CAC_LOAI:
            v = kq[muc][loai]
            if not v:
                continue
            so_phan += 1
            ct, sf, tm = MOI_TRUONG[loai]
            tep = f"{muc}_{loai}"
            k.append(r"\phanCon{" + f"{so_phan}. {TEN_PHAN[loai]} ({len(v)} câu)" + "}")
            k.append(f"\\setcounter{{{ct}}}{{0}}")
            k.append(f"\\Opensolutionfile{{{sf}}}[{tm}/{tep}]")
            dang_cu = None
            for c in v:
                if c["dang_key"] != dang_cu:
                    dang_cu = c["dang_key"]
                    k.append(r"\dangPhieu{" + str(so_dang[dang_cu]) + "}{" +
                             thoat((id_map.get(dang_cu, {}).get("type_name") or dang_cu).strip()) + "}")
                k.append(c["noi_dung"])
            k.append(f"\\Closesolutionfile{{{sf}}}")
            bang.append((nhan_muc, so_phan, TEN_PHAN[loai], tm, tep))
        vd = kq[muc].get("VD") or []
        if vd:
            so_phan += 1
            k.append(r"\phanCon{" + f"{so_phan}. Vận dụng – Vận dụng cao ({len(vd)} câu)" + "}")
            for loai in CAC_LOAI:
                v = [c for c in vd if c["loai"] == loai]
                if not v:
                    continue
                ct, sf, tm = MOI_TRUONG[loai]
                tep = f"{muc}_VD_{loai}"
                k.append(r"\par\noindent{\small\itshape " + TEN_PHAN[loai] + r"}\par")
                k.append(f"\\setcounter{{{ct}}}{{0}}")
                k.append(f"\\Opensolutionfile{{{sf}}}[{tm}/{tep}]")
                for c in v:
                    k.append(r"\nhanMuc{" + c["_muc_nc"] + "}{" + str(so_dang[c["dang_key"]]) + "}")
                    k.append(c["noi_dung"])
                k.append(f"\\Closesolutionfile{{{sf}}}")
                bang.append((nhan_muc, so_phan, "Vận dụng – VDC · " + TEN_PHAN[loai], tm, tep))
        return "\n".join(k)
    lt, btvn = khoi_phan("LT", "II. LUYỆN TẬP"), khoi_phan("BTVN", "III. BÀI TẬP VỀ NHÀ")
    bat, tat = ("\\begin{multicols}{2}\n", "\n\\end{multicols}") if hai_cot else ("", "")
    than = (dau + "\n" + r"\phanPhieu{I. KIẾN THỨC TRỌNG TÂM}" + "\n" + kien + "\n" + bat + lt + "\n\n" + btvn + tat)
    # File lời giải riêng: đầu "LỜI GIẢI", bảng đáp án ngay đầu, rồi lời giải chi tiết II, III (không có phần I, không dòng kẻ)
    het = "\n\\par\\bigskip\\begin{center}{\\small\\itshape --- Hết ---}\\end{center}\\label{trangCuoiPhieu}\n"
    chan_goc = thoat(f"{nhan.title()}: {ten}")

    def bang_dap_an(cac_muc):
        d = [r"\phanPhieu{BẢNG ĐÁP ÁN}"]
        cu = None
        for nhan_muc, so_phan, tp, tm, tep in bang:
            if nhan_muc not in cac_muc:
                continue
            if nhan_muc != cu:
                cu = nhan_muc; d.append(r"\phanCon{" + nhan_muc + "}")
            d.append(f"\\par\\noindent\\textbf{{{so_phan}. {tp}}}\\par\n\\begin{{flushleft}}\n"
                     f"\\IfFileExists{{{tm}/{tep}.tex}}{{\\input{{{tm}/{tep}}}}}{{(biên dịch lại để hiện đáp án)}}\n\\end{{flushleft}}")
        return "\n".join(d)

    khong_kt = (cfg.get("kien_thuc_in") or "") == "khong"     # bỏ hẳn mục I để tiết kiệm giấy

    def danh_so(t):
        """Không có mục I → đánh số lại: I. LUYỆN TẬP, II. BÀI TẬP VỀ NHÀ."""
        if not khong_kt:
            return t
        return t.replace("III. BÀI TẬP VỀ NHÀ", "II. BÀI TẬP VỀ NHÀ").replace("II. LUYỆN TẬP", "I. LUYỆN TẬP")

    def viet(tep, tieu_de, chan, noi, cac_muc, co_kien_thuc):
        co_kien_thuc = co_kien_thuc and not khong_kt
        """Ghi 1 cặp file: <tep>.tex (câu hỏi, phát HS) và <tep>_LoiGiai.tex (bảng đáp án + lời giải chi tiết)."""
        m = mau.replace(chan_goc, thoat(chan))
        hs = dau_phieu(tieu_de) + "\n"
        if co_kien_thuc:
            hs += r"\phanPhieu{I. KIẾN THỨC TRỌNG TÂM}" + "\n" + kien + "\n"
        hs += bat + noi + tat
        ghi(os.path.join(out, tep + ".tex"), m.replace("<<CHE_DO_LOI_GIAI>>", "\\anloigiai").replace("<<NOI_DUNG>>", danh_so(hs) + het))
        m2 = mau.replace(chan_goc, thoat("Lời giải " + chan[:1].lower() + chan[1:]))
        lg = (dau_phieu("LỜI GIẢI " + tieu_de, ho_ten=False) + "\n" + bang_dap_an(cac_muc) + "\n" +
              r"\phanPhieu{LỜI GIẢI CHI TIẾT}" + "\n" + bat + noi + tat)
        ghi(os.path.join(out, tep + "_LoiGiai.tex"), m2.replace("<<CHE_DO_LOI_GIAI>>", "\\hienthiloigiai").replace("<<NOI_DUNG>>", danh_so(lg) + het))

    # 1) Phiếu đầy đủ (I + II + III); 2) Phiếu trên lớp (I + II); 3) Phiếu về nhà (III) — mỗi phiếu có file lời giải riêng
    viet("PhieuBaiHoc", nhan, f"{nhan.title()}: {ten}", lt + "\n\n" + btvn, ("II. LUYỆN TẬP", "III. BÀI TẬP VỀ NHÀ"), True)
    viet("PhieuTrenLop", nhan + " – TRÊN LỚP", f"{nhan.title()} (trên lớp): {ten}", lt, ("II. LUYỆN TẬP",), True)
    btvn_rieng = btvn.replace(r"\phanPhieu{III. BÀI TẬP VỀ NHÀ}", r"\phanPhieu{BÀI TẬP VỀ NHÀ}", 1)
    viet("PhieuVeNha", "BÀI TẬP VỀ NHÀ", f"Bài tập về nhà: {ten}", btvn_rieng, ("III. BÀI TẬP VỀ NHÀ",), False)
    # Beamer trình chiếu kèm phiếu: phương pháp từng dạng + câu 1 (ví dụ) + câu 2 (HS tự làm) + lời giải
    if cfg.get("beamer", True):
        import beamer_phieu
        beamer_phieu.tao(out, ten, nhan, dict(tt, giao_vien=gv), lop, tl, cac_dang,
                         {d: (id_map.get(d, {}).get("type_name") or d).strip() for d in cac_dang}, kq, kt,
                         phan_ve_nha="II" if khong_kt else "III")
    ghi(os.path.join(out, "_ten_phieu.txt"), ten_tep(f"{nhan.title()} - {ten}", 90))
    json.dump(cfg, open(os.path.join(out, "cau_hinh_phieu.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    so_lt = {l: len(kq["LT"][l]) for l in CAC_LOAI}; so_bt = {l: len(kq["BTVN"][l]) for l in CAC_LOAI}
    in_ra(f"{nhan}: {ten} — {len(cac_dang)} dạng · Luyện tập TN {so_lt['TN']}, ĐS {so_lt['DS']}, TLN {so_lt['TLN']}"
          f" · Bài tập về nhà TN {so_bt['TN']}, ĐS {so_bt['DS']}, TLN {so_bt['TLN']}")
    if kq["LT"].get("VD") or kq["BTVN"].get("VD"):
        in_ra(f"  + Vận dụng – vận dụng cao: luyện tập {len(kq['LT']['VD'])} câu, về nhà {len(kq['BTVN']['VD'])} câu")
    for t in thieu:
        in_ra("  ⚠ " + t)
    rel = os.path.relpath(out_goc, GOC)
    in_ra(f"THU_MUC:{rel}")
    return out_goc

def _ghi_tu_luan(L):
    import phieu_tu_luan
    cfg, out, out_goc, mau, kien, nhan, ten, cac_dang = (L[k] for k in ("cfg", "out", "out_goc", "mau", "kien", "nhan", "ten", "cac_dang"))
    kq_tl, thieu, id_map, dau_phieu, in_ra, tl = (L[k] for k in ("kq_tl", "thieu", "id_map", "dau_phieu", "in_ra", "tl"))
    ten_dang = {d: (id_map.get(d, {}).get("type_name") or d).strip() for d in cac_dang}
    mau = mau.replace("\\begin{document}", phieu_tu_luan.MACRO + "\\begin{document}", 1)
    kt_in = cfg.get("kien_thuc_in") or "in_san"
    so_dong = int(cfg.get("so_dong_lam_bai", 2))
    het = "\n\\par\\bigskip\\begin{center}{\\small\\itshape --- Hết ---}\\end{center}\\label{trangCuoiPhieu}\n"
    muc_kt = "" if kt_in == "khong" else (r"\phanPhieu{I. KIẾN THỨC TRỌNG TÂM}" + "\n" + kien + "\n")
    tieu_muc = r"\phanPhieu{" + ("I" if kt_in == "khong" else "II") + r". CÁC DẠNG TOÁN – VÍ DỤ MẪU VÀ TỰ LUYỆN}" + "\n"
    hs = dau_phieu(nhan + " – TỰ LUẬN") + "\n" + muc_kt + tieu_muc + phieu_tu_luan.khoi(kq_tl, cac_dang, ten_dang, False, so_dong, thoat)
    lg = (dau_phieu("LỜI GIẢI " + nhan + " – TỰ LUẬN", ho_ten=False) + "\n" +
          r"\phanPhieu{LỜI GIẢI CÁC BÀI TỰ LUYỆN}" + "\n{\\small\\itshape (Ví dụ mẫu đã có lời giải trên phiếu học sinh.)}\n" +
          "\\begin{multicols}{2}\\nhoHinh\n" + phieu_tu_luan.khoi(kq_tl, cac_dang, ten_dang, True, 0, thoat) + "\n\\end{multicols}")
    chan_goc = thoat(f"{nhan.title()}: {ten}")
    ghi(os.path.join(out, "PhieuBaiHoc.tex"), mau.replace("<<CHE_DO_LOI_GIAI>>", "\\hienthiloigiai").replace("<<NOI_DUNG>>", hs + het))
    ghi(os.path.join(out, "PhieuBaiHoc_LoiGiai.tex"),
        mau.replace(chan_goc, thoat(f"Lời giải {nhan.lower()}: {ten}")).replace("<<CHE_DO_LOI_GIAI>>", "\\hienthiloigiai").replace("<<NOI_DUNG>>", lg + het))
    ghi(os.path.join(out, "_ten_phieu.txt"), ten_tep(f"{nhan.title()} Tự Luận - {ten}", 90))
    json.dump(cfg, open(os.path.join(out, "cau_hinh_phieu.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if cfg.get("beamer", True):            # Beamer cùng loại phiếu: phương pháp → ví dụ mẫu → từng bài tự luyện (đề, lời giải)
        import beamer_phieu
        ctd, so_vd, so_bai = {}, 0, 0
        for d in cac_dang:
            if d not in kq_tl:
                continue
            ds_m = []
            vd = kq_tl[d]["vd"]; so_vd += 1
            def muc(c, tieu, nhan):
                t = c["_tl"]
                return {"tieu": tieu, "nhan": nhan, "loai": "TL" if c["loai"] == "TL" or not t["dap"] else "TLN",
                        "p": {"de": t["de"], "lg": t["lg"], "pa": None, "y_giai": None}, "dap": t["dap"]}
            ds_m.append(muc(vd, f"Ví dụ {so_vd}", r"\nhanViDu"))
            for c in kq_tl[d]["tu_luyen"]:
                so_bai += 1
                ds_m.append(muc(c, f"Bài {so_bai} \\textendash{{}} " + ("Vận dụng" if c["_vai"] == "van_dung" else "Học sinh tự làm"),
                                r"\nhanTuLam"))
            ctd[d] = ds_m
        beamer_phieu.tao(out, ten, nhan + " – TỰ LUẬN", dict(L["tt"], giao_vien=L["gv"]), L["lop"], tl, cac_dang, ten_dang,
                         {"LT": {}, "BTVN": {}}, L["kt"], cau_theo_dang=ctd,
                         loi_ket=r"Hoàn thành các bài \textbf{tự luyện} còn lại trên phiếu")
    n_tl = sum(len(v["tu_luyen"]) for v in kq_tl.values())
    in_ra(f"{nhan} – TỰ LUẬN: {ten} — {len(kq_tl)} dạng · {len(kq_tl)} ví dụ mẫu · {n_tl} bài tự luyện")
    for t in thieu:
        in_ra("  ⚠ " + t)
    in_ra(f"THU_MUC:{os.path.relpath(out_goc, GOC)}")
    return out_goc


if __name__ == "__main__":
    cfg = json.load(open(sys.argv[1], encoding="utf-8"))
    o = tao(cfg)
    if "--bien-dich" in sys.argv:
        from nh_core import bien_dich_thu_muc
        bien_dich_thu_muc(o)
