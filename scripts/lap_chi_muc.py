# -*- coding: utf-8 -*-
"""
BƯỚC 2 (chạy lại mỗi khi thầy thêm/sửa câu): đọc toàn bộ cau-hoi/**/*.tex rồi
  - gắn mã câu %[ma:xxxxxxxx] cho câu mới chưa có mã
  - lập chỉ mục: du-lieu/nganhang.sqlite + du-lieu/chi_muc.jsonl
  - thống kê theo dạng × mức × loại: du-lieu/thong_ke_theo_dang.csv
  - kiểm tra lỗi: du-lieu/bao_cao_kiem_tra.md
Cách chạy:  python3 scripts/lap_chi_muc.py
"""
import os, sys, glob, json, sqlite3, csv, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nh_core import *

ch = cau_hinh()
quy_doi = ch.get("quy_doi_muc", {"N": "N", "H": "H", "V": "V", "C": "C"})
id_map = tai_id_map()
p_ls = os.path.join(GOC, "du-lieu", "lich_su_dung.json")
lich_su = json.load(open(p_ls, encoding="utf-8")) if os.path.exists(p_ls) else {}

ds_cau, loi = [], collections.defaultdict(list)
so_gan_ma = 0
for f in sorted(glob.glob(os.path.join(GOC, "cau-hoi", "**", "*.tex"), recursive=True)):
    rel = os.path.relpath(f, GOC)
    t = doc(f); doi = False
    def gan(m):
        global so_gan_ma
        k = m.group(0)
        if not MA_CAU.search(k.split("\n", 1)[0]):
            so_gan_ma += 1
            return gan_ma(k, ma_bam(k))
        return k
    t2 = KHOI.sub(gan, t)
    if t2 != t:
        ghi(f, t2); t = t2
    for k in tach_khoi(t):
        info = phan_tich_cau(k)
        ten = id_map.get(info["dang_key"] or "", {})
        info.update(file=rel, muc_chuan=quy_doi.get(info["muc"] or "", None),
                    ten_chuong=ten.get("chap_name"), ten_bai=ten.get("lesson_name"), ten_dang=ten.get("type_name"),
                    so_lan_dung=len(lich_su.get(info["ma"], [])), noi_dung=k)
        ds_cau.append(info)
        nhan = f"`{info['ma']}` {rel}"
        if not info["id"]:
            loi["Thiếu mã dạng %[..]"].append(nhan)
        elif not ten:
            loi["Mã dạng không có trong id_map.json"].append(f"{nhan} ({info['dang_key']})")
        if info["muc"] and not info["muc_chuan"]:
            loi["Mức độ chưa quy đổi (thêm vào cau_hinh.json)"].append(f"{nhan} ({info['muc']})")
        if info["loai"] == "TN" and (not info["dap_an"] or len(info["dap_an"]) != 1):
            loi["Trắc nghiệm không có đúng 1 \\True"].append(f"{nhan} (đáp án: {info['dap_an']})")
        if info["loai"] == "DS" and (not info["dap_an"] or len(info["dap_an"]) != 4):
            loi["Đúng/Sai không đọc được 4 ý"].append(nhan)
        if info["loai"] == "TLN" and not info["dap_an"]:
            loi["Trả lời ngắn thiếu \\shortans"].append(nhan)
        if not info["co_loi_giai"]:
            loi["Thiếu lời giải"].append(nhan)

dem_ma = collections.Counter(c["ma"] for c in ds_cau)
for c in ds_cau:
    if dem_ma[c["ma"]] > 1:
        loi["Mã câu bị trùng (câu lặp hoặc chép trùng)"].append(f"`{c['ma']}` {c['file']}")

# ---- SQLite + JSONL
dl = os.path.join(GOC, "du-lieu"); os.makedirs(dl, exist_ok=True)
cot = ["ma", "id", "dang_key", "lop", "mon", "chuong", "bai", "dang", "muc", "muc_chuan", "loai", "dap_an",
       "co_loi_giai", "co_hinh", "so_lan_dung", "ten_chuong", "ten_bai", "ten_dang", "file", "moi_truong", "noi_dung"]
p_db = os.path.join(dl, "nganhang.sqlite")
import tempfile
thu_muc_tam = tempfile.mkdtemp()
tam = os.path.join(thu_muc_tam, "nganhang.sqlite")   # tạo ở thư mục tạm rồi chép sang (tránh lỗi khoá file trên iCloud)
db = sqlite3.connect(tam)
db.execute("DROP TABLE IF EXISTS cau_hoi"); db.execute("DROP VIEW IF EXISTS thong_ke")
db.execute(f"CREATE TABLE cau_hoi ({', '.join(c + (' TEXT' if c not in ('lop','chuong','bai','dang','co_loi_giai','co_hinh','so_lan_dung') else ' INTEGER') for c in cot)})")
db.executemany(f"INSERT INTO cau_hoi VALUES ({','.join('?' * len(cot))})", [[c.get(k) for k in cot] for c in ds_cau])
db.execute("CREATE INDEX i_dang ON cau_hoi(dang_key, loai, muc_chuan)")
db.execute("CREATE VIEW thong_ke AS SELECT lop, dang_key, ten_dang, loai, muc_chuan, COUNT(*) so_cau FROM cau_hoi GROUP BY 1,2,3,4,5")
db.commit(); db.close()
import shutil
shutil.copyfile(tam, p_db); shutil.rmtree(thu_muc_tam, ignore_errors=True)
with open(os.path.join(dl, "chi_muc.jsonl"), "w", encoding="utf-8") as fo:
    for c in ds_cau:
        fo.write(json.dumps({k: c.get(k) for k in cot}, ensure_ascii=False) + "\n")

# ---- thống kê theo dạng
bang = collections.defaultdict(collections.Counter)
for c in ds_cau:
    bang[c["dang_key"] or "(chưa mã)"][f"{c['loai']}-{c['muc_chuan'] or '?'}"] += 1
cot_tk = [f"{l}-{m}" for l in ("TN", "DS", "TLN", "TL") for m in ("N", "H", "V", "C", "?")]
with open(os.path.join(dl, "thong_ke_theo_dang.csv"), "w", encoding="utf-8-sig", newline="") as fo:
    w = csv.writer(fo); w.writerow(["dang_key", "chuong", "bai", "dang", "tong"] + cot_tk)
    for k in sorted(bang):
        ten = id_map.get(k, {})
        w.writerow([k, ten.get("chap_name", ""), ten.get("lesson_name", ""), ten.get("type_name", ""),
                    sum(bang[k].values())] + [bang[k][x] or "" for x in cot_tk])

# ---- báo cáo
tk_loai = collections.Counter(c["loai"] for c in ds_cau)
tk_lop = collections.Counter(c["lop"] for c in ds_cau)
dang_mong = [k for k in id_map if sum(bang.get(k, {}).values()) < 5]
L = ["# Báo cáo kiểm tra ngân hàng", "",
     f"- Tổng số câu: **{len(ds_cau):,}** trong {len(set(c['file'] for c in ds_cau))} file",
     "- Theo lớp: " + ", ".join(f"" + (f"lớp {k}" if k else "chưa mã") + f": {v:,}" for k, v in sorted(tk_lop.items(), key=lambda x: (x[0] is None, x[0] or 0))),
     "- Theo loại: " + ", ".join(f"{LOAI_TEN[k]}: {v:,}" for k, v in tk_loai.items()),
     f"- Câu mới vừa được gắn mã: {so_gan_ma}",
     f"- Dạng trong id_map có dưới 5 câu: {len(dang_mong)}", ""]
for ten_loi, ds in sorted(loi.items(), key=lambda x: -len(x[1])):
    L += [f"## {ten_loi}: {len(ds)}", ""]
    L += [f"- {x}" for x in ds[:40]]
    if len(ds) > 40:
        L.append(f"- … và {len(ds) - 40} câu nữa (lọc trong nganhang.sqlite)")
    L.append("")
if dang_mong:
    L += ["## Dạng còn mỏng (< 5 câu)", ""] + [f"- {k}: {id_map[k]['type_name']} — {sum(bang.get(k, {}).values())} câu" for k in dang_mong]
ghi(os.path.join(dl, "bao_cao_kiem_tra.md"), "\n".join(L) + "\n")
print(f"Đã lập chỉ mục {len(ds_cau):,} câu. Gắn mã mới: {so_gan_ma}.")
for ten_loi, ds in loi.items():
    print(f"  - {ten_loi}: {len(ds)}")
print("Xem: du-lieu/bao_cao_kiem_tra.md, du-lieu/thong_ke_theo_dang.csv")
