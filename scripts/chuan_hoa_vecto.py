# -*- coding: utf-8 -*-
"""
CHUẨN HOÁ DẤU VECTƠ NGẮN → VECTƠ DÀI TRONG TOÀN BỘ DỮ LIỆU NGÂN HÀNG.
  \\vec{AB}, \\vec{a}, \\vec a, \\vv{AB}  →  \\overrightarrow{AB}, \\overrightarrow{a}

Chạy:
  python3 scripts/chuan_hoa_vecto.py         # chuyển đổi và lập lại chỉ mục
  python3 scripts/chuan_hoa_vecto.py --thu   # chỉ thống kê, chưa ghi file
"""
import os, sys, glob, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nh_core import GOC, chuan_vecto

THU_MUC = [
    os.path.join(GOC, "cau-hoi"),
    os.path.join(GOC, "cau-hoi-ts10"),
    os.path.join(GOC, "du-lieu", "kien_thuc"),
    os.path.join(GOC, "du-lieu", "phuong_phap"),
]

def chay(thu=False, in_ra=print):
    tong_file, tong_lan = 0, 0
    for tm in THU_MUC:
        if not os.path.isdir(tm):
            continue
        for p in sorted(glob.glob(os.path.join(tm, "**", "*.tex"), recursive=True)):
            goc = open(p, encoding="utf-8", errors="ignore").read()
            moi, n = chuan_vecto(goc)
            if n:
                tong_file += 1
                tong_lan += n
                if not thu:
                    open(p, "w", encoding="utf-8").write(moi)
    in_ra(f"{'[XEM TRƯỚC] ' if thu else ''}Đã chuyển {tong_lan:,} dấu vectơ ngắn → \\overrightarrow trong {tong_file} file.")
    if not thu and tong_lan:
        in_ra("Đang cập nhật lại chỉ mục ngân hàng…")
        subprocess.run([sys.executable or "python3", os.path.join(GOC, "scripts", "lap_chi_muc.py")], cwd=GOC, check=True)
    return tong_file, tong_lan

if __name__ == "__main__":
    chay(thu=("--thu" in sys.argv))
