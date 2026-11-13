# -*- coding: utf-8 -*-
"""
BƯỚC 3: trộn đề theo ma trận → xuất đề LaTeX nhiều mã đề.

Cách chạy:
  python3 scripts/tron_de.py ma-tran/GHK1_12.json          # ma trận dạng JSON
  python3 scripts/tron_de.py ma-tran/GHK1_12.csv           # ma trận dạng bảng (sinh mẫu bằng tao_mau_ma_tran.py)
Tuỳ chọn:
  --thu          chỉ chọn câu, in danh sách, không ghi file
  --bien-dich    gọi pdflatex biên dịch luôn (cần LaTeX có gói vietnam)
  --so-ma-de 4   --ten GHK1_12A   (ghi đè giá trị trong ma trận)

Kết quả trong de-da-ra/<ten>/:
  <ten>_<mã>.tex            đề cho học sinh (không lời giải)
  <ten>_<mã>_LoiGiai.tex    đề + lời giải + bảng đáp án
  <ten>_TatCa_De.tex        mọi mã đề trong một file (in một lần)
  <ten>_TatCa_LoiGiai.tex   mọi mã đề kèm lời giải
  dap_an_ngang.csv          mỗi mã đề một dòng (mở bằng Excel, nạp app chấm)
  dap_an.csv                mỗi câu một dòng (có mã câu gốc)
  danh_sach_cau.csv, ma_tran_da_dung.json
"""
import os, sys, json, re, random, shutil, csv, argparse, subprocess, time, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nh_core import *

ap = argparse.ArgumentParser()
ap.add_argument("ma_tran")
ap.add_argument("--thu", action="store_true")
ap.add_argument("--bien-dich", action="store_true")
ap.add_argument("--so-ma-de", type=int)
ap.add_argument("--ten")
a = ap.parse_args()

CH = cau_hinh()
THONG_TIN_MAC_DINH = {
    "so_gd": "SỞ GD&ĐT TP. HỒ CHÍ MINH", "truong": "TRƯỜNG THPT NGUYỄN HỮU CẢNH",
    "ten_ky_thi": "ĐỀ KIỂM TRA", "nam_hoc": "NĂM HỌC 2026 -- 2027", "mon": "TOÁN -- Lớp 12",
    "thoi_gian": "90 phút", "khung": "DeThiChinhThuc", "so_ma_de": 4, "ma_de_bat_dau": 101,
    "xao_cau": True, "xao_phuong_an": True, "sap_xep": "ngau_nhien",
    "moi_ma_de_cau_khac_nhau": False, "tranh_cau_da_dung": True,
}
CAC_LOAI = ["TN", "DS", "TLN", "TL"]
CAC_MUC = ["N", "H", "V", "C"]

def doc_ma_tran_csv(p):
    """Bảng ma trận: mỗi dòng một dạng; cột TN_N…TL_C là số câu cần lấy."""
    phan = collections.OrderedDict((l, []) for l in CAC_LOAI)
    with open(p, encoding="utf-8-sig", newline="") as f:
        sample = f.read(4096); f.seek(0)
        dl = csv.Sniffer().sniff(sample, delimiters=",;\t") if sample else csv.excel
        for r in csv.DictReader(f, dialect=dl):
            dang = (r.get("ma_dang") or "").strip()
            if not dang or dang.startswith("#"):
                continue
            for l in CAC_LOAI:
                for m in CAC_MUC:
                    v = (r.get(f"{l}_{m}") or "").strip()
                    if v and v not in ("0", "-"):
                        phan[l].append({"dang": dang, "muc": m, "so": int(float(v))})
    return [{"loai": l, "yeu_cau": yc} for l, yc in phan.items() if yc]

if a.ma_tran.lower().endswith(".csv"):
    mt = {"ten": os.path.splitext(os.path.basename(a.ma_tran))[0], "phan": doc_ma_tran_csv(a.ma_tran)}
else:
    mt = json.load(open(a.ma_tran, encoding="utf-8"))
    if "ma_tran_csv" in mt:
        p = mt["ma_tran_csv"]
        p = p if os.path.isabs(p) else os.path.join(GOC, p)
        mt["phan"] = doc_ma_tran_csv(p)
mt = {**THONG_TIN_MAC_DINH, **CH.get("thong_tin_de", {}), **mt}
if a.so_ma_de: mt["so_ma_de"] = a.so_ma_de
if a.ten: mt["ten"] = a.ten
ten = mt["ten"]
rng = random.Random(mt.get("seed", int(time.time())))

p_cm = os.path.join(GOC, "du-lieu", "chi_muc.jsonl")
if not os.path.exists(p_cm):
    sys.exit("Chưa có chỉ mục. Chạy: python3 scripts/lap_chi_muc.py")
tat_ca = [c for c in map(json.loads, open(p_cm, encoding="utf-8")) if c["dang_key"]]
p_ls = os.path.join(GOC, "du-lieu", "lich_su_dung.json")
lich_su = json.load(open(p_ls, encoding="utf-8")) if os.path.exists(p_ls) else {}

# ---------------------------------------------------------------- chọn câu
def mau_dang(m):
    r = re.escape(m).replace(r"\?", ".").replace(r"\*", ".*")
    return re.compile("^" + r + r"(?:[?\-].*)?$")

def hop_le(c, loai):
    if loai == "TN":
        return bool(c["dap_an"]) and len(c["dap_an"]) == 1
    if loai == "DS":
        return bool(c["dap_an"]) and len(c["dap_an"]) == 4
    if loai == "TLN":
        return bool(c["dap_an"])
    return True

def loc(loai, yc, da_chon):
    rx = mau_dang(yc["dang"])
    muc = yc.get("muc")
    muc = [muc] if isinstance(muc, str) else muc
    ds = [c for c in tat_ca if c["loai"] == loai and rx.match(c["dang_key"]) and c["ma"] not in da_chon
          and (not muc or c["muc_chuan"] in muc) and hop_le(c, loai)]
    rng.shuffle(ds)
    if mt.get("tranh_cau_da_dung", True):
        ds.sort(key=lambda c: len(lich_su.get(c["ma"], [])))
    return ds

def chon_bo_cau():
    da_chon, bo, thieu = set(), collections.OrderedDict(), []
    for phan in mt["phan"]:
        loai = phan["loai"]; bo.setdefault(loai, [])
        for yc in phan["yeu_cau"]:
            lay = loc(loai, yc, da_chon)[:yc["so"]]
            if len(lay) < yc["so"]:
                thieu.append(f"{loai} {yc['dang']} mức {yc.get('muc', '*')}: cần {yc['so']}, kho chỉ có {len(lay)}")
            for c in lay:
                da_chon.add(c["ma"]); bo[loai].append(c)
    return bo, thieu

THU_MUC = {"N": 0, "H": 1, "V": 2, "C": 3}
THU_MON = {"D": 0, "H": 1, "C": 2}
def khoa_noi_dung(c):
    return (c["lop"] or 0, THU_MON.get(c["mon"], 9), c["chuong"] or 0, c["bai"] or 0, c["dang"] or 0)

def sap_xep(ds):
    ds = list(ds)
    if mt.get("xao_cau", True):
        rng.shuffle(ds)
    kieu = mt.get("sap_xep", "ngau_nhien")
    if kieu == "do_kho":
        ds.sort(key=lambda c: THU_MUC.get(c["muc_chuan"], 9))
    elif kieu == "noi_dung":
        ds.sort(key=khoa_noi_dung)
    elif kieu == "noi_dung_do_kho":
        ds.sort(key=lambda c: (khoa_noi_dung(c)[:3], THU_MUC.get(c["muc_chuan"], 9)))
    return ds

# ---------------------------------------------------------------- xáo phương án
GOI_Y_DAP_AN = re.compile(r"([Cc]họn|[Đđ]áp án|[Pp]hương án)\s*(đúng\s*)?(là\s*)?\(?\s*(\\\w+\{)?[A-D]\b")
THAM_CHIEU_PA = re.compile(r"Cả|cả hai|Tất cả|tất cả|đáp án|phương án|\b[A-D] và [A-D]\b|\b[A-D], [A-D]\b")
def xao_phuong_an(k):
    m = tim_lenh(k, "choice")
    if not m:
        return k, None
    ds, _ = doc_tham_so(k, m.end(), 4)
    if not ds:
        return k, None
    dung0 = [i for i, x in enumerate(ds) if re.search(r"\\True(?![A-Za-z])", x[2])]
    if GOI_Y_DAP_AN.search(k[m.end():]) or any(THAM_CHIEU_PA.search(x[2]) for x in ds):
        return k, ("ABCD"[dung0[0]] if dung0 else None)
    hv = list(range(4)); rng.shuffle(hv)
    moi = [ds[i][2] for i in hv]
    out = k
    for (dau, cuoi, _), nd in sorted(zip(ds, moi), key=lambda x: -x[0][0]):
        out = out[:dau] + "{" + nd + "}" + out[cuoi:]
    dung = [i for i, nd in enumerate(moi) if re.search(r"\\True(?![A-Za-z])", nd)]
    return out, ("ABCD"[dung[0]] if dung else None)

# ---------------------------------------------------------------- soạn thân đề
SO_LA_MA = ["I", "II", "III", "IV"]
PHAN = {
    "TN": ("Câu trắc nghiệm nhiều phương án lựa chọn.", "Thí sinh trả lời từ câu 1 đến câu {n}. Mỗi câu hỏi thí sinh chỉ chọn một phương án.", "ex", "ans", "Ans"),
    "DS": ("Câu trắc nghiệm đúng sai.", "Thí sinh trả lời từ câu 1 đến câu {n}. Trong mỗi ý a), b), c), d) ở mỗi câu, thí sinh chọn đúng hoặc sai.", "ex", "ansbook", "Ansbook"),
    "TLN": ("Câu trắc nghiệm trả lời ngắn.", "Thí sinh trả lời từ câu 1 đến câu {n}.", "bt", "ansbt", "Ansbook"),
    "TL": ("Tự luận.", "Thí sinh trình bày lời giải từ câu 1 đến câu {n}.", "bt", None, None),
}
CHINH_THUC = mt.get("khung", "DeThiChinhThuc") == "DeThiChinhThuc"

def soan_ma_de(bo, ma_de):
    """Trả (thân đề, phần đáp án cuối, các dòng đáp án)."""
    khoi, dap_an_rows, bang = [], [], []
    stt = 0
    if CHINH_THUC:
        khoi.append(f"\\dauDe{{{ma_de}}}")
    else:
        khoi.append(f"\\section{{{mt.get('ten_ky_thi', ten)} -- Mã đề {ma_de}}}")
    for loai in CAC_LOAI:
        ds = bo.get(loai) or []
        if not ds:
            continue
        ds = sap_xep(ds)
        tieu, loi, ct, sf, tm = PHAN[loai]
        tep = f"{ten}_{ma_de}_{loai}"
        so_la_ma = SO_LA_MA[stt]; stt += 1
        if CHINH_THUC:
            khoi.append(f"\\phanDe{{\\textbf{{PHẦN {so_la_ma}. {tieu}}} {loi.format(n=len(ds))}}}")
        else:
            khoi.append(f"\\subsection{{Phần {so_la_ma}. {tieu[:-1]}}}\n{loi.format(n=len(ds))}")
        khoi.append(f"\\setcounter{{{ct}}}{{0}}")
        if sf:
            khoi.append(f"\\Opensolutionfile{{{sf}}}[{tm}/{tep}]")
        for i, c in enumerate(ds, 1):
            k, da = c["noi_dung"], c["dap_an"]
            if loai == "TN" and mt.get("xao_phuong_an", True):
                k, da = xao_phuong_an(k)
            khoi.append(k)
            dap_an_rows.append([ma_de, loai, i, da or "", c["ma"], c["id"]])
        if sf:
            khoi.append(f"\\Closesolutionfile{{{sf}}}")
            bang.append(f"\\par\\noindent\\textbf{{PHẦN {so_la_ma}.}}\\par\n\\begin{{flushleft}}\n\\input{{{tm}/{tep}}}\n\\end{{flushleft}}")
    if CHINH_THUC:
        khoi.append(f"\\hetDe{{{ma_de}}}")
    cuoi = ""
    if bang:
        tieu_da = (f"\\phanDapAn{{{ma_de}}}\n" if CHINH_THUC else
                   f"\\newpage\n\\begin{{center}}{{\\large\\bfseries ĐÁP ÁN -- MÃ ĐỀ {ma_de}}}\\end{{center}}\n")
        cuoi = tieu_da + "\n".join(bang)
    return "\n\n".join(khoi), cuoi, dap_an_rows

# ---------------------------------------------------------------- chạy
so_ma = int(mt["so_ma_de"]); bat_dau = int(mt["ma_de_bat_dau"])
bo_chung, thieu = chon_bo_cau()
for x in thieu:
    print("  ⚠ thiếu câu:", x)
dem = {l: len(v) for l, v in bo_chung.items() if v}
print("Đã chọn: " + ", ".join(f"{LOAI_TEN[k]} {v}" for k, v in dem.items()))
if CHINH_THUC and (dem.get("TN"), dem.get("DS"), dem.get("TLN")) != (12, 4, 6):
    print("  (lưu ý: cấu trúc đề tốt nghiệp 2025 là 12 TN – 4 Đúng/Sai – 6 Trả lời ngắn)")
if a.thu:
    for loai, ds in bo_chung.items():
        for c in ds:
            print(f"  {loai:<3} {c['id']:<10} {c['ma']}  {c['muc_chuan'] or '?'}  {c['ten_dang'] or ''}")
    sys.exit(0)

khung = mt["khung"]
src = os.path.join(GOC, "khung", khung)
out = os.path.join(GOC, "de-da-ra", ten)
if os.path.exists(out):
    sys.exit(f"Đã có de-da-ra/{ten}. Đổi 'ten' (hoặc --ten) hay đổi tên thư mục cũ.")
shutil.copytree(src, out, ignore=shutil.ignore_patterns("mau_de.tex", "*.bat"))
mau = doc(os.path.join(src, "mau_de.tex"))
for k, v in {"<<SO_GD>>": mt["so_gd"], "<<TRUONG>>": mt["truong"], "<<TEN_KY_THI>>": mt["ten_ky_thi"],
             "<<NAM_HOC>>": mt["nam_hoc"], "<<MON>>": mt["mon"], "<<THOI_GIAN>>": mt["thoi_gian"],
             "<<CHAN_TRANG>>": mt.get("chan_trang", mt["ten_ky_thi"])}.items():
    mau = mau.replace(k, re.sub(r"(?<!\\)([&%#])", r"\\\1", v))   # tự thoát ký tự & % # cho LaTeX
def tai_lieu(than, loi_giai):
    return mau.replace("<<CHE_DO_LOI_GIAI>>", "\\hienthiloigiai" if loi_giai else "\\anloigiai").replace("<<NOI_DUNG>>", than)

tat_ca_dap_an, ds_cau_dung, gop_de, gop_lg = [], {}, [], []
for s in range(so_ma):
    ma_de = str(bat_dau + s)
    bo = chon_bo_cau()[0] if (mt.get("moi_ma_de_cau_khac_nhau") and s > 0) else bo_chung
    for v in bo.values():
        for c in v:
            ds_cau_dung[c["ma"]] = c
    than, cuoi, rows = soan_ma_de(bo, ma_de)
    tat_ca_dap_an += rows
    ghi(os.path.join(out, f"{ten}_{ma_de}.tex"), tai_lieu(than, False))
    ghi(os.path.join(out, f"{ten}_{ma_de}_LoiGiai.tex"), tai_lieu(than + "\n\n" + cuoi, True))
    gop_de.append(than); gop_lg.append(than + "\n\n" + cuoi)
ghi(os.path.join(out, f"{ten}_TatCa_De.tex"), tai_lieu("\n\n\\newpage\n".join(gop_de), False))
ghi(os.path.join(out, f"{ten}_TatCa_LoiGiai.tex"), tai_lieu("\n\n\\newpage\n".join(gop_lg), True))

with open(os.path.join(out, "dap_an.csv"), "w", encoding="utf-8-sig", newline="") as fo:
    w = csv.writer(fo); w.writerow(["ma_de", "phan", "cau", "dap_an", "ma_cau", "ma_dang"]); w.writerows(tat_ca_dap_an)
# bảng ngang: mỗi mã đề một dòng
cot = []
for loai, phan_so in (("TN", "I"), ("DS", "II"), ("TLN", "III")):
    n = max([r[2] for r in tat_ca_dap_an if r[1] == loai] or [0])
    cot += [(loai, i, f"{phan_so}.{i}") for i in range(1, n + 1)]
with open(os.path.join(out, "dap_an_ngang.csv"), "w", encoding="utf-8-sig", newline="") as fo:
    w = csv.writer(fo); w.writerow(["Mã đề"] + [c[2] for c in cot])
    tra = {(r[0], r[1], r[2]): r[3] for r in tat_ca_dap_an}
    for s in range(so_ma):
        md = str(bat_dau + s)
        w.writerow([md] + [tra.get((md, l, i), "") for l, i, _ in cot])
with open(os.path.join(out, "danh_sach_cau.csv"), "w", encoding="utf-8-sig", newline="") as fo:
    w = csv.writer(fo); w.writerow(["ma_cau", "loai", "ma_dang", "muc", "ten_dang", "file"])
    for c in ds_cau_dung.values():
        w.writerow([c["ma"], c["loai"], c["id"], c["muc_chuan"], c["ten_dang"], c["file"]])
json.dump(mt, open(os.path.join(out, "ma_tran_da_dung.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

for ma in ds_cau_dung:
    lich_su.setdefault(ma, []).append(ten)
json.dump(lich_su, open(p_ls, "w", encoding="utf-8"), ensure_ascii=False)
print(f"Đã tạo {so_ma} mã đề trong de-da-ra/{ten}/ (đề, lời giải, file gộp, đáp án). Lịch sử dùng câu đã cập nhật.")

if a.bien_dich:
    for f in sorted(os.listdir(out)):
        if f.endswith(".tex") and f.startswith(ten):
            for _ in range(2):
                subprocess.run(["pdflatex", "-interaction=nonstopmode", f], cwd=out,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            ok = os.path.exists(os.path.join(out, f[:-4] + ".pdf"))
            print("  ", f[:-4] + ".pdf", "✓" if ok else "✗ (xem file .log)")
