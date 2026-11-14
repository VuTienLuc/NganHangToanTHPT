# -*- coding: utf-8 -*-
"""
NGÂN HÀNG TUYỂN SINH 10 – TOÁN TP.HCM (cấu trúc 7 bài, 10 điểm, 120 phút — đề chính thức 2025–26, 2026–27).
  • Dạng toán + ma trận: du-lieu/ts10_dang.json (từ file Excel "Ma trận dạng toán vào 10 TP.HCM").
  • Kho: cau-hoi-ts10/Bai1.tex … Bai7.tex — mỗi mục là MỘT BÀI hoàn chỉnh (đủ các ý a, b, c) dạng
        \\begin{bt}%[TS10 1.0 1.2]%[ma:xxxxxxxx]
        <đề bài>
        \\loigiai{<lời giải + điểm từng ý>}
        \\end{bt}
    Dòng đầu ghi các mã dạng (bảng Excel) của bài; Bài 7 ghi cấu hình + dạng từng câu (vd 7.C2 7.a1 7.b1 7.c1).
  • Tạo đề: mỗi bài lấy 1 mục trong kho (theo dạng chỉ định hoặc ngẫu nhiên theo tỉ lệ đề thật), nhiều đề không trùng bài.
"""
import os, re, json, random, hashlib, datetime, collections, shutil, subprocess
from nh_core import GOC, tim_pdflatex

P_DANG = os.path.join(GOC, "du-lieu", "ts10_dang.json")
P_KHO = os.path.join(GOC, "cau-hoi-ts10")      # ngoài cau-hoi/ để chỉ mục câu lẻ không đọc nhầm
P_LS = os.path.join(GOC, "du-lieu", "ts10_lich_su.json")
MAC_DINH = {"so_gd": "SỞ GIÁO DỤC VÀ ĐÀO TẠO", "tinh": "THÀNH PHỐ HỒ CHÍ MINH", "ten_ky_thi": "KỲ THI TUYỂN SINH LỚP 10 THPT",
            "nam_hoc": "NĂM HỌC 2027 – 2028", "mon": "TOÁN", "thoi_gian": "120 phút", "giao_vien": "Vũ Tiến Lực",
            "nhan_de": "ĐỀ LUYỆN TẬP"}


def du_lieu():
    return json.load(open(P_DANG, encoding="utf-8"))


def lich_su():
    return json.load(open(P_LS, encoding="utf-8")) if os.path.exists(P_LS) else {}


# ---------------------------------------------------------------- đọc / tách khối
def khop_ngoac(t, i):
    """t[i] == '{' → vị trí '}' khớp."""
    sau = 0
    j = i
    while j < len(t):
        ch = t[j]
        if ch == "\\":
            j += 2; continue
        if ch == "{":
            sau += 1
        elif ch == "}":
            sau -= 1
            if sau == 0:
                return j
        j += 1
    return -1


def tach_khoi(van_ban):
    return re.findall(r"\\begin\{bt\}.*?\\end\{bt\}", van_ban or "", re.S)


def phan_tich(khoi):
    dau = khoi.split("\n", 1)[0]
    m = re.search(r"%\[TS10([^\]]*)\]", dau)
    cac = m.group(1).split() if m else []
    mm = re.search(r"%\[ma:([0-9a-f]{8})\]", dau)
    than = khoi[len("\\begin{bt}"):khoi.rfind("\\end{bt}")]
    than = than.split("\n", 1)[1] if "\n" in than else ""
    lg = ""
    k = re.search(r"\\loigiai\s*\{", than)
    if k:
        a = k.end() - 1; b = khop_ngoac(than, a)
        if b > 0:
            lg = than[a + 1:b].strip(); than = than[:k.start()] + than[b + 1:]
    de = than.strip()
    bai = int(cac[0].split(".")[0]) if cac and re.match(r"\d", cac[0]) else 0
    return {"cac_dang": cac, "bai": bai, "ma": mm.group(1) if mm else None, "de": de, "lg": lg, "khoi": khoi}


def chuan_hoa(t):
    return re.sub(r"[\s{}\\$~.,;:()]+", "", t).lower()


def doc_kho():
    ra = []
    if not os.path.isdir(P_KHO):
        return ra
    for f in sorted(os.listdir(P_KHO)):
        if f.endswith(".tex"):
            for k in tach_khoi(open(os.path.join(P_KHO, f), encoding="utf-8").read()):
                x = phan_tich(k); x["file"] = f
                if x["ma"]:
                    ra.append(x)
    return ra


def thong_ke():
    D = du_lieu(); kho = doc_kho(); ls = lich_su()
    dem = collections.Counter(d for x in kho for d in x["cac_dang"])
    theo_bai = collections.Counter(x["bai"] for x in kho)
    chua = collections.Counter(x["bai"] for x in kho if not ls.get(x["ma"]))
    return {"bai": [dict(b, so_kho=theo_bai.get(b["bai"], 0), chua_dung=chua.get(b["bai"], 0)) for b in D["bai"]],
            "dang": [dict(d, so_kho=dem.get(d["ma"], 0)) for d in D["dang"]], "tong": len(kho)}


# ---------------------------------------------------------------- nhập kho
def nhap(van_ban, thu=False):
    """Dán kết quả AI → thêm vào kho. thu=True: chỉ kiểm tra."""
    t = van_ban or ""
    m = re.search(r"```(?:latex|tex)?\s*\n(.*?)```", t, re.S)
    if m:
        t = "\n".join(re.findall(r"```(?:latex|tex)?\s*\n(.*?)```", t, re.S))
    ma_hop_le = {d["ma"] for d in du_lieu()["dang"]}
    kho = doc_kho(); da_co = {chuan_hoa(x["de"]) for x in kho}
    them, canh_bao = collections.defaultdict(list), []
    for i, k in enumerate(tach_khoi(t), 1):
        x = phan_tich(k)
        if not x["cac_dang"]:
            canh_bao.append(f"Bài thứ {i}: thiếu dòng %[TS10 <mã dạng>] → bỏ qua"); continue
        sai = [d for d in x["cac_dang"] if d not in ma_hop_le]
        if sai:
            canh_bao.append(f"Bài thứ {i}: mã dạng không có trong bảng: {', '.join(sai)} (vẫn nhập)")
        if not 1 <= x["bai"] <= 7:
            canh_bao.append(f"Bài thứ {i}: không xác định được Bài 1–7 → bỏ qua"); continue
        if not x["lg"]:
            canh_bao.append(f"Bài thứ {i} (Bài {x['bai']}): chưa có \\loigiai{{…}} (vẫn nhập)")
        if x["de"].count("{") != x["de"].count("}"):
            canh_bao.append(f"Bài thứ {i}: ngoặc {{ }} không cân → bỏ qua"); continue
        n = chuan_hoa(x["de"])
        if n in da_co:
            canh_bao.append(f"Bài thứ {i} (Bài {x['bai']}): trùng bài đã có → bỏ qua"); continue
        da_co.add(n)
        ma = hashlib.sha1(n.encode()).hexdigest()[:8]
        khoi = f"\\begin{{bt}}%[TS10 {' '.join(x['cac_dang'])}]%[ma:{ma}]\n{x['de']}\n\\loigiai{{\n{x['lg']}\n}}\n\\end{{bt}}"
        them[x["bai"]].append(khoi)
    if not thu:
        os.makedirs(P_KHO, exist_ok=True)
        for b, ds in them.items():
            p = os.path.join(P_KHO, f"Bai{b}.tex")
            with open(p, "a", encoding="utf-8") as f:
                f.write(("\n\n" if os.path.exists(p) and os.path.getsize(p) else f"% NGÂN HÀNG TUYỂN SINH 10 – BÀI {b}\n\n") + "\n\n".join(ds) + "\n")
    return {"so": sum(len(v) for v in them.values()), "theo_bai": {b: len(v) for b, v in sorted(them.items())}, "canh_bao": canh_bao}


# ---------------------------------------------------------------- chọn đề
def _chon_1(bai, kieu, kho, tranh, ls, rng, D):
    """kieu: 'ti_le' | 'hay_nhat' | mã dạng."""
    ung = [x for x in kho if x["bai"] == bai and x["ma"] not in tranh]
    if not ung:
        return None
    dang_bai = [d for d in D["dang"] if d["bai"] == bai]
    if kieu not in ("ti_le", "hay_nhat", "", None):
        loc = [x for x in ung if kieu in x["cac_dang"]]
        ung = loc or ung
    elif kieu == "hay_nhat":
        chinh = [c["dang_chinh"] for b in D["bai"] if b["bai"] == bai for c in b["cau"]]
        loc = [x for x in ung if any(d in x["cac_dang"] for d in chinh)]
        ung = loc or ung
    else:   # theo tỉ lệ đề thật: trọng số = tổng số đề có các dạng của bài
        w = {d["ma"]: max(1, d["so_de"]) for d in dang_bai}
        trong = [sum(w.get(d, 1) for d in x["cac_dang"]) or 1 for x in ung]
        moi = [i for i, x in enumerate(ung) if not ls.get(x["ma"])]
        idx = moi or list(range(len(ung)))
        return ung[rng.choices(idx, weights=[trong[i] for i in idx])[0]]
    moi = [x for x in ung if not ls.get(x["ma"])]
    return rng.choice(moi or ung)


def chon_bo(cfg, rng=None):
    """→ (danh sách đề [{bai: mục}], thiếu)."""
    rng = rng or random.Random(cfg.get("seed"))
    D = du_lieu(); kho = doc_kho(); ls = lich_su() if cfg.get("tranh_da_dung", True) else {}
    so_de = max(1, int(cfg.get("so_de") or 1))
    kieu = {int(k): v for k, v in (cfg.get("dang") or {}).items()}
    de, thieu, da = [], [], set()
    for _ in range(so_de):
        mot = {}
        for b in range(1, 8):
            x = _chon_1(b, kieu.get(b, "ti_le"), kho, da, ls, rng, D)
            if not x:   # hết bài riêng → cho phép dùng lại giữa các đề
                x = _chon_1(b, kieu.get(b, "ti_le"), kho, set(), ls, rng, D)
            if x:
                mot[b] = x; da.add(x["ma"])
            elif f"Bài {b}" not in thieu:
                thieu.append(f"Bài {b}")
        de.append(mot)
    return de, thieu


def doi(bai, kieu, tranh, ma_cu=None):
    D = du_lieu(); kho = doc_kho()
    return _chon_1(int(bai), kieu or "ti_le", kho, set(tranh or []) | {ma_cu}, lich_su(), random.Random(), D)


def the_xem(x):
    import xem_truoc
    return {"ma": x["ma"], "bai": x["bai"], "cac_dang": x["cac_dang"], "de": xem_truoc.sang_html(x["de"]),
            "da_dung": len(lich_su().get(x["ma"], []))}


# ---------------------------------------------------------------- LaTeX
DAU = r"""\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{vietnam}
\usepackage{amsmath,amssymb,mathtools,array,tabularx,multicol,enumitem,graphicx,xcolor}
\usepackage[a4paper,top=1.6cm,bottom=1.8cm,left=2cm,right=1.8cm]{geometry}
\usepackage{tikz,pgfplots}\pgfplotsset{compat=1.16}
\usetikzlibrary{calc,angles,quotes,intersections,patterns,arrows.meta,positioning,through}
\IfFileExists{tkz-euclide.sty}{\usepackage{tkz-euclide}}{}
\usepackage{fancyhdr}\pagestyle{fancy}\fancyhf{}\renewcommand{\headrulewidth}{0pt}
\fancyfoot[L]{\footnotesize <<CHAN>>}\fancyfoot[R]{\footnotesize Trang \thepage}
\setlength{\parindent}{0pt}\setlength{\parskip}{3pt}
\setlist{nosep,leftmargin=1.5em}
\newcommand{\bai}[2]{\par\medskip\noindent\textbf{Bài #1.} \textit{(#2 điểm)}\ }
\newcommand{\heva}[1]{\left\{\begin{aligned}#1\end{aligned}\right.}
\newcommand{\hoac}[1]{\left[\begin{aligned}#1\end{aligned}\right.}
\providecommand{\dfrac}{\frac}
\begin{document}
"""


def thoat(s):
    return re.sub(r"([&%#_$])", r"\\\1", str(s or ""))


def dau_de(tt, so, loi_giai=False):
    return (r"\noindent\begin{tabular}{@{}>{\centering\arraybackslash}p{0.40\linewidth}>{\centering\arraybackslash}p{0.58\linewidth}@{}}" "\n"
            rf"{thoat(tt['so_gd'])} & \textbf{{{thoat(tt['ten_ky_thi'])}}}\\" "\n"
            rf"\textbf{{{thoat(tt['tinh'])}}} & \textbf{{{thoat(tt['nam_hoc'])}}}\\" "\n"
            rf"\rule{{3cm}}{{0.4pt}} & \textbf{{MÔN: {thoat(tt['mon'])}}}\\" "\n"
            rf"\fbox{{\textbf{{{thoat(tt['nhan_de'])} SỐ {so}}}}} & "
            + (r"\textbf{HƯỚNG DẪN GIẢI VÀ BIỂU ĐIỂM}" if loi_giai else
               rf"Thời gian làm bài: {thoat(tt['thoi_gian'])} \textit{{(không kể thời gian phát đề)}}") + r"\\" "\n"
            r"\end{tabular}\par\medskip" "\n")


def viet_de(mot, tt, so, loi_giai, D):
    diem = {b["bai"]: b["diem"] for b in D["bai"]}
    f = [dau_de(tt, so, loi_giai)]
    for b in range(1, 8):
        x = mot.get(b)
        if not x:
            f.append(rf"\bai{{{b}}}{{{diem[b]:g}}}\ \textit{{(kho chưa có bài này)}}".replace(".", ",")); continue
        f.append(rf"\bai{{{b}}}{{{('%g' % diem[b]).replace('.', ',')}}}" + x["de"])
        if loi_giai:
            f.append(r"\par\smallskip\noindent{\color{blue!60!black}\textbf{Lời giải.}}\ " + (x["lg"] or r"\textit{(chưa có lời giải)}"))
    if not loi_giai:
        f.append(r"\par\bigskip\centering --- HẾT --- \par\smallskip{\footnotesize\itshape Thí sinh không được sử dụng tài liệu. Cán bộ coi thi không giải thích gì thêm.}")
    return "\n\n".join(f)


def tao(cfg, in_ra=print, chon_san=None):
    """Tạo bộ đề tuyển sinh 10. chon_san: [{bai: ma}] đã xem trước và xác nhận."""
    D = du_lieu(); tt = dict(MAC_DINH, **{k: v for k, v in cfg.items() if k in MAC_DINH and v})
    if chon_san:
        theo_ma = {x["ma"]: x for x in doc_kho()}
        bo = [{int(b): theo_ma[m] for b, m in d.items() if m in theo_ma} for d in chon_san]
        thieu = [f"Bài {b}" for b in range(1, 8) if any(b not in d for d in bo)]
    else:
        bo, thieu = chon_bo(cfg)
    ngay = datetime.date.today().strftime("%d-%m-%Y")
    ten = re.sub(r'[\\/:*?"<>|]', "", cfg.get("ten") or "Đề luyện tuyển sinh 10")[:70].strip()
    goc = os.path.join(GOC, "de-da-ra", f"Tuyển sinh 10 - {ten} - {ngay}")
    out_goc, n = goc, 2
    while os.path.exists(out_goc):
        out_goc = f"{goc} ({n})"; n += 1
    tex = os.path.join(out_goc, "tex"); os.makedirs(tex)
    chan = thoat(f"GV: {tt['giao_vien']}  ·  {ten}")
    for i, mot in enumerate(bo, 1):
        for lg in (False, True):
            ten_f = f"De_{i:02d}{'_LoiGiai' if lg else ''}.tex"
            open(os.path.join(tex, ten_f), "w", encoding="utf-8").write(
                DAU.replace("<<CHAN>>", chan) + viet_de(mot, tt, i, lg, D) + "\n\\end{document}\n")
    json.dump({"cfg": cfg, "bo": [{b: x["ma"] for b, x in d.items()} for d in bo]},
              open(os.path.join(out_goc, "bo_de.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # lịch sử dùng
    ls = lich_su(); hom = datetime.date.today().isoformat()
    for d in bo:
        for x in d.values():
            ls.setdefault(x["ma"], []).append(hom)
    json.dump(ls, open(P_LS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    in_ra(f"Đã tạo {len(bo)} đề tuyển sinh 10 (7 bài, 10 điểm, 120 phút) trong {os.path.relpath(out_goc, GOC)}/")
    for i, d in enumerate(bo, 1):
        in_ra(f"  Đề {i:02d}: " + " · ".join(f"B{b}[{' '.join(x['cac_dang'][:2])}]" for b, x in sorted(d.items())))
    for t in thieu:
        in_ra(f"  ⚠ {t}: kho chưa có bài — bấm Prompt AI soạn bài để bổ sung")
    in_ra(f"THU_MUC:{os.path.relpath(out_goc, GOC)}")
    return out_goc


def bien_dich(out_goc, in_ra=print):
    pdfl = tim_pdflatex()
    if not pdfl:
        in_ra("Không tìm thấy pdflatex — mở các file trong thư mục tex/ bằng TeXstudio để biên dịch."); return False
    tex = os.path.join(out_goc, "tex"); ten = os.path.basename(out_goc).split(" - ")[1] if " - " in os.path.basename(out_goc) else "De"
    ok = True
    for f in sorted(x for x in os.listdir(tex) if x.endswith(".tex")):
        for _ in range(2):
            r = subprocess.run([pdfl, "-interaction=nonstopmode", "-halt-on-error", f], cwd=tex, capture_output=True,
                               text=True, errors="ignore", timeout=300, env=dict(os.environ, TEXINPUTS=os.environ.get("NH_TEXINPUTS", "") + ":"))
        pdf = os.path.join(tex, f[:-4] + ".pdf")
        if r.returncode == 0 and os.path.exists(pdf):
            so = re.search(r"De_(\d+)", f).group(1)
            dich = f"Đề {so}{' - Lời giải' if 'LoiGiai' in f else ''}.pdf"
            shutil.copy(pdf, os.path.join(out_goc, dich)); in_ra(f"  ✓ {dich}")
        else:
            ok = False
            loi = [l for l in (r.stdout or "").splitlines() if l.startswith("!")][:2]
            in_ra(f"  ✗ {f}: {' | '.join(loi) or 'lỗi biên dịch'} (xem tex/{f[:-4]}.log)")
    return ok


# ---------------------------------------------------------------- prompt AI
def prompt(bai, cac_dang=None, so_luong=5):
    D = du_lieu(); bai = int(bai)
    B = next(b for b in D["bai"] if b["bai"] == bai)
    dang = [d for d in D["dang"] if d["bai"] == bai]
    chon = [d for d in dang if not cac_dang or d["ma"] in cac_dang]
    cau = "\n".join(f"  - Câu {c['cau']} ({str(c['diem']).replace('.', ',')} điểm, mức {c['muc']}): {c['yeu_cau']}" for c in B["cau"])
    ds = "\n".join(f"  - {d['ma']}  {d['ten']}  [câu {d['cau']}, mức {d['muc']}] — dấu hiệu: {d['dau_hieu']}"
                   + (f" — ghi chú: {d['ghi_chu']}" if d['ghi_chu'] else "") for d in chon)
    rieng = {
        1: "Ý a) luôn là vẽ (P): y = ax² (a ≠ 0, chọn a để bảng giá trị 5 điểm có y nguyên). Lời giải ý a) có bảng giá trị (tabular) và hình vẽ (P) bằng TikZ (\\draw[domain=…,smooth] plot (\\x,{a*\\x*\\x});).",
        2: "Phương trình bậc hai có hệ số nguyên, Δ không chính phương (bắt buộc dùng Viète, không giải được nghiệm đẹp). Ý a) chứng minh có hai nghiệm phân biệt (0,25 đ), ý b) tính biểu thức của x₁, x₂ (0,75 đ).",
        3: "Đề có bảng số liệu hoặc biểu đồ VẼ BẰNG TikZ/pgfplots (\\begin{tikzpicture}\\begin{axis}[ybar,…] … \\end{axis}\\end{tikzpicture}), số liệu cụ thể, bối cảnh học sinh TP.HCM. Ba ý a), b), c) mỗi ý 0,5 đ: a) đọc/tính từ biểu đồ; b), c) xác suất (kết quả phân số tối giản).",
        4: "Khung: a) viết biểu thức A theo x (thu gọn); b) tìm x để A thỏa điều kiện (lập phương trình, thường bậc hai). Bối cảnh thực tế (mảnh đất, lối đi, hồ tròn, giảm giá…). Có hình minh họa TikZ nếu là hình học.",
        5: "Vật thể thực tế (đề Sở gần đây là hình khối ghép: trụ + nửa cầu, trụ + nón…). ĐỀ CHO SẴN CÔNG THỨC thể tích/diện tích cần dùng. Có hình minh họa TikZ đơn giản. a) tính thể tích/diện tích; b) bài toán thực tế từ kết quả a (chi phí sơn, nước dâng…), làm tròn theo yêu cầu.",
        6: "Một bài lập hệ phương trình (hoặc phương trình) bậc nhất hai ẩn, số liệu đẹp, có đơn vị; lời giải: gọi ẩn + điều kiện, lập hệ, giải, đối chiếu, kết luận.",
        7: "Bài hình học đường tròn đủ ba câu a), b), c) (mỗi câu 1 điểm) trên CÙNG một cấu hình; ghi trên dòng đầu: mã cấu hình (7.C1…7.C5) + mã dạng của từng câu (7.a…, 7.b…, 7.c…). Lời giải có HÌNH VẼ TikZ đầy đủ (đặt đầu lời giải), lập luận chặt chẽ, chỉ dùng kiến thức lớp 9 (góc nội tiếp, tứ giác nội tiếp, tam giác đồng dạng, hệ thức lượng); câu c) thường tính theo R.",
    }[bai]
    vi_du = " ".join(d["ma"] for d in chon[:2]) if bai != 7 else "7.C2 7.a1 7.b1 7.c1"
    return f"""# NHIỆM VỤ
Bạn là giáo viên Toán THCS giàu kinh nghiệm luyện thi vào lớp 10 TP.HCM (chương trình GDPT 2018, SGK Toán 9 Kết nối tri thức).
Hãy soạn **{so_luong} BÀI {bai} khác nhau** cho đề tuyển sinh lớp 10 môn Toán TP.HCM (cấu trúc 7 bài, 10 điểm, 120 phút).

# BÀI {bai} – {B['chu_de']} ({str(B['diem']).replace('.', ',')} điểm), gồm:
{cau}

# CÁC DẠNG ĐƯỢC CHỌN (rải đều {so_luong} bài cho các dạng, ưu tiên dạng có tỉ lệ ra đề cao)
{ds}

# YÊU CẦU RIÊNG CHO BÀI {bai}
- {rieng}
- Văn phong, độ dài, độ khó giống đề chính thức của Sở GD&ĐT TP.HCM 2025–2026, 2026–2027; số liệu đẹp, đáp số đúng (tự kiểm tra lại từng phép tính).
- Không dùng kiến thức THPT.

# ĐỊNH DẠNG BẮT BUỘC (LaTeX) — trả về DUY NHẤT một khối ```latex … ```, gồm {so_luong} khối:
\\begin{{bt}}%[TS10 {vi_du}]
<đề bài: câu dẫn, rồi các ý xuống dòng: \\textbf{{a)}} … \\par \\textbf{{b)}} …  (không ghi "Bài {bai}", không ghi điểm tổng)>
\\loigiai{{
\\textbf{{a)}} … \\hfill \\textit{{(… điểm)}}\\par
\\textbf{{b)}} … \\hfill \\textit{{(… điểm)}}
}}
\\end{{bt}}
- Dòng đầu mỗi khối: %[TS10 <các mã dạng của bài, cách nhau bởi dấu cách>] — chỉ dùng mã trong danh sách trên.
- Công thức trong $…$; số thập phân dùng dấu phẩy $2{{,}}5$; hệ phương trình dùng \\heva{{…\\\\…}}; không dùng \\section, không gói lạ (được dùng tikz, pgfplots, tkz-euclide).
- Hình vẽ: \\begin{{center}}\\begin{{tikzpicture}}[scale=…] … \\end{{tikzpicture}}\\end{{center}} (bán kính, tọa độ cụ thể, có nhãn điểm).
"""
