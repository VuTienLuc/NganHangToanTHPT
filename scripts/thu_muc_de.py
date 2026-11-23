# -*- coding: utf-8 -*-
"""THƯ MỤC ĐỀ — liệt kê mọi bộ đề/phiếu đã xuất trong de-da-ra/ để ứng dụng hiện theo Lớp → nhóm (chương / kỳ) → bộ.

Một "bộ" là một thư mục có file kết quả ngay bên trong (PDF, Word, Excel, HTML). Cấu trúc chuẩn:
  Lớp N / <chương | Ôn tập nhiều chương> / <ngày> <tên>
  Lớp N / Đề kiểm tra – Ôn thi / <kỳ> / <ngày> <tên>
  Tuyển sinh 10 / <ngày> <tên>   ·   Khác / …   ·   TrinhChieu / …
Ghim và ghi chú của thầy lưu ở de-da-ra/_thu_muc.json (đi theo kho, máy nào cũng thấy).
"Cất" một bộ = chuyển vào de-da-ra/_cu/<đường dẫn cũ> (không xoá; chuyển ngược lại được bằng Finder).
"""
import os, re, json, time, shutil, datetime
from nh_core import GOC, RA

DUOI = (".pdf", ".docx", ".xlsx", ".html", ".pptx")
P_TM = os.path.join(RA, "_thu_muc.json")
NGAY = re.compile(r"^(\d{4})-(\d{2})-(\d{2})\s+")


def _doc_tm():
    try:
        d = json.load(open(P_TM, encoding="utf-8"))
        return {"ghim": list(d.get("ghim") or []), "ghi": dict(d.get("ghi") or {})}
    except Exception:
        return {"ghim": [], "ghi": {}}


def _ghi_tm(d):
    os.makedirs(RA, exist_ok=True)
    tam = P_TM + ".tam"
    json.dump(d, open(tam, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tam, P_TM)


def kieu_tep(f):
    """Loại file để hiện nút: de | lg | tc | ln | xlsx | word | web | pdf."""
    t, e = f.lower(), os.path.splitext(f)[1].lower()
    if e == ".xlsx":
        return "xlsx"
    if e == ".docx":
        return "word"
    if e == ".html":
        return "web"
    if e == ".pptx" or "beamer" in t or "trình chiếu" in t or "trinhchieu" in t:
        return "tc"
    if "leftnote" in t:
        return "ln"
    if "loigiai" in t or "lời giải" in t or "đáp án" in t or "dap an" in t:
        return "lg"
    if re.match(r"^(de|đề)[ _]", t) or re.match(r"^de_\d", t):
        return "de"
    return "pdf"


def loai_bo(ten, tep):
    """Loại bộ để lọc nhanh."""
    t = ten.lower()
    if re.search(r"mật mã|lỗi sai|ngắt quãng|leo núi|mảnh ghép|hoạt động", t):
        return "hoat_dong"
    if re.search(r"công thức|kiến thức trọng tâm|sổ tay", t):
        return "cong_thuc"
    if re.search(r"phiếu|bài học|chuyên đề|luyện mỗi ngày", t):
        return "phieu"
    if re.search(r"trình chiếu|bài giảng|slide", t) and not any(kieu_tep(f) == "de" for f in tep):
        return "trinh_chieu"
    if any(re.match(r"de_\d", f.lower()) for f in tep) or re.search(r"đề|kiểm tra|thi|ôn tập", t):
        return "de"
    return "khac"


HAU_TO = re.compile(r"((?:\s*[-–]\s*(?:Trên lớp|Về nhà|Trình chiếu|Lời giải|Đáp án))+)$")


def _nhan(f, ten):
    """Nhãn ngắn cho file (nút bấm): Đề 101, Lời giải 101, Beamer xanh 101, Trên lớp – Lời giải, Phiếu web…"""
    g, e = os.path.splitext(f)
    m = re.match(r"^(De|LoiGiai|BeamerXanh|BeamerTrang|Leftnote|Word_De|Word_LoiGiai|DapAn|Word_K12Online)_?(\d*)(_ThuTuDaChon)?$", g)
    if m:
        ten_k = {"De": "Đề", "LoiGiai": "Lời giải", "BeamerXanh": "Beamer xanh", "BeamerTrang": "Beamer trắng", "Leftnote": "Leftnote",
                 "Word_De": "Word đề", "Word_LoiGiai": "Word lời giải", "DapAn": "Đáp án Excel", "Word_K12Online": "Word K12Online"}[m.group(1)]
        return (ten_k + " " + m.group(2)).strip() + (" (thứ tự đã chọn)" if m.group(3) else "")
    if g == "PhieuHocTap_Web":
        return "Phiếu web"
    hau = HAU_TO.search(g)
    hau = re.sub(r"\s*[-–]\s*", " – ", hau.group(1)).strip(" –") if hau else ""
    m = re.match(r"^(Đề \d+|Đề cương)", g)
    if m:
        return m.group(1) + (" – " + hau if hau else "")
    if hau:
        return hau
    goc = re.sub(r"\s*\(\d+\)$", "", ten)
    if g in (ten, goc) or g.startswith(goc[:25]) or goc.startswith(g) or len(g) > 28:
        return "Phiếu" if e.lower() == ".pdf" else e[1:].upper()
    return g


def _so_cau(thu):
    p = os.path.join(thu, "_ma_cau_dung.json")
    try:
        return len(json.load(open(p, encoding="utf-8")))
    except Exception:
        return 0


def danh_sach():
    """→ {"bo": [...], "khu": [[tên khu, số bộ], …], "ghim": [...], "ghi": {...}}"""
    tm = _doc_tm()
    bo = []
    if not os.path.isdir(RA):
        return {"bo": [], "khu": [], **tm}
    for r, ds, fs in os.walk(RA):
        rel = os.path.relpath(r, RA)
        ds[:] = [d for d in ds if not d.startswith((".", "_")) and d not in ("tex", "Ans", "Ansbook")]
        if rel == ".":
            continue
        tep = sorted(f for f in fs if f.lower().endswith(DUOI) and not f.startswith((".", "_", "~$")))
        if not tep:
            continue
        ds[:] = []                                     # một bộ: không đi sâu hơn
        phan = rel.split(os.sep)
        ten_thu = phan[-1]
        m = NGAY.match(ten_thu)
        mt = max(os.path.getmtime(os.path.join(r, f)) for f in tep)
        if m:
            ngay = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
            ten = ten_thu[m.end():]
        else:
            ngay = datetime.date.fromtimestamp(mt).isoformat()
            ten = ten_thu
        if len(phan) == 1:                             # file nằm thẳng trong khu (vd TrinhChieu/)
            khu, nhom = phan[0], []
        else:
            khu, nhom = phan[0], phan[1:-1]
        ds_tep = [{"ten": f, "p": os.path.relpath(os.path.join(r, f), GOC), "kieu": kieu_tep(f), "nhan": _nhan(f, ten),
                   "kb": max(1, os.path.getsize(os.path.join(r, f)) // 1024)} for f in tep]
        so_ma = sorted({re.match(r"De_(\d+)\.pdf$", f).group(1) for f in tep if re.match(r"De_(\d+)\.pdf$", f)})
        p = os.path.relpath(r, GOC)
        bo.append({"p": p, "khu": khu, "nhom": nhom, "ten": ten, "ngay": ngay, "mt": int(mt), "tep": ds_tep,
                   "loai": loai_bo(ten + " " + " ".join(nhom), tep), "so_ma": so_ma, "so_cau": _so_cau(r),
                   "ghim": p in tm["ghim"], "ghi": tm["ghi"].get(p, "")})
    dem = {}
    for b in bo:
        dem[b["khu"]] = dem.get(b["khu"], 0) + 1

    def thu_tu(k):
        m = re.match(r"Lớp (\d+)$", k)
        return (0, -int(m.group(1))) if m else (1, {"Tuyển sinh 10": 0, "Khác": 2, "TrinhChieu": 3}.get(k, 1), k)
    return {"bo": bo, "khu": [[k, dem[k]] for k in sorted(dem, key=thu_tu)], **tm}


def _an_toan(p):
    a = os.path.realpath(os.path.join(GOC, p or ""))
    if not a.startswith(os.path.realpath(RA) + os.sep) or not os.path.isdir(a):
        raise ValueError("Thư mục không nằm trong de-da-ra.")
    return a


def ghim(p, bat=True):
    _an_toan(p)
    d = _doc_tm()
    d["ghim"] = [x for x in d["ghim"] if x != p] + ([p] if bat else [])
    _ghi_tm(d)


def ghi_chu(p, noi):
    _an_toan(p)
    d = _doc_tm()
    noi = (noi or "").strip()[:300]
    if noi:
        d["ghi"][p] = noi
    else:
        d["ghi"].pop(p, None)
    _ghi_tm(d)


def cat(p):
    """Chuyển bộ vào de-da-ra/_cu/<đường dẫn cũ> (không xoá)."""
    a = _an_toan(p)
    rel = os.path.relpath(a, RA)
    dich = os.path.join(RA, "_cu", rel)
    if os.path.exists(dich):
        dich += time.strftime(" (%H%M%S)")
    os.makedirs(os.path.dirname(dich), exist_ok=True)
    shutil.move(a, dich)
    d = _doc_tm()
    d["ghim"] = [x for x in d["ghim"] if x != p]
    d["ghi"].pop(p, None)
    _ghi_tm(d)
    return os.path.relpath(dich, GOC)
