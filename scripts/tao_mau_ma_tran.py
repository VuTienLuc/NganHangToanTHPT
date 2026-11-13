# -*- coding: utf-8 -*-
"""
Sinh BẢNG MA TRẬN (CSV, mở bằng Excel/Numbers) để thầy điền số câu cần lấy.
  python3 scripts/tao_mau_ma_tran.py GHK1_12 --pham-vi 2D1,2D2,2H2
  python3 scripts/tao_mau_ma_tran.py HK1_10 --pham-vi 0D1,0D2,0D3,0H4 --cham-phay   (Excel tiếng Việt)
Mỗi dòng là một dạng toán. Các cột "kho_..." cho biết kho đang có bao nhiêu câu theo mức N/H/V/C.
Thầy điền số vào các cột TN_N … TL_C (để trống = 0), lưu lại dạng CSV, rồi:
  python3 scripts/tron_de.py ma-tran/GHK1_12.csv
Thông tin đầu đề (Sở, trường, kỳ thi…) đặt trong cau_hinh.json → "thong_tin_de",
hoặc viết file JSON có "ma_tran_csv": "ma-tran/GHK1_12.csv" kèm các thông tin đó.
"""
import os, sys, json, csv, argparse, collections, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nh_core import *

ap = argparse.ArgumentParser()
ap.add_argument("ten")
ap.add_argument("--pham-vi", required=True, help="tiền tố mã dạng, cách nhau dấu phẩy: 2D1 (cả chương), 2D1?2 (bài 2)")
ap.add_argument("--cham-phay", action="store_true", help="dùng dấu ; (Excel cài tiếng Việt)")
a = ap.parse_args()

id_map = tai_id_map()
p_cm = os.path.join(GOC, "du-lieu", "chi_muc.jsonl")
cau = [c for c in map(json.loads, open(p_cm, encoding="utf-8")) if c["dang_key"]]
tien_to = [x.strip() for x in a.pham_vi.split(",") if x.strip()]
def thuoc(k):
    return any(k.startswith(t) and (len(k) == len(t) or k[len(t)] in "?-") for t in tien_to)
def hop_le(c):
    l, d = c["loai"], c["dap_an"]
    return (l == "TL") or (l == "TN" and d and len(d) == 1) or (l == "DS" and d and len(d) == 4) or (l == "TLN" and d)

kho = collections.defaultdict(collections.Counter)
for c in cau:
    if thuoc(c["dang_key"]) and hop_le(c):
        kho[c["dang_key"]][(c["loai"], c["muc_chuan"])] += 1
dang = sorted(set(kho) | {k for k in id_map if thuoc(k)},
              key=lambda k: (k[0], "DHC".find(k[1]), int(re.match(r"..(\d+)", k).group(1)), int(k.split("?")[1].split("-")[0]), int(k.split("-")[1])))
if not dang:
    sys.exit("Không có dạng nào khớp phạm vi.")
L, M = ["TN", "DS", "TLN", "TL"], ["N", "H", "V", "C"]
p = os.path.join(GOC, "ma-tran", a.ten + ".csv")
if os.path.exists(p):
    sys.exit(f"Đã có {os.path.relpath(p, GOC)} — chọn tên khác.")
os.makedirs(os.path.dirname(p), exist_ok=True)
with open(p, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, delimiter=";" if a.cham_phay else ",")
    w.writerow(["ma_dang", "chuong", "bai", "dang"] + [f"kho_{l}(N/H/V/C)" for l in L] + [f"{l}_{m}" for l in L for m in M])
    for k in dang:
        t = id_map.get(k, {})
        w.writerow([k, t.get("chap_name", ""), t.get("lesson_name", ""), t.get("type_name", "")]
                   + ["/".join(str(kho[k][(l, m)]) for m in M) for l in L] + [""] * 16)
print(f"Đã tạo {os.path.relpath(p, GOC)}: {len(dang)} dạng. Mở bằng Excel/Numbers, điền số câu, lưu lại (CSV).")
