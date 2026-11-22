# -*- coding: utf-8 -*-
"""SỔ TAY CÔNG THỨC — KIẾN THỨC TRỌNG TÂM CÁC DẠNG TOÁN (PDF in cho học sinh).

Lấy nội dung từ Kho kiến thức: phần chung của từng bài (du-lieu/kien_thuc/<bài>.tex) + phương pháp từng dạng
(du-lieu/phuong_phap/<dạng>.tex). Thầy chọn dạng cần in; xếp Chương → Bài → Dạng.
Mẫu trình bày dùng chung với phiếu bài học (mau_phieu.py); khổ in: tiết kiệm (2 cột, chữ 10) / bình thường (1 cột, chữ 12).
Chân trang: tên giáo viên · tên tài liệu · Trang x/y; cuối tài liệu có dòng "Giáo viên biên soạn".
"""
import os, re, json, shutil, time, collections
from nh_core import GOC, doc as doc_tep, ghi, cau_hinh, tai_id_map, thu_muc_xuat

KHO = {
    "tiet_kiem": {"ten": "Tiết kiệm — 2 cột, chữ 10, lề hẹp", "co": "10", "le": "left=1.0cm,right=1.0cm,top=0.9cm,bottom=1.3cm,footskip=0.6cm", "cot": 2},
    "vua": {"ten": "Vừa — 2 cột, chữ 11", "co": "11", "le": "left=1.3cm,right=1.2cm,top=1.1cm,bottom=1.4cm,footskip=0.6cm", "cot": 2},
    "binh_thuong": {"ten": "Bình thường — 1 cột, chữ 12", "co": "12", "le": "left=1.8cm,right=1.6cm,top=1.4cm,bottom=1.6cm,footskip=0.7cm", "cot": 1},
}


def _khoa_bai(b, x):
    lop = int(x["lop"])
    return (lop, b[1:2] if lop >= 10 else "", int(re.sub(r"\D", "", x["chuong"][2:]) or 0) if lop >= 10 else 0, x["so_bai"], b)


def danh_muc(lop):
    """Cây Chương → Bài → Dạng của một lớp, kèm đã có nội dung chưa."""
    import kho_kien_thuc, beamer_phieu
    id_map = tai_id_map()
    ds = [(b, x) for b, x in kho_kien_thuc.cac_bai(id_map).items() if int(x["lop"]) == int(lop)]
    ds.sort(key=lambda bx: _khoa_bai(*bx))
    chuong = collections.OrderedDict()
    for b, x in ds:
        kt = kho_kien_thuc.doc(b).strip()
        chung = beamer_phieu.tach_phuong_phap(kt, x["dang"])[0].strip() if kt else ""
        dang = [{"k": d, "ten": (id_map.get(d, {}).get("type_name") or d).strip(), "co": os.path.exists(beamer_phieu.tep_pp(d))}
                for d in sorted(x["dang"], key=lambda d: int(d.split("-")[1]))]
        c = chuong.setdefault(x["chuong"], {"ma": x["chuong"], "ten": x["ten_chuong"], "bai": []})
        c["bai"].append({"k": b, "ten": x["ten_bai"], "so": x["so_bai"], "co_kt": bool(chung), "dang": dang})
    return list(chuong.values())


def _tieu_de_bai(ten, so):
    return ten if re.match(r"(?i)\s*(bài|chủ đề)\s*\d", ten or "") else f"Bài {so}. {ten}"


def tao(cfg, in_ra=print):
    """cfg: {lop, dang:[mã dạng], bai_kt:[mã bài in kiến thức chung], mau_trinh_bay, kho, ten, giao_vien, truong, nam_hoc, ho_ten}
    → thư mục kết quả (có tex/SoTayCongThuc.tex)."""
    import kho_kien_thuc, beamer_phieu, mau_phieu
    from phieu_bai_hoc import thoat, ten_tep, chuan_kien_thuc, tieu_de_ten
    lop = int(cfg.get("lop") or 10)
    chon = set(cfg.get("dang") or [])
    bai_kt = set(cfg.get("bai_kt") or [])
    if not chon and not bai_kt:
        raise ValueError("Chưa chọn dạng / bài nào để in.")
    tt = {**cau_hinh().get("thong_tin_de", {}), **{k: v for k, v in cfg.items() if v not in (None, "")}}
    gv = (tt.get("giao_vien") or "").strip()
    kho = KHO.get(cfg.get("kho")) or KHO["tiet_kiem"]
    ten = (cfg.get("ten") or "").strip() or f"Công thức – Kiến thức trọng tâm Toán {lop}"
    cay = danh_muc(lop)
    # ---------- nội dung
    than, so_dang, thieu, chuong_dung = [], 0, [], []
    for c in cay:
        khoi_c = []
        for b in c["bai"]:
            dang = [d for d in b["dang"] if d["k"] in chon]
            in_kt = b["k"] in bai_kt and b["co_kt"]
            if not dang and not in_kt:
                continue
            k = [r"\phanCon{" + thoat(_tieu_de_bai(b["ten"], b["so"])) + "}"]
            if in_kt:
                kt = kho_kien_thuc.doc(b["k"])
                chung = beamer_phieu.tach_phuong_phap(kt, [d["k"] for d in b["dang"]])[0].strip()
                k.append(r"\begin{khungKT}" + "\n" + chuan_kien_thuc(chung) + "\n" + r"\end{khungKT}")
            for d in dang:
                so_dang += 1
                pp = beamer_phieu.doc_pp(d["k"]).strip()
                k.append(r"\dangPhieu{" + str(int(d["k"].split("-")[1])) + "}{" + thoat(d["ten"]) + "}")
                if pp:
                    k.append(r"{\setlength{\parskip}{1pt}" + chuan_kien_thuc(pp) + r"\par}")
                else:
                    thieu.append(f"{d['k']} {d['ten']}")
                    k.append(r"{\small\itshape\color{black!55}(Ghi phương pháp:)}\dongKe{" + ("2" if kho["cot"] == 2 else "3") + "}")
            khoi_c.append("\n".join(k))
        if khoi_c:
            chuong_dung.append(c["ten"])
            than.append(r"\phanPhieu[\faBookmark]{" + thoat(c["ten"].upper()) + "}\n" + "\n\n".join(khoi_c))
    if not than:
        raise ValueError("Các mục đã chọn chưa có nội dung trong Kho kiến thức.")
    # ---------- tài liệu
    id_dau = sorted(chon) or [f"{b}-1" for b in bai_kt]
    out_goc = thu_muc_xuat(ten_tep(f"{ten} - {time.strftime('%d-%m-%Y')}", 90), id_dau, "phieu")
    out = os.path.join(out_goc, "tex")
    os.makedirs(out_goc)
    src = os.path.join(GOC, "khung", "DeThiChinhThuc")
    shutil.copytree(src, out, ignore=shutil.ignore_patterns("mau_de.tex", "*.bat"))
    mau = doc_tep(os.path.join(src, "mau_de.tex"))
    for a, v in {"<<SO_GD>>": tt.get("so_gd", ""), "<<TRUONG>>": tt.get("truong", ""), "<<TEN_KY_THI>>": ten,
                 "<<NAM_HOC>>": tt.get("nam_hoc", ""), "<<MON>>": f"TOÁN – Lớp {lop}", "<<THOI_GIAN>>": "", "<<CHAN_TRANG>>": ten}.items():
        mau = mau.replace(a, thoat(v))
    mau = re.sub(r"\\documentclass\[\d+pt,", f"\\\\documentclass[{kho['co']}pt,", mau, count=1)
    mau = re.sub(r"\\usepackage\[a4paper,[^\]]*\]\{geometry\}", lambda m: "\\usepackage[a4paper," + kho["le"] + "]{geometry}", mau, count=1)
    mau = mau.replace("\\setstretch{1.1}", "\\setstretch{1.05}").replace("\\setlength{\\parskip}{6pt}", "\\setlength{\\parskip}{2pt}")
    chan = thoat(ten if len(ten) <= 60 else ten[:58] + "…")
    them = [r"%==================== SỔ TAY CÔNG THỨC ====================",
            r"\makeatletter\g@addto@macro\normalsize{\setlength{\abovedisplayskip}{3pt}\setlength{\belowdisplayskip}{3pt}"
            r"\setlength{\abovedisplayshortskip}{1pt}\setlength{\belowdisplayshortskip}{1pt}}\makeatother",
            r"\pagestyle{fancy}\fancyhf{}\renewcommand{\headrulewidth}{0pt}\renewcommand{\footrulewidth}{0.4pt}",
            r"\fancyfoot[L]{\footnotesize " + (r"GV: " + thoat(gv) if gv else "") + r"}\fancyfoot[C]{\footnotesize " + chan + r"}"
            r"\fancyfoot[R]{\footnotesize Trang \thepage/\pageref{trangCuoiPhieu}}",
            r"\fancypagestyle{plain}{\fancyhf{}\fancyfoot[L]{\footnotesize " + (r"GV: " + thoat(gv) if gv else "") +
            r"}\fancyfoot[R]{\footnotesize Trang \thepage/\pageref{trangCuoiPhieu}}}",
            mau_phieu.mo_dau(cfg.get("mau_trinh_bay"))]
    if kho["cot"] == 2:
        them += [r"\usepackage{multicol}\setlength{\columnsep}{0.6cm}\setlength{\columnseprule}{0.3pt}"]
    mau = mau.replace("\\begin{document}", "\n".join(them) + "\n\\begin{document}", 1)
    phu = f"Toán {lop} · " + (thoat(chuong_dung[0]) if len(chuong_dung) == 1 else f"{len(chuong_dung)} chương") + f" · {so_dang} dạng toán"
    dau = (r"\dauPhieuKhung{" + thoat(tt.get("truong") or "") + "}{" + thoat(tt.get("nam_hoc") or "") + "}{SỔ TAY CÔNG THỨC}{"
           + tieu_de_ten(ten, thoat) + "}{" + phu + "}{" + ("1" if cfg.get("ho_ten") else "0") + "}")
    bat, tat = ("\\begin{multicols}{2}\n", "\n\\end{multicols}") if kho["cot"] == 2 else ("", "")
    ky = (r"\par\bigskip\noindent\hfill{\small\itshape Giáo viên biên soạn: }{\small\bfseries " + thoat(gv) + r"}\par" if gv else "")
    noi = dau + "\n" + bat + "\n\n".join(than) + tat + "\n" + ky + "\n\\label{trangCuoiPhieu}\n"
    ghi(os.path.join(out, "SoTayCongThuc.tex"),
        mau_phieu.gan_bieu_tuong(mau.replace("<<CHE_DO_LOI_GIAI>>", "\\hienthiloigiai").replace("<<NOI_DUNG>>", noi)))
    ghi(os.path.join(out, "_ten_phieu.txt"), ten_tep(ten, 90))
    json.dump(cfg, open(os.path.join(out, "cau_hinh_so_tay.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    in_ra(f"SỔ TAY CÔNG THỨC: {ten} — {len(chuong_dung)} chương · {so_dang} dạng · {len(bai_kt)} bài có kiến thức chung · khổ {kho['ten']}")
    if thieu:
        in_ra(f"  ⚠ {len(thieu)} dạng chưa có phương pháp trong kho (in dòng kẻ để ghi): " + "; ".join(thieu[:6]) + (" …" if len(thieu) > 6 else ""))
    in_ra(f"THU_MUC:{os.path.relpath(out_goc, GOC)}")
    return out_goc
