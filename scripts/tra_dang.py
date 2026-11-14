# -*- coding: utf-8 -*-
"""
TRA MÃ DẠNG trong danh mục (cho Antigravity / thầy chọn đúng %[mã] khi soạn câu).
  python3 scripts/tra_dang.py "tich vo huong"            # tìm theo từ khoá (không dấu cũng được)
  python3 scripts/tra_dang.py --tien-to 0H5              # mọi dạng của lớp 10, Hình, chương 5
  python3 scripts/tra_dang.py --tien-to 0H5?3 --it 20    # các dạng của bài 3 đang có < 20 câu
  python3 scripts/tra_dang.py "cap so cong" --json
Mã: lớp (0=10, 1=11, 2=12, 6…9=THCS) · môn · chương · ? (thay bằng N/H/V/C) · bài - dạng.
"""
import os, sys, csv, json, argparse, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nh_core import GOC

def kd(s):
    s = (s or "").replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tu_khoa", nargs="*")
    ap.add_argument("--tien-to", default="", help="vd 0H5 hoặc 0H5?3")
    ap.add_argument("--it", type=int, help="chỉ hiện dạng có ít hơn N câu trong kho")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    p = os.path.join(GOC, "du-lieu", "danh_muc_ma_dang.csv")
    if not os.path.exists(p):
        sys.exit("Chưa có du-lieu/danh_muc_ma_dang.csv — chạy: python3 scripts/lap_chi_muc.py")
    rows = list(csv.DictReader(open(p, encoding="utf-8-sig")))
    tk = kd(" ".join(a.tu_khoa)).split()
    kq = []
    for r in rows:
        ma = r["ma_dang"].strip()
        if a.tien_to and not ma.startswith(a.tien_to):
            continue
        chu = kd(" ".join([ma, r["chuong"], r["bai"], r["dang"]]))
        if tk and not all(w in chu for w in tk):
            continue
        so = int(r.get("so_cau_trong_kho") or 0)
        if a.it is not None and so >= a.it:
            continue
        kq.append({"ma_dang": ma, "lop": r["lop"], "chuong": r["chuong"].strip(), "bai": r["bai"].strip(),
                   "dang": r["dang"].strip(), "so_cau": so})
    if a.json:
        print(json.dumps(kq, ensure_ascii=False, indent=1)); return
    if not kq:
        print("Không thấy dạng nào khớp."); return
    bai_cu = None
    for x in kq:
        if (x["lop"], x["bai"]) != bai_cu:
            bai_cu = (x["lop"], x["bai"])
            print(f"\n■ Lớp {x['lop']} · {x['chuong']} · {x['bai']}")
        print(f"  {x['ma_dang']:<10} {x['so_cau']:>4} câu  {x['dang']}")
    print(f"\n{len(kq)} dạng. Thay '?' bằng mức N/H/V/C khi ghi %[mã].")

if __name__ == "__main__":
    main()
