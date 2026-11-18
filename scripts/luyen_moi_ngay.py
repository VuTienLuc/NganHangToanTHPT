# -*- coding: utf-8 -*-
"""
LUYỆN MỖI NGÀY — lộ trình tự luận theo ngày (Ngày 1, Ngày 2, …), hợp với học sinh nhỏ (lớp 4, 5) và lớp nào cũng dùng được.
  Mỗi ngày 1 dạng (hoặc 2): VÍ DỤ MẪU có lời giải từng bước → TỰ LUYỆN dễ → khó → ô tự đánh giá + phụ huynh kí.
  Thứ tự ngày theo đúng thứ tự bài, dạng trong SGK (mã dạng).
Ra (de-da-ra/Lớp N/<chương>/<ngày> Luyện Mỗi Ngày - …/):
  tex/LuyenMoiNgay.tex          — phiếu học sinh: trang lộ trình + mỗi ngày một trang
  tex/LuyenMoiNgay_LoiGiai.tex  — lời giải các bài tự luyện theo ngày
  PhieuHocTap_Web.html          — trang web học sinh tự luyện từng ngày (xem lời giải, tự chấm, lưu tiến độ trên máy)
  tex/phieu_web.json            — dữ liệu để đăng / dựng lại trang (nút 🌐 Phiếu HTML lên web dùng chung)
Dùng: python3 luyen_moi_ngay.py cau_hinh.json [--bien-dich]
  cau_hinh: {"pham_vi": ["4D1"] | ["4D1?1", "4D1?2"], "dang": [...] (tuỳ chọn), "so_dang_ngay": 1, "so_tuong_tu": 2,
             "so_van_dung": 1, "so_dong_lam_bai": 4, "ten": "", "seed": 1}
"""
import html, json, os, random, re, shutil, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nh_core import GOC, doc, ghi, cau_hinh, tai_id_map, lop_tu_so, thu_muc_xuat  # noqa: E402
import phieu_tu_luan  # noqa: E402
from phieu_bai_hoc import thoat, ten_tep, ten_ngan, thuoc, hop_le, khoa_noi_dung  # noqa: E402

E = lambda s: html.escape(str(s or ""), quote=True)


def khoa_dang(k):
    m = re.match(r"(\d)([A-Z])(\d+)\?(\d+)-(\d+)", k or "")
    if not m:
        return (k or "",)
    l, mon, ch, bai, dg = m.groups()
    return (int(l), int(bai), int(dg)) if lop_tu_so(l) <= 9 else (int(l), "DHC".find(mon), int(ch), int(bai), int(dg))


def chon(cfg, rng):
    """→ (kq {dạng: {vd, tu_luyen}}, các dạng theo thứ tự, thiếu)."""
    cfg.setdefault("so_tuong_tu", 2); cfg.setdefault("so_van_dung", 1)
    ds = [c for c in map(json.loads, open(os.path.join(GOC, "du-lieu", "chi_muc.jsonl"), encoding="utf-8"))
          if c["loai"] in ("TL", "TLN", "TN") and thuoc(c, cfg["pham_vi"]) and (c["loai"] == "TL" or hop_le(c))
          and (not cfg.get("dang") or c["dang_key"] in cfg["dang"])]
    cac_dang = sorted({c["dang_key"] for c in ds if c.get("dang_key")}, key=khoa_dang)
    kq, thieu = phieu_tu_luan.chon(ds, cac_dang, cfg, rng, khoa_noi_dung)
    return kq, [d for d in cac_dang if d in kq], thieu


def chia_ngay(cac_dang, so_dang_ngay, id_map):
    """Mỗi ngày tối đa so_dang_ngay dạng, không trộn hai bài khác nhau trong một ngày."""
    ngay = []
    for d in cac_dang:
        bai = d.split("-")[0]
        if ngay and len(ngay[-1]) < so_dang_ngay and ngay[-1][0].split("-")[0] == bai:
            ngay[-1].append(d)
        else:
            ngay.append([d])
    ra = []
    for i, ds in enumerate(ngay, 1):
        t = id_map.get(ds[0], {})
        so_bai = int(re.match(r".*\?(\d+)", ds[0]).group(1))
        ra.append({"so": i, "dang": ds, "bai": f"Bài {so_bai}. {(t.get('lesson_name') or '').strip()}",
                   "chuong": (t.get("chap_name") or "").strip(),
                   "ten_dang": [(id_map.get(d, {}).get("type_name") or d).strip() for d in ds]})
    return ra


# ------------------------------------------------------------------ LaTeX
def _mau(tt, ten, lop, gv):
    src = os.path.join(GOC, "khung", "DeThiChinhThuc")
    mau = doc(os.path.join(src, "mau_de.tex"))
    for k, v in {"<<SO_GD>>": tt.get("so_gd", ""), "<<TRUONG>>": tt.get("truong", ""), "<<TEN_KY_THI>>": ten,
                 "<<NAM_HOC>>": tt.get("nam_hoc", ""), "<<MON>>": f"TOÁN – Lớp {lop}", "<<THOI_GIAN>>": "",
                 "<<CHAN_TRANG>>": ten}.items():
        mau = mau.replace(k, thoat(v))
    co = "12" if lop <= 5 else "11"                       # học sinh nhỏ: chữ to hơn
    mau = re.sub(r"\\documentclass\[\d+pt,", f"\\\\documentclass[{co}pt,", mau, count=1)
    mau = re.sub(r"\\usepackage\[a4paper,[^\]]*\]\{geometry\}",
                 lambda m: "\\usepackage[a4paper,left=1.4cm,right=1.3cm,top=1.1cm,bottom=1.4cm,footskip=0.6cm]{geometry}", mau, count=1)
    mau = mau.replace("\\setstretch{1.1}", "\\setstretch{1.1}").replace("\\setlength{\\parskip}{6pt}", "\\setlength{\\parskip}{2pt}")
    them = [r"%==================== LUYỆN MỖI NGÀY ====================",
            r"\definecolor{mauPhieu}{RGB}{21,67,140}\definecolor{mauDang}{RGB}{0,121,107}\definecolor{mauNgay}{RGB}{234,88,12}",
            r"\newcommand{\phanPhieu}[1]{\par\medskip\noindent{\color{mauPhieu}\rule[0.3ex]{0.6em}{0.6em}\ \large\bfseries #1}\par"
            r"\vspace{-2pt}\noindent{\color{mauPhieu}\rule{\linewidth}{0.6pt}}\par\smallskip}",
            r"\newcommand{\dangPhieu}[2]{\par\smallskip\noindent{\colorbox{mauDang!12}{\color{mauDang}\bfseries\small\ Dạng #1\ }\ \textit{#2}}\par\nopagebreak}",
            r"\newcommand{\dongKe}[1]{\par\foreach \i in {1,...,#1}{\noindent\makebox[\linewidth]{\rule{0pt}{8mm}\color{black!35}\dotfill}\par}}",
            r"\newcommand{\oVuong}{\raisebox{-0.15ex}{\tikz\draw[line width=0.6pt] (0,0) rectangle (0.32,0.32);}}",
            r"\pagestyle{fancy}\fancyhf{}\renewcommand{\headrulewidth}{0pt}\renewcommand{\footrulewidth}{0.4pt}",
            r"\fancyfoot[L]{\footnotesize GV: " + thoat(gv) + r"}\fancyfoot[C]{\footnotesize " + thoat(ten_ngan(ten, 60)) + r"}"
            r"\fancyfoot[R]{\footnotesize Trang \thepage/\pageref{trangCuoiPhieu}}",
            r"\fancypagestyle{plain}{\fancyhf{}\fancyfoot[L]{\footnotesize GV: " + thoat(gv) + r"}\fancyfoot[R]{\footnotesize Trang \thepage/\pageref{trangCuoiPhieu}}}"]
    return src, mau.replace("\\begin{document}", "\n".join(them) + phieu_tu_luan.MACRO + "\\begin{document}", 1)


def _dau_ngay(n, tong, lop):
    return (r"\begin{tcolorbox}[colback=mauNgay!6,colframe=mauNgay,boxrule=0.8pt,arc=2mm,left=3mm,right=3mm,top=1.2mm,bottom=1.2mm]" "\n"
            r"{\LARGE\bfseries\color{mauNgay} NGÀY " + str(n["so"]) + r"}{\small\color{black!55}\,/\," + str(tong) + r"}"
            r"\hfill{\small Ngày học: \makebox[1cm]{\dotfill}/\makebox[1cm]{\dotfill}/\makebox[1.6cm]{\dotfill}}\par\smallskip" "\n"
            r"{\large\bfseries " + thoat(n["bai"]) + r"}\hfill{\small\color{black!65}Toán " + str(lop) + r"}\par\smallskip" "\n"
            r"{\small Họ và tên: \makebox[6.5cm]{\dotfill}\hfill Lớp: \makebox[2cm]{\dotfill}}" "\n"
            r"\end{tcolorbox}" "\n"
            r"{\small\itshape Đọc kĩ \textbf{Ví dụ mẫu}, rồi tự làm \textbf{Tự luyện} vào chỗ chấm; làm xong mới xem lời giải để tự chấm.}\par")


def _tu_danh_gia(so_bai):
    return (r"\par\vspace{2pt}\begin{tcolorbox}[colback=mauDang!5,colframe=mauDang!70,boxrule=0.6pt,arc=1.5mm,left=2mm,right=2mm,top=0.5mm,bottom=0.5mm]" "\n"
            r"{\small{\bfseries\color{mauDang} Tự đánh giá:} đúng \makebox[0.8cm]{\dotfill}/" + str(so_bai) + r" bài\quad"
            r"\oVuong\ Em hiểu cách làm\quad \oVuong\ Em cần hỏi thầy cô\hfill PH kí: \makebox[2.4cm]{\dotfill}}" "\n"
            r"\end{tcolorbox}")


def _lo_trinh(ngay):
    hang = "\n".join(rf"{n['so']} & {thoat(n['bai'])} & {thoat('; '.join(n['ten_dang']))} & \oVuong & \makebox[1cm]{{\dotfill}} \\ \hline"
                     for n in ngay)
    return (r"\phanPhieu{LỘ TRÌNH " + str(len(ngay)) + r" NGÀY}" "\n"
            r"{\small Mỗi ngày làm một trang (khoảng 20 – 30 phút). Làm xong đánh dấu \oVuong\ và ghi số bài làm đúng.}\par\smallskip" "\n"
            r"{\small\renewcommand{\arraystretch}{1.35}\begin{longtable}{|c|p{0.25\linewidth}|p{0.39\linewidth}|c|c|}\hline" "\n"
            r"\textbf{Ngày} & \textbf{Bài} & \textbf{Dạng toán} & \textbf{Xong} & \textbf{Đúng} \\ \hline\endhead" "\n"
            + hang + "\n\\end{longtable}}")


def viet_tex(out, ngay, kq, mau, so_dong, lop, ten):
    tong = len(ngay)
    hs, lg = [], []
    for n in ngay:
        ten_d = dict(zip(n["dang"], n["ten_dang"]))
        so_bai = sum(len(kq[d]["tu_luyen"]) for d in n["dang"])
        hs.append(r"\clearpage" "\n" + _dau_ngay(n, tong, lop) + "\n" +
                  phieu_tu_luan.khoi(kq, n["dang"], ten_d, False, so_dong, thoat, "tren_duoi") + "\n" + _tu_danh_gia(so_bai))
        lg.append(r"\phanPhieu{NGÀY " + str(n["so"]) + " – " + thoat(n["bai"]) + "}\n" +
                  phieu_tu_luan.khoi(kq, n["dang"], ten_d, True, 0, thoat))
    het = "\n\\label{trangCuoiPhieu}\n"
    bia = (r"\begin{tcolorbox}[colback=mauPhieu!4,colframe=mauPhieu,boxrule=0.8pt,arc=2mm,left=3mm,right=3mm,top=2mm,bottom=2mm]" "\n"
           r"\begin{center}{\Huge\bfseries\color{mauNgay} LUYỆN MỖI NGÀY}\\[4pt]{\Large\bfseries\color{mauPhieu} " + thoat(ten) + r"}\\[3pt]"
           r"{\small Toán " + str(lop) + r" · Tự luận có lời giải từng bước · " + str(tong) + r" ngày}\end{center}" "\n"
           r"{\small Họ và tên: \makebox[7cm]{\dotfill}\hfill Lớp: \makebox[2.2cm]{\dotfill}}" "\n\\end{tcolorbox}\n")
    ghi(os.path.join(out, "LuyenMoiNgay.tex"),
        mau.replace("<<CHE_DO_LOI_GIAI>>", "\\hienthiloigiai").replace("<<NOI_DUNG>>", bia + _lo_trinh(ngay) + "\n" + "\n".join(hs) + het))
    ghi(os.path.join(out, "LuyenMoiNgay_LoiGiai.tex"),
        mau.replace("<<CHE_DO_LOI_GIAI>>", "\\hienthiloigiai").replace(
            "<<NOI_DUNG>>", bia.replace("LUYỆN MỖI NGÀY", "LỜI GIẢI – LUYỆN MỖI NGÀY") +
            "{\\small\\itshape (Ví dụ mẫu đã có lời giải trên phiếu học sinh. Dưới đây là lời giải các bài tự luyện.)}\n" +
            "\\begin{multicols}{2}\\nhoHinh\n" + "\n".join(lg) + "\n\\end{multicols}" + het))


# ------------------------------------------------------------------ dữ liệu web + trang HTML
def du_lieu_web(cfg, ngay, kq, lop, ten, gv):
    def cau(c, vai):
        t = c["_tl"]
        return {"de": t["de"], "lg": t["lg"], "dap": t["dap"] if c["loai"] != "TL" else "", "vai": vai, "ma": c["ma"]}
    return {"kieu": "luyen_ngay", "ten": ten, "lop": lop, "giao_vien": gv, "pham_vi": cfg.get("pham_vi") or [],
            "id": "lmn-" + re.sub(r"[^a-z0-9]+", "-", ten_tep(ten, 60).lower()).strip("-") + "-" + time.strftime("%y%m%d"),
            "ngay": [{"so": n["so"], "bai": n["bai"], "chuong": n["chuong"],
                      "dang": [{"ten": td, "vi_du": cau(kq[d]["vd"], "vi_du"), "tu_luyen": [cau(c, c["_vai"]) for c in kq[d]["tu_luyen"]]}
                               for d, td in zip(n["dang"], n["ten_dang"])]} for n in ngay]}


def tao_html(P, in_ra=print, ve=True):
    """Dữ liệu luyen_ngay → trang HTML một file."""
    import phieu_web
    tat_ca = []
    for n in P["ngay"]:
        for d in n["dang"]:
            for c in [d["vi_du"]] + d["tu_luyen"]:
                c["_q"] = {"stem": c["de"], "solution": c["lg"], "options": []}
                tat_ca.append(c["_q"])
    if ve and any("tikzpicture" in q["stem"] + q["solution"] for q in tat_ca):
        try:
            import trinh_chieu
            n_h, ok = trinh_chieu.ve_hinh(tat_ca, in_ra)
            if n_h:
                in_ra(f"  Hình/bảng: {ok}/{n_h} đã thành SVG")
        except Exception as e:
            in_ra(f"  Chưa vẽ được hình ({e}) — hình hiện chữ 'xem bản PDF'.")
    ra = []
    for n in P["ngay"]:
        ds = []
        for d in n["dang"]:
            def h(c):
                f = c["_q"].get("figures") or {}
                return {"de": phieu_web.chu(c["de"], f, "stem"), "lg": phieu_web.chu(c["lg"], f, "solution"),
                        "dap": phieu_web.chu(c.get("dap") or ""), "vai": c.get("vai") or ""}
            ds.append({"ten": d["ten"], "vd": h(d["vi_du"]), "bt": [h(c) for c in d["tu_luyen"]]})
        ra.append({"so": n["so"], "bai": n["bai"], "chuong": n["chuong"], "dang": ds})
    du = json.dumps({"id": P["id"], "ten": P["ten"], "lop": P["lop"], "ngay": ra}, ensure_ascii=False).replace("</", "<\\/")
    return (TRANG.replace("__TIEU__", E(P["ten"])).replace("__LOP__", E(P["lop"])).replace("__GV__", E(P.get("giao_vien") or ""))
            .replace("__DU_LIEU__", du))


def ghi_html(thu_muc, in_ra=print, ve=True):
    goc = os.path.join(GOC, thu_muc) if not os.path.isabs(thu_muc) else thu_muc
    P = json.load(open(os.path.join(goc, "tex", "phieu_web.json"), encoding="utf-8"))
    p = os.path.join(goc, "PhieuHocTap_Web.html")
    open(p, "w", encoding="utf-8").write(tao_html(P, in_ra, ve))
    in_ra(f"  ✓ {os.path.relpath(p, GOC)}")
    return p, P


# ------------------------------------------------------------------ chính
def tao(cfg, in_ra=print):
    CH = cau_hinh()
    tt = {**CH.get("thong_tin_de", {}), **{k: v for k, v in cfg.items() if v not in (None, "")}}
    id_map = tai_id_map()
    rng = random.Random(cfg.get("seed") or time.time())
    kq, cac_dang, thieu = chon(cfg, rng)
    if not kq:
        raise RuntimeError("Phạm vi đã chọn chưa có câu tự luận nào có lời giải. Thầy nhập câu vào kho rồi tạo lại.")
    ngay = chia_ngay(cac_dang, max(1, int(cfg.get("so_dang_ngay") or 1)), id_map)
    lop = lop_tu_so(cac_dang[0][0])
    gv = tt.get("giao_vien") or "Vũ Tiến Lực"
    vd = id_map.get(cac_dang[0], {})
    cac_bai = {d.split("-")[0] for d in cac_dang}
    ten = (cfg.get("ten") or "").strip() or ((vd.get("lesson_name") if len(cac_bai) == 1 else vd.get("chap_name")) or "Toán").strip()
    so_dong = int(cfg.get("so_dong_lam_bai") or 3)
    out_goc = thu_muc_xuat(ten_tep(f"Luyện Mỗi Ngày - {ten_ngan(ten, 55)} - {time.strftime('%d-%m-%Y')}", 90), cac_dang, "phieu")
    out = os.path.join(out_goc, "tex")
    os.makedirs(out_goc)
    src, mau = _mau(tt, ten, lop, gv)
    shutil.copytree(src, out, ignore=shutil.ignore_patterns("mau_de.tex", "*.bat"))
    viet_tex(out, ngay, kq, mau, so_dong, lop, ten)
    P = du_lieu_web(cfg, ngay, kq, lop, ten, gv)
    json.dump(P, open(os.path.join(out, "phieu_web.json"), "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(cfg, open(os.path.join(out, "cau_hinh_phieu.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ghi(os.path.join(out, "_ten_phieu.txt"), ten_tep(f"Luyện Mỗi Ngày - {ten_ngan(ten, 55)}", 90))
    ghi_html(out_goc, in_ra)
    n_bt = sum(len(v["tu_luyen"]) for v in kq.values())
    in_ra(f"LUYỆN MỖI NGÀY: {ten} — {len(ngay)} ngày · {len(kq)} ví dụ mẫu · {n_bt} bài tự luyện")
    for t in thieu:
        in_ra("  ⚠ " + t)
    in_ra(f"THU_MUC:{os.path.relpath(out_goc, GOC)}")
    return out_goc


TRANG = r"""<!DOCTYPE html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>Luyện mỗi ngày – __TIEU__</title>
<script>window.MathJax={tex:{inlineMath:[['$','$'],['\\(','\\)']],displayMath:[['$$','$$'],['\\[','\\]']]},options:{enableMenu:false},chtml:{scale:1.04},
startup:{typeset:false}};</script>
<script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml-full.js"></script>
<style>
:root{--nen:#fff7ed;--mat:#fff;--mat2:#fffbf5;--chu:#1c1917;--nhat:#78716c;--vien:#fed7aa;--cam:#ea580c;--cam-dam:#c2410c;--cam-nhat:#ffedd5;
--xanh:#0f766e;--xanh-nhat:#ccfbf1;--dung:#15803d;--dung-nhat:#dcfce7;--sai:#b91c1c;--sai-nhat:#fee2e2;--vang:#facc15;--bo:16px;--co:18px}
@media (prefers-color-scheme:dark){:root{--nen:#1c1410;--mat:#292018;--mat2:#221a14;--chu:#fafaf9;--nhat:#a8a29e;--vien:#57351f;--cam:#fb923c;--cam-dam:#fdba74;
--cam-nhat:#431f0a;--xanh:#5eead4;--xanh-nhat:#134e4a88;--dung:#86efac;--dung-nhat:#14532d88;--sai:#fca5a5;--sai-nhat:#7f1d1d88}}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--nen);color:var(--chu);font:var(--co)/1.7 "Be Vietnam Pro",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.vo{max-width:860px;margin:0 auto;padding:0 16px}
.dau-trang{background:linear-gradient(135deg,#ea580c,#f59e0b);color:#fff;padding:20px 0 18px}
.dau-trang .nhan{font-size:13px;font-weight:800;letter-spacing:.1em;opacity:.9}.dau-trang h1{margin:2px 0 4px;font-size:clamp(22px,4.4vw,32px);line-height:1.25}
.dau-trang .phu{font-size:15px;opacity:.95}
.so-lieu{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px}
.so-lieu div{background:rgba(255,255,255,.2);border-radius:12px;padding:6px 12px;font-weight:700;font-size:15px}
.vach{height:8px;background:rgba(255,255,255,.3);border-radius:9px;margin-top:12px;overflow:hidden}.vach i{display:block;height:100%;background:#fff;width:0;transition:width .3s ease-out}
main{padding:18px 0 70px}
.luoi-ngay{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,240px),1fr));gap:12px}
.the-ngay{font:inherit;text-align:left;color:var(--chu);background:var(--mat);border:2px solid var(--vien);border-radius:var(--bo);padding:12px 14px;cursor:pointer;
 display:flex;flex-direction:column;gap:2px;min-height:44px;transition:transform .15s ease-out,border-color .15s}
.the-ngay:hover{transform:translateY(-2px);border-color:var(--cam)}.the-ngay:focus-visible,button:focus-visible,summary:focus-visible{outline:3px solid #60a5fa;outline-offset:2px}
.the-ngay .so{font-size:20px;font-weight:800;color:var(--cam)}.the-ngay .bai{font-weight:700;font-size:15px;line-height:1.35}
.the-ngay .dg{font-size:13.5px;color:var(--nhat);line-height:1.35}.the-ngay .tt{font-size:14px;font-weight:700;margin-top:4px}
.the-ngay.xong{border-color:var(--dung);background:var(--dung-nhat)}.the-ngay.xong .tt{color:var(--dung)}
.the-ngay.hom-nay{border-color:var(--cam);box-shadow:0 0 0 4px var(--cam-nhat)}.the-ngay.hom-nay .tt{color:var(--cam-dam)}
.goi-y{background:var(--mat);border:1px dashed var(--vien);border-radius:var(--bo);padding:12px 14px;margin:0 0 16px;font-size:15.5px}
.nut{font:inherit;font-size:16px;font-weight:700;min-height:48px;padding:10px 18px;border-radius:12px;border:2px solid var(--vien);background:var(--mat);color:var(--chu);cursor:pointer}
.nut:hover{border-color:var(--cam)}.nut.chinh{background:var(--cam);border-color:var(--cam);color:#fff}.nut.chinh:hover{background:var(--cam-dam)}
.nut.dung{border-color:var(--dung);color:var(--dung)}.nut.dung.chon{background:var(--dung);color:#fff}
.nut.sai{border-color:var(--sai);color:var(--sai)}.nut.sai.chon{background:var(--sai);color:#fff}
.thanh-ngay{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:12px}
.thanh-ngay h2{margin:0;font-size:clamp(22px,4vw,28px);color:var(--cam)}.thanh-ngay .gian{flex:1}
.bai-ten{font-weight:800;font-size:19px;margin:0}.chuong-ten{color:var(--nhat);font-size:14.5px;margin:0 0 10px}
.buoc{display:flex;align-items:center;gap:8px;margin:20px 0 8px;font-weight:800;font-size:17px}
.buoc b{display:inline-grid;place-items:center;width:30px;height:30px;border-radius:50%;background:var(--cam);color:#fff;font-size:15px}
.dang-ten{display:inline-block;background:var(--xanh-nhat);color:var(--xanh);font-weight:800;font-size:14.5px;border-radius:9px;padding:3px 10px;margin:14px 0 4px}
.cau{background:var(--mat);border:1px solid var(--vien);border-radius:var(--bo);padding:14px 16px;margin:10px 0}
.cau.vd{background:var(--cam-nhat);border-color:transparent}
.cau .nhan-cau{font-weight:800;color:var(--cam-dam);margin-right:6px}.cau .muc{font-size:12.5px;font-weight:800;color:#fff;background:#b91c1c;border-radius:6px;padding:1px 7px;margin-right:6px;vertical-align:2px}
.de p{margin:.3em 0}.de>p:first-child{display:inline}
.lg{margin-top:10px;background:var(--mat2);border-left:4px solid var(--xanh);border-radius:10px;padding:10px 14px}
.lg .lg-tieu{font-weight:800;color:var(--xanh);font-size:15px}.lg p{margin:.3em 0}
.cau.vd .lg{background:var(--mat)}
.hanh-dong{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px;align-items:center}
.cau.da-dung{border-color:var(--dung)}.cau.da-sai{border-color:var(--sai)}
.ket{background:var(--mat);border:2px solid var(--dung);border-radius:var(--bo);padding:16px;margin:18px 0;text-align:center}
.ket .sao{font-size:34px;letter-spacing:4px}.ket p{margin:.3em 0}
figure.hinh{margin:.5em auto;text-align:center}figure.hinh svg{max-width:100%;height:auto;background:#fff;border-radius:8px}
.giua{text-align:center}table{border-collapse:collapse;margin:.4em auto}td,th{border:1px solid var(--vien);padding:3px 8px}
mjx-container[display=true]{max-width:100%;overflow-x:auto;overflow-y:hidden}
footer{color:var(--nhat);font-size:13px;text-align:center;padding:20px 0}
@media (prefers-reduced-motion:reduce){*{transition:none!important;scroll-behavior:auto!important}}
@media print{.dau-trang,.hanh-dong,.thanh-ngay .nut,#ve-ds{display:none}body{background:#fff}}
</style></head><body>
<header class="dau-trang"><div class="vo">
  <div class="nhan">📅 LUYỆN MỖI NGÀY · TOÁN __LOP__</div><h1>__TIEU__</h1>
  <div class="phu">Mỗi ngày một trang: đọc ví dụ mẫu → tự làm ra giấy → xem lời giải → tự chấm.</div>
  <div class="so-lieu"><div id="sl-xong">✅ 0 ngày</div><div id="sl-sao">⭐ 0</div><div id="sl-chuoi">🔥 0 ngày liên tiếp</div></div>
  <div class="vach" aria-hidden="true"><i id="vach"></i></div>
</div></header>
<main><div class="vo" id="noi" aria-live="polite"></div></main>
<footer>GV: __GV__ · Tiến độ lưu trên máy này</footer>
<script id="du-lieu" type="application/json">__DU_LIEU__</script>
<script>
const D=JSON.parse(document.getElementById("du-lieu").textContent),KHOA="lmn:"+D.id,$=s=>document.querySelector(s);
const MUC={van_dung:"Vận dụng",nang_cao:"Nâng cao"};
let S={ngay:{}};try{S=JSON.parse(localStorage.getItem(KHOA))||S}catch(_){}
const luu=()=>{try{localStorage.setItem(KHOA,JSON.stringify(S))}catch(_){}};
const homNay=()=>new Date().toISOString().slice(0,10);
const soBai=n=>n.dang.reduce((a,d)=>a+d.bt.length,0);
const tt=n=>S.ngay[n.so]||(S.ngay[n.so]={cham:{}});
const xong=n=>{const t=S.ngay[n.so];return !!(t&&t.xong)};
const soDung=n=>{const t=S.ngay[n.so];return t?Object.values(t.cham).filter(v=>v==="d").length:0};
function chuoi(){const ds=[...new Set(Object.values(S.ngay).filter(t=>t.xong).map(t=>t.xong))].sort().reverse();if(!ds.length)return 0;
  let c=0,d=new Date(homNay());if(ds[0]!==homNay()){d.setDate(d.getDate()-1);if(ds[0]!==d.toISOString().slice(0,10))return 0}
  for(const x of ds){if(x===d.toISOString().slice(0,10)){c++;d.setDate(d.getDate()-1)}else break}return c}
function capNhatDau(){const n=D.ngay.filter(xong).length,sao=D.ngay.reduce((a,x)=>a+(xong(x)?soDung(x):0),0);
  $("#sl-xong").textContent=`✅ ${n}/${D.ngay.length} ngày`;$("#sl-sao").textContent=`⭐ ${sao}`;$("#sl-chuoi").textContent=`🔥 ${chuoi()} ngày liên tiếp`;
  $("#vach").style.width=(100*n/D.ngay.length)+"%"}
function toan(el){if(window.MathJax&&MathJax.typesetPromise)MathJax.typesetPromise([el]).catch(()=>{});else setTimeout(()=>toan(el),300)}
function esc(s){return String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"})[c])}
function veDanhSach(){
  const tiep=D.ngay.find(n=>!xong(n));
  let h=`<div class="goi-y">${tiep?`👉 Hôm nay em làm <b>Ngày ${tiep.so}</b>: ${esc(tiep.bai)}. Mỗi ngày một trang là đủ, đều đặn mới giỏi!`:"🎉 Em đã hoàn thành cả lộ trình! Em có thể làm lại những ngày còn sai để nhớ lâu hơn."}</div><div class="luoi-ngay">`;
  for(const n of D.ngay){const x=xong(n),ht=n===tiep;
    h+=`<button class="the-ngay ${x?"xong":""} ${ht?"hom-nay":""}" data-n="${n.so}"><span class="so">Ngày ${n.so}</span><span class="bai">${esc(n.bai)}</span>
      <span class="dg">${n.dang.map(d=>esc(d.ten)).join(" · ")}</span>
      <span class="tt">${x?`✓ Xong · đúng ${soDung(n)}/${soBai(n)} ${"⭐".repeat(soDung(n))}`:ht?"▶ Làm hôm nay":"Chưa làm"}</span></button>`}
  $("#noi").innerHTML=h+"</div>";
  document.querySelectorAll(".the-ngay").forEach(b=>b.onclick=()=>{location.hash="ngay-"+b.dataset.n});
  capNhatDau();window.scrollTo(0,0)}
function veNgay(so){
  const n=D.ngay.find(x=>x.so===so);if(!n){veDanhSach();return}
  const t=tt(n);let h=`<div class="thanh-ngay"><button class="nut" id="ve-ds">← Các ngày</button><h2>Ngày ${n.so}</h2><span class="gian"></span>
    <button class="nut" id="lam-lai" title="Xoá phần tự chấm của ngày này để làm lại">↺ Làm lại</button></div>
    <p class="bai-ten">${esc(n.bai)}</p><p class="chuong-ten">Toán ${esc(D.lop)}${n.chuong?" · "+esc(n.chuong):""}</p>`;
  let k=0;
  n.dang.forEach((d,j)=>{
    h+=`<span class="dang-ten">${n.dang.length>1?"Dạng "+(j+1)+": ":""}${esc(d.ten)}</span>
      <div class="buoc"><b>1</b> Đọc kĩ ví dụ mẫu</div>
      <div class="cau vd"><span class="nhan-cau">Ví dụ.</span><div class="de" style="display:inline">${d.vd.de}</div>
        <div class="lg"><div class="lg-tieu">Cách giải</div>${d.vd.lg}</div></div>
      <div class="buoc"><b>2</b> Em tự làm ra giấy, xong mới bấm xem lời giải</div>`;
    d.bt.forEach(c=>{k++;const v=t.cham[k];
      h+=`<div class="cau ${v==="d"?"da-dung":v==="s"?"da-sai":""}" id="bt${k}"><span class="nhan-cau">Bài ${k}.</span>${MUC[c.vai]?`<span class="muc">${MUC[c.vai]}</span>`:""}
        <div class="de" style="display:inline">${c.de}</div>
        <div class="lg" ${v?"":"hidden"}><div class="lg-tieu">Lời giải</div>${c.dap?`<p><b>Đáp số:</b> ${c.dap}</p>`:""}${c.lg}</div>
        <div class="hanh-dong">${v?"":`<button class="nut chinh xem" data-k="${k}">Em làm xong – xem lời giải</button>`}
          <span class="cham" ${v?"":"hidden"}><button class="nut dung ${v==="d"?"chon":""}" data-k="${k}" data-v="d">✅ Em làm đúng</button>
          <button class="nut sai ${v==="s"?"chon":""}" data-k="${k}" data-v="s">❌ Em làm chưa đúng</button></span></div></div>`})});
  h+=`<div id="ket"></div>`;
  $("#noi").innerHTML=h;window.scrollTo(0,0);
  $("#ve-ds").onclick=()=>{location.hash=""};
  $("#lam-lai").onclick=()=>{if(confirm("Làm lại ngày này? Phần tự chấm sẽ được xoá.")){delete S.ngay[n.so];luu();veNgay(so)}};
  document.querySelectorAll(".xem").forEach(b=>b.onclick=()=>{const c=$("#bt"+b.dataset.k);c.querySelector(".lg").hidden=false;c.querySelector(".cham").hidden=false;b.remove()});
  document.querySelectorAll(".cham .nut").forEach(b=>b.onclick=()=>{const k=b.dataset.k,v=b.dataset.v;t.cham[k]=v;
    const c=$("#bt"+k);c.classList.toggle("da-dung",v==="d");c.classList.toggle("da-sai",v==="s");
    c.querySelectorAll(".cham .nut").forEach(x=>x.classList.toggle("chon",x===b));
    if(Object.keys(t.cham).length>=soBai(n)&&!t.xong)t.xong=homNay();luu();veKet(n)});
  veKet(n);toan($("#noi"))}
function veKet(n){
  const t=tt(n),tong=soBai(n),dung=soDung(n),da=Object.keys(t.cham).length;
  if(da<tong){$("#ket").innerHTML="";capNhatDau();return}
  const tiep=D.ngay.find(x=>x.so>n.so);
  const loi=dung===tong?"Tuyệt vời! Em làm đúng hết. 🎉":dung*2>=tong?"Giỏi lắm! Em xem lại lời giải những bài chưa đúng nhé.":"Không sao cả! Em đọc lại ví dụ mẫu rồi bấm ↺ Làm lại vào ngày mai.";
  $("#ket").innerHTML=`<div class="ket"><div class="sao">${"⭐".repeat(dung)||"💪"}</div><p><b>Em đúng ${dung}/${tong} bài.</b> ${loi}</p>
    <div class="hanh-dong" style="justify-content:center">${tiep?`<button class="nut chinh" id="sang">Ngày ${tiep.so} (ngày mai) →</button>`:""}<button class="nut" id="ve2">Về các ngày</button></div></div>`;
  if(tiep)$("#sang").onclick=()=>{location.hash="ngay-"+tiep.so};$("#ve2").onclick=()=>{location.hash=""};
  capNhatDau()}
function dinhTuyen(){const m=location.hash.match(/^#ngay-(\d+)$/);m?veNgay(+m[1]):veDanhSach()}
window.addEventListener("hashchange",dinhTuyen);dinhTuyen();
</script></body></html>"""


if __name__ == "__main__":
    cfg = json.load(open(sys.argv[1], encoding="utf-8"))
    o = tao(cfg)
    if "--bien-dich" in sys.argv:
        from nh_core import bien_dich_thu_muc
        bien_dich_thu_muc(o)
