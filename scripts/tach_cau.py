# -*- coding: utf-8 -*-
"""
BƯỚC 1 (chạy một lần): chuyển dữ liệu của phần mềm NganHangTHPT sang ngân hàng cá nhân.
  - gỡ lệnh rác mã hoá
  - tách từng câu, gắn mã câu %[ma:xxxxxxxx]
  - bỏ câu trùng y hệt
  - ghi ra cau-hoi/lopXX/<chương>/<dạng>.tex
Cách chạy (trong thư mục NganHangCaNhan):   python3 scripts/tach_cau.py
Thêm nguồn khác:                            python3 scripts/tach_cau.py --nguon "../Data_Lop12/*.tex"
Ghi đè thư mục cau-hoi đã có:               python3 scripts/tach_cau.py --ghi-de
"""
import os, sys, glob, json, shutil, argparse, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nh_core import *

ap = argparse.ArgumentParser()
ap.add_argument("--nguon", action="append", help="mẫu đường dẫn file .tex nguồn (tính từ thư mục NganHangTHPT1.3)")
ap.add_argument("--ghi-de", action="store_true")
a = ap.parse_args()

mau = a.nguon or ["DuLieuNganHang/*/*.tex"]
files = sorted({f for m in mau for f in glob.glob(os.path.join(KHO_GOC, m))})
if not files:
    sys.exit("Không tìm thấy file nguồn.")
dich = os.path.join(GOC, "cau-hoi")
if os.path.isdir(dich) and any(os.scandir(dich)) and not a.ghi_de:
    sys.exit("Thư mục cau-hoi đã có dữ liệu (có thể thầy đã sửa). Thêm --ghi-de nếu muốn tạo lại từ đầu.")
if a.ghi_de and os.path.isdir(dich):
    import time
    cu = os.path.join(GOC, "_cu", "cau-hoi_" + time.strftime("%Y%m%d_%H%M%S"))
    os.makedirs(os.path.dirname(cu), exist_ok=True)
    os.rename(dich, cu)
    print("Đã cất bản cũ vào", os.path.relpath(cu, GOC))

print(f"Đọc {len(files)} file nguồn...")
van_ban = {f: doc(f) for f in files}
sty = [f for d in ("DeThi", "Leftnote", "XBeamer/KhaibaoBM", "TBeamer/KhaibaoBM")
       for f in glob.glob(os.path.join(KHO_GOC, d, "*.sty")) + glob.glob(os.path.join(KHO_GOC, d, "Khaibao", "*.tex"))
       + glob.glob(os.path.join(KHO_GOC, d, "*.tex"))]
hop_le = lenh_hop_le(van_ban.values(), sty)
rac, nghi_van, dem = tim_lenh_rac(van_ban.values(), hop_le)
chuan = {l.strip() for l in open(os.path.join(GOC, "scripts", "lenh_tex_chuan.txt"), encoding="utf-8")}
lenh_sty = lenh_hop_le([], sty) - chuan if sty else set()
lenh_du_lieu = set()
for t in van_ban.values():
    lenh_du_lieu |= lenh_tu_dinh_nghia(t)
lenh_du_lieu -= chuan | lenh_sty
so_lan_rac = sum(dem[k] for k in rac)
print(f"Lệnh rác: {len(rac)} tên khác nhau, {so_lan_rac} lần chèn.")

id_map = tai_id_map()
os.makedirs(os.path.join(GOC, "du-lieu"), exist_ok=True)
for f in ("id_map.json", "idvn_map.json"):
    if os.path.exists(os.path.join(KHO_GOC, f)):
        shutil.copy(os.path.join(KHO_GOC, f), os.path.join(GOC, "du-lieu", f))

theo_file = collections.defaultdict(list)      # đường dẫn đích -> [(info, text, nguồn)]
da_co = {}                                       # ma -> nguồn đầu tiên
trung = collections.Counter(); tk_nguon = {}
muc_la = collections.Counter(); khong_ma = collections.Counter()
for f in files:
    t = go_rac(van_ban[f], rac)
    ten_nguon = os.path.splitext(os.path.basename(f))[0]
    khoi = tach_khoi(t)
    tk = collections.Counter()
    for k in khoi:
        k = go_rac_trong_cau(k, lenh_du_lieu)
        info = phan_tich_cau(k)
        ma = ma_bam(k)
        tk[info["loai"]] += 1
        if ma in da_co:
            trung[ten_nguon] += 1
            continue
        da_co[ma] = ten_nguon
        k = gan_ma(k, ma)
        if info["muc"] and info["muc"] not in "NHVC":
            muc_la[(ten_nguon, info["muc"])] += 1
        p = duong_dan_dang(info, id_map)
        if p is None:
            khong_ma[ten_nguon] += 1
            p = os.path.join("_chua_phan_loai", ten_nguon + ".tex")
        theo_file[p].append((info, k, ten_nguon))
    tk_nguon[ten_nguon] = (len(khoi), tk)
    print(f"  {ten_nguon}: {len(khoi)} câu")

THU_TU_MUC = {"N": 0, "H": 1, "V": 2, "C": 3}
tong = 0
for p, ds in sorted(theo_file.items()):
    ds.sort(key=lambda x: (LOAI_THU_TU[x[0]["loai"]], THU_TU_MUC.get(x[0]["muc"] or "", 9), x[0]["bai"] or 0))
    i0 = ds[0][0]
    ten = id_map.get(i0["dang_key"] or "", {})
    dau = ["%" * 70]
    if ten:
        dau += [f"% Lớp {i0['lop']} | {ten['chap_name']} | {ten['lesson_name']}",
                f"% Dạng {i0['dang_key']}: {ten['type_name']}"]
    elif i0["dang_key"]:
        dau += [f"% Lớp {i0['lop']} | Dạng {i0['dang_key']} (chưa có tên trong id_map.json)"]
    else:
        dau += ["% Câu chưa có mã dạng — cần gắn %[..] rồi chuyển vào đúng file dạng"]
    dau += [f"% Số câu: {len(ds)}  (sinh tự động bởi tach_cau.py; từ nay thầy sửa trực tiếp file này)", "%" * 70, ""]
    than = []
    loai_truoc = None
    for info, k, nguon in ds:
        if info["loai"] != loai_truoc:
            than.append(f"\n%%%%%%%%%%%%%%%% {LOAI_TEN[info['loai']].upper()} %%%%%%%%%%%%%%%%\n")
            loai_truoc = info["loai"]
        than.append(f"% nguồn: {nguon}\n{k}\n")
    ghi(os.path.join(dich, p), "\n".join(dau) + "\n".join(than))
    tong += len(ds)

# ---- báo cáo chuyển đổi
L = ["# Báo cáo chuyển đổi ngân hàng", "",
     f"- File nguồn: {len(files)}",
     f"- Lệnh rác đã gỡ: {len(rac):,} tên khác nhau, {so_lan_rac:,} lần chèn",
     f"- Tên lệnh rác trùng tên lệnh thật (giữ nguyên, cần soát khi biên dịch lỗi): {len(nghi_van)} — {', '.join(sorted(nghi_van)[:60])}",
     f"- Tổng câu đọc được: {sum(v[0] for v in tk_nguon.values()):,}",
     f"- Câu trùng y hệt đã bỏ: {sum(trung.values()):,}",
     f"- Câu giữ lại: {tong:,} trong {len(theo_file)} file dạng",
     f"- Câu chưa có mã dạng: {sum(khong_ma.values())} (ở cau-hoi/_chua_phan_loai)", "",
     "## Theo file nguồn", "", "| File | Số câu | TN | ĐS | TLN | TL | Trùng bỏ | Không mã |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
for n, (s, tk) in tk_nguon.items():
    L.append(f"| {n} | {s} | {tk['TN']} | {tk['DS']} | {tk['TLN']} | {tk['TL']} | {trung[n]} | {khong_ma[n]} |")
if muc_la:
    L += ["", "## Mức độ ngoài N/H/V/C (cần thầy quy đổi trong cau_hinh.json)", "", "| File | Mức | Số câu |", "|---|---|---:|"]
    for (n, m), s in sorted(muc_la.items()):
        L.append(f"| {n} | {m} | {s} |")
ghi(os.path.join(GOC, "du-lieu", "bao_cao_chuyen_doi.md"), "\n".join(L) + "\n")
json.dump(sorted(rac), open(os.path.join(GOC, "du-lieu", "lenh_rac.json"), "w"), ensure_ascii=False)
print(f"\nXong: {tong} câu → {len(theo_file)} file. Báo cáo: du-lieu/bao_cao_chuyen_doi.md")
print("Tiếp theo: python3 scripts/lap_chi_muc.py")
