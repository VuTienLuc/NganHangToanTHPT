# -*- coding: utf-8 -*-
"""
NHẬP THÊM CÂU HỎI vào ngân hàng (cộng dồn, không ghi đè).
  python3 scripts/nhap_cau.py file1.tex [file2.tex ...] --thu    # chỉ báo cáo, chưa ghi gì
  python3 scripts/nhap_cau.py file1.tex [file2.tex ...]          # nhập thật
  Nhận cả .txt/.md (chứa khối \\begin{ex}…) và .json (mảng câu: khối tex, hoặc các trường Nội dung/Lựa chọn/Đáp án/Lời giải…,
  kể cả mẫu 13 trường). --ma-dang 2D1?1-2 : gán mã dạng cho câu chưa có mã ("?" = mức độ của câu).
Mỗi câu \\begin{ex}…\\end{ex} hoặc \\begin{bt}…\\end{bt} có mã %[2D1N1-2] được chép vào đúng file dạng
trong cau-hoi/ (tạo file mới nếu dạng chưa có). Câu chưa có mã vào cau-hoi/_chua_phan_loai/<tên file>.tex.
Câu trùng y hệt câu đã có trong ngân hàng bị bỏ qua. File bị mã hoá (lệnh rác) được tự gỡ.
Xong tự chạy lap_chi_muc.py.
"""
import os, sys, glob, json, re, argparse, subprocess, collections, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nh_core import *
import doc_nhap

def nhap(cac_file, thu=False, in_ra=print, ma_dang=None):
    id_map = tai_id_map()
    # 1. băm toàn bộ câu đang có để chống trùng
    da_co = {}
    for f in glob.glob(os.path.join(GOC, "cau-hoi", "**", "*.tex"), recursive=True):
        for k in tach_khoi(doc(f)):
            da_co[ma_bam(k)] = os.path.relpath(f, GOC)
    # 2. lệnh thật đã biết (để nhận ra lệnh rác)
    sty = (glob.glob(os.path.join(GOC, "khung", "*", "*.sty")) +
           glob.glob(os.path.join(GOC, "khung", "*", "Khaibao", "*.tex")))
    p_rac = os.path.join(GOC, "du-lieu", "lenh_rac.json")
    rac_da_biet = set(json.load(open(p_rac, encoding="utf-8"))) if os.path.exists(p_rac) else set()
    # từ vựng lệnh của ngân hàng hiện có (đã sạch) — lệnh trong file nhập mà nằm ngoài từ vựng này dễ là rác
    tu_vung = set()
    for f in glob.glob(os.path.join(GOC, "cau-hoi", "**", "*.tex"), recursive=True):
        tu_vung |= set(re.findall(r"\\([A-Za-z]+)", doc(f)))
    them = collections.defaultdict(list); bao_cao = []; tong = collections.Counter()
    for f in cac_file:
        try:
            t = doc_nhap.doc_tep(f, ma_dang)            # .tex/.txt/.md/.json → khối LaTeX
        except Exception as e:
            in_ra(f"{os.path.basename(f)}: không đọc được ({e})"); continue
        ten_nguon = os.path.splitext(os.path.basename(f))[0]
        hop = lenh_hop_le([t], sty)
        rac, _, dem = tim_lenh_rac([t], hop)
        nghi_ngo = []
        if len(rac) >= 20:                          # file mã hoá: gỡ thêm tên lạ không có trong ngân hàng
            sty_ten = {x for f in sty for x in re.findall(r"\\([A-Za-z]+)", doc(f))}
            dn = lenh_tu_dinh_nghia(t)
            them_rac = {k for k in dem if re.fullmatch(r"[a-z]{3,6}", k)
                        and k not in tu_vung and k not in sty_ten and k not in dn} | ({k for k in rac_da_biet if k in dem} - tu_vung)
            chuan = {l.strip() for l in open(os.path.join(GOC, "scripts", "lenh_tex_chuan.txt"), encoding="utf-8")}
            nghi_ngo = sorted(k for k in them_rac - rac if k in chuan)
            rac |= them_rac
        so_rac = sum(dem[k] for k in rac)
        if len(rac) >= 20:                          # file có dấu hiệu mã hoá → gỡ
            t = go_rac(t, rac)
            ldl = lenh_tu_dinh_nghia(t) - hop
            khoi = [go_rac_trong_cau(k, ldl) for k in tach_khoi(t)]
        else:
            so_rac = 0
            khoi = tach_khoi(t)
        tk = collections.Counter()
        for k in khoi:
            ma = ma_bam(k)
            if ma in da_co:
                tk["trung"] += 1; continue
            da_co[ma] = "(file đang nhập)"
            k = gan_ma(k, ma)
            info = phan_tich_cau(k)
            p = duong_dan_dang(info, id_map) or os.path.join("_chua_phan_loai", ten_khong_dau(ten_nguon, 60) + ".tex")
            them[p].append((info, k, ten_nguon))
            tk[info["loai"]] += 1
            if not info["dang_key"]:
                tk["chua_ma"] += 1
            if info["loai"] == "TN" and (not info["dap_an"] or len(info["dap_an"]) != 1):
                tk["loi_dap_an"] += 1
        tong.update(tk)
        bao_cao.append(f"{os.path.basename(f)}: {len(khoi)} câu — TN {tk['TN']}, ĐS {tk['DS']}, TLN {tk['TLN']}, TL {tk['TL']}"
                       f"; trùng bỏ {tk['trung']}; chưa có mã {tk['chua_ma']}; TN thiếu/thừa \\True {tk['loi_dap_an']}"
                       + (f"; đã gỡ {so_rac} lệnh rác" if so_rac else "")
                       + (f"\n   (đã gỡ cả các tên trùng lệnh LaTeX, nếu đề lỗi thì kiểm tra: {', '.join(nghi_ngo[:20])})" if nghi_ngo else ""))
    for d in bao_cao:
        in_ra(d)
    moi = sum(len(v) for v in them.values())
    dang_moi = [p for p in them if not os.path.exists(os.path.join(GOC, "cau-hoi", p))]
    in_ra(f"→ Sẽ thêm {moi} câu vào {len(them)} file dạng ({len(dang_moi)} file dạng mới).")
    for p in sorted(them)[:15]:
        in_ra(f"   + {len(them[p]):3d} câu → cau-hoi/{p}")
    if len(them) > 15:
        in_ra(f"   … và {len(them) - 15} file khác")
    if thu or not moi:
        if thu: in_ra("(Chế độ xem trước: chưa ghi gì.)")
        return moi
    # 3. ghi: nối vào cuối file dạng (tạo mới nếu chưa có)
    ngay = time.strftime("%d/%m/%Y")
    for p, ds in them.items():
        dich = os.path.join(GOC, "cau-hoi", p)
        if os.path.exists(dich):
            cu = doc(dich).rstrip("\n") + "\n"
        else:
            i0 = ds[0][0]; ten = id_map.get(i0["dang_key"] or "", {})
            dau = ["%" * 70]
            if ten:
                dau += [f"% Lớp {i0['lop']} | {ten['chap_name']} | {ten['lesson_name']}", f"% Dạng {i0['dang_key']}: {ten['type_name']}"]
            elif i0["dang_key"]:
                dau += [f"% Lớp {i0['lop']} | Dạng {i0['dang_key']}"]
            else:
                dau += ["% Câu chưa có mã dạng — gắn %[..] rồi chuyển vào đúng file dạng"]
            cu = "\n".join(dau + ["%" * 70, ""]) + "\n"
        moi_txt = "".join(f"\n% nguồn: {ng} (nhập {ngay})\n{k}\n" for _, k, ng in ds)
        ghi(dich, cu + moi_txt)
    in_ra(f"Đã nhập {moi} câu. Đang cập nhật chỉ mục…")
    r = subprocess.run([sys.executable, os.path.join(GOC, "scripts", "lap_chi_muc.py")], cwd=GOC, capture_output=True, text=True)
    in_ra((r.stdout or "") + (r.stderr or ""))
    return moi

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--thu", action="store_true")
    ap.add_argument("--ma-dang", help="gán mã dạng cho câu chưa có mã, vd 2D1?1-2 (? = theo mức độ câu)")
    a = ap.parse_args()
    fs = [f for f in a.files if os.path.isfile(f)]
    if not fs:
        sys.exit("Không thấy file nào.")
    nhap(fs, a.thu, ma_dang=a.ma_dang)
