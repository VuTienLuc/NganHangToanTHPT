# -*- coding: utf-8 -*-
"""
BỘ ĐỀ ÔN TẬP NHIỀU LẦN — nhập liên tiếp các ma trận (Lần 1, Lần 2, …; lần sau thêm/bớt/sửa so với lần trước),
rồi xuất một lượt:
  • mỗi lần một thư mục con, mã đề nối tiếp (101–104, 105–108, …);
  • không lặp câu giữa các lần (tùy chọn);
  • gộp thành 1 quyển "Bộ đề – Câu hỏi.pdf" và "Bộ đề – Lời giải.pdf" (có trang bìa + mục lục), nếu có pdflatex.
CLI: python3 scripts/bo_de.py bo.json [--bien-dich]
"""
import os, re, sys, json, time, subprocess, datetime, shutil
from nh_core import GOC, tim_pdflatex, bien_dich_thu_muc, ten_khong_dau, thu_muc_xuat

SCRIPTS = os.path.dirname(os.path.abspath(__file__))


def ten_tm(s):
    s = re.sub(r'[\\/:*?"<>|\n\r\t]+', " ", s or "")
    return re.sub(r"\s+", " ", s).strip(" .")[:80] or "Bo de"


def tong_cau(mt):
    return sum(y.get("so", 0) for p in mt.get("phan", []) for y in p.get("yeu_cau", []))


def chay(cfg, in_ra=print, bien_dich=False):
    lan = [l for l in cfg.get("cac_lan", []) if tong_cau(l.get("ma_tran", {}))]
    if not lan:
        raise ValueError("Bộ đề chưa có lần nào có số câu.")
    ten = ten_tm(cfg.get("ten") or "Bộ đề ôn tập")
    ngay = datetime.date.today().strftime("%d-%m-%Y")
    khoa = [k for l in lan for p in l["ma_tran"].get("phan", []) for y in p.get("yeu_cau", []) for k in re.split(r"[+,;]", str(y.get("dang") or ""))]
    out = thu_muc_xuat(ten, khoa, "de")                  # de-da-ra/Lớp N/…/<ngày> <tên>
    os.makedirs(out)
    ma = int(cfg.get("ma_de_bat_dau") or 101)
    khong_lap = cfg.get("khong_lap", True)
    tranh, muc_luc = set(), []
    for i, l in enumerate(lan, 1):
        mt = dict(l["ma_tran"])
        nhan = (l.get("ten") or f"Lần {i}").strip()
        so = int(mt.get("so_ma_de") or 1)
        mt.update(ma_de_bat_dau=ma, thu_muc_ra=os.path.relpath(os.path.join(out, ten_tm(f"{i:02d}. {nhan}")), GOC),
                  ten=(ten_khong_dau(f"{ten} {nhan}", 50) or f"BoDe_{i}").replace(" ", "_"))   # tên tệp đáp án: không dấu, không cách
        if cfg.get("ten_ky_thi_chung"):
            mt["ten_ky_thi"] = f"{cfg['ten_ky_thi_chung']} – {nhan.upper()}"
        if khong_lap:
            mt["tranh_ma"] = sorted(tranh)
        p = os.path.join(GOC, "du-lieu", "_bo_lan.json")
        json.dump(mt, open(p, "w", encoding="utf-8"), ensure_ascii=False)
        in_ra(f"▶ {nhan}: {tong_cau(mt)} câu × {so} mã đề (mã {ma}–{ma + so - 1})")
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "tron_de.py"), p], cwd=GOC, capture_output=True, text=True,
                           errors="ignore", timeout=900)
        log = (r.stdout or "") + (r.stderr or "")
        for d in log.splitlines():
            if d.strip() and not d.startswith("THU_MUC:"):
                in_ra("   " + d)
        m = re.search(r"THU_MUC:(.+)", log)
        if r.returncode or not m:
            in_ra(f"   ✗ {nhan}: không tạo được (xem nhật ký trên)"); continue
        tm = os.path.join(GOC, m.group(1).strip())
        try:
            tranh |= set(json.load(open(os.path.join(tm, "_ma_cau_dung.json"), encoding="utf-8")))
        except OSError:
            pass
        muc_luc.append({"nhan": nhan, "thu_muc": tm, "ma": [str(ma + k) for k in range(so)], "ten_ky_thi": mt.get("ten_ky_thi", "")})
        ma += so
    json.dump({"cfg": cfg, "muc_luc": [dict(x, thu_muc=os.path.relpath(x["thu_muc"], GOC)) for x in muc_luc]},
              open(os.path.join(out, "bo_de.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    in_ra(f"Đã tạo bộ {len(muc_luc)} lần · {sum(len(x['ma']) for x in muc_luc)} mã đề"
          + (" · không lặp câu giữa các lần" if khong_lap else ""))
    if bien_dich:
        bien_dich_bo(out, muc_luc, ten, in_ra)
    in_ra(f"THU_MUC:{os.path.relpath(out, GOC)}")
    return out


def bien_dich_bo(out, muc_luc, ten, in_ra=print):
    if not tim_pdflatex():
        in_ra("Không tìm thấy pdflatex — mở thư mục tex/ của từng lần bằng TeXstudio để biên dịch."); return
    for x in muc_luc:
        in_ra(f"— Biên dịch {x['nhan']}…")
        bien_dich_thu_muc(x["thu_muc"], in_ra)
    gop(out, muc_luc, ten, in_ra)


def gop(out, muc_luc, ten, in_ra=print):
    """Gộp PDF các lần thành 1 quyển câu hỏi + 1 quyển lời giải (pdfpages), có bìa và mục lục."""
    pdfl = tim_pdflatex()
    tex = os.path.join(out, "_gop"); os.makedirs(tex, exist_ok=True)
    for loai, tien_to, duoi in (("Câu hỏi", "De_", "Câu hỏi"), ("Lời giải", "LoiGiai_", "Lời giải")):
        tep, dong = [], []
        for x in muc_luc:
            for m in x["ma"]:
                f = os.path.join(x["thu_muc"], f"{tien_to}{m}.pdf")
                if os.path.exists(f):
                    dich = f"{len(tep):03d}.pdf"; shutil.copyfile(f, os.path.join(tex, dich))
                    tep.append((dich, x["nhan"], m))
        if not tep:
            continue
        nd = [r"\documentclass[12pt,a4paper]{article}\usepackage[utf8]{vietnam}\usepackage{pdfpages,xcolor}"
              r"\usepackage[a4paper,margin=2.2cm]{geometry}\usepackage[hidelinks]{hyperref}\pagestyle{empty}\begin{document}",
              r"\begin{center}\vspace*{3cm}{\Huge\bfseries " + ten.replace("&", r"\&") + r"}\par\bigskip{\Large " + loai + r"}\par\vspace{1.5cm}"
              r"{\large " + f"{len(muc_luc)} lần · {len(tep)} mã đề" + r"}\end{center}\vspace{1cm}"
              r"\begin{tabular}{@{}p{0.55\linewidth}p{0.4\linewidth}@{}}\textbf{Lần} & \textbf{Mã đề}\\\hline"]
        for x in muc_luc:
            co = [m for d, n, m in tep if n == x["nhan"]]
            if co:
                nd.append(x["nhan"].replace("&", r"\&") + " & " + ", ".join(rf"\hyperlink{{de{m}.1}}{{{m}}}" for m in co) + r"\\")
        nd.append(r"\end{tabular}\newpage")
        for d, n, m in tep:
            nd.append(rf"\includepdf[pages=-,link,linkname=de{m}]{{{d}}}")
        nd.append(r"\end{document}")
        f = f"Gop_{tien_to.strip('_')}.tex"
        open(os.path.join(tex, f), "w", encoding="utf-8").write("\n".join(nd))
        for _ in range(2):
            subprocess.run([pdfl, "-interaction=nonstopmode", f], cwd=tex, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=900)
        pdf = os.path.join(tex, f[:-4] + ".pdf")
        if os.path.exists(pdf):
            dich = f"{ten} - {duoi}.pdf"; shutil.copyfile(pdf, os.path.join(out, dich)); in_ra(f"  ✓ Quyển gộp: {dich}")
        else:
            in_ra(f"  ✗ Không gộp được quyển {duoi} (xem _gop/{f[:-4]}.log)")


if __name__ == "__main__":
    cfg = json.load(open(sys.argv[1], encoding="utf-8"))
    chay(cfg, bien_dich="--bien-dich" in sys.argv)
