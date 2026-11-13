# -*- coding: utf-8 -*-
"""
BƯỚC 3: trộn đề theo ma trận.
Cách chạy:  python3 scripts/tron_de.py ma-tran/vi_du_GHK1_lop12.json
Tuỳ chọn:   --thu           chỉ chọn câu và in thống kê, không ghi file, không ghi lịch sử
            --bien-dich     gọi pdflatex biên dịch luôn (cần LaTeX có gói vietnam)
Kết quả:    de-da-ra/<ten>/  gồm khung LaTeX + <ten>_<mã đề>.tex (đề) + <ten>_<mã đề>_LoiGiai.tex
            + dap_an.csv (mọi mã đề, nạp được vào app chấm) + danh_sach_cau.csv
"""
import os, sys, json, re, random, shutil, csv, argparse, sqlite3, subprocess, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nh_core import *

ap = argparse.ArgumentParser()
ap.add_argument("ma_tran")
ap.add_argument("--thu", action="store_true")
ap.add_argument("--bien-dich", action="store_true")
a = ap.parse_args()

mt = json.load(open(a.ma_tran, encoding="utf-8"))
ten = mt["ten"]
rng = random.Random(mt.get("seed", int(time.time())))
quy_doi = cau_hinh().get("quy_doi_muc", {})
p_cm = os.path.join(GOC, "du-lieu", "chi_muc.jsonl")
if not os.path.exists(p_cm):
    sys.exit("Chưa có chỉ mục. Chạy: python3 scripts/lap_chi_muc.py")
tat_ca = [c for c in map(json.loads, open(p_cm, encoding="utf-8")) if c["dang_key"]]
p_ls = os.path.join(GOC, "du-lieu", "lich_su_dung.json")
lich_su = json.load(open(p_ls, encoding="utf-8")) if os.path.exists(p_ls) else {}

def mau_dang(m):
    r = re.escape(m).replace(r"\?", ".").replace(r"\*", ".*")
    return re.compile("^" + r + r"(?:[?\-].*)?$")

def loc(loai, yc, da_chon):
    rx = mau_dang(yc["dang"])
    muc = yc.get("muc")
    muc = [muc] if isinstance(muc, str) else muc
    ds = [c for c in tat_ca if c["loai"] == loai and rx.match(c["dang_key"]) and c["ma"] not in da_chon
          and (not muc or c["muc_chuan"] in muc)
          and (loai != "TN" or (c["dap_an"] and len(c["dap_an"]) == 1))
          and (loai != "DS" or (c["dap_an"] and len(c["dap_an"]) == 4))]
    rng.shuffle(ds)
    if mt.get("tranh_cau_da_dung", True):
        ds.sort(key=lambda c: len(lich_su.get(c["ma"], [])))
    return ds

THU_TU = ["TN", "DS", "TLN", "TL"]
def chon_bo_cau():
    da_chon, bo, thieu = set(), {}, []
    for phan in mt["phan"]:
        loai = phan["loai"]; bo.setdefault(loai, [])
        for yc in phan["yeu_cau"]:
            ung = loc(loai, yc, da_chon)
            lay = ung[:yc["so"]]
            if len(lay) < yc["so"]:
                thieu.append(f"{loai} {yc['dang']} mức {yc.get('muc','*')}: cần {yc['so']}, chỉ có {len(lay)}")
            for c in lay:
                da_chon.add(c["ma"]); bo[loai].append(c)
    return bo, thieu

GOI_Y_DAP_AN = re.compile(r"([Cc]họn|[Đđ]áp án|[Pp]hương án)\s*(đúng\s*)?(là\s*)?\(?\s*(\\\w+\{)?[A-D]\b")
THAM_CHIEU_PA = re.compile(r"Cả|cả hai|Tất cả|tất cả|đáp án|phương án|\b[A-D] và [A-D]\b|\b[A-D], [A-D]\b")
def xao_phuong_an(k):
    """Xáo 4 phương án của \\choice. Trả (khối mới, đáp án mới). Bỏ qua nếu lời giải/phương án nhắc tới chữ cái."""
    m = tim_lenh(k, "choice")
    if not m:
        return k, None
    ds, _ = doc_tham_so(k, m.end(), 4)
    if not ds:
        return k, None
    lg = k[m.end():]
    if GOI_Y_DAP_AN.search(lg) or any(THAM_CHIEU_PA.search(x[2]) for x in ds):
        dung = [i for i, x in enumerate(ds) if re.search(r"\\True(?![A-Za-z])", x[2])]
        return k, "ABCD"[dung[0]] if dung else None
    hv = list(range(4)); rng.shuffle(hv)
    moi = [ds[i][2] for i in hv]
    out = k
    for (dau, cuoi, _), nd in sorted(zip(ds, moi), key=lambda x: -x[0][0]):
        out = out[:dau] + "{" + nd + "}" + out[cuoi:]
    dung = [i for i, nd in enumerate(moi) if re.search(r"\\True(?![A-Za-z])", nd)]
    return out, ("ABCD"[dung[0]] if dung else None)

TIEU_DE_PHAN = {
    "TN": ("Phần trắc nghiệm nhiều lựa chọn", "Câu trắc nghiệm nhiều phương án lựa chọn. Thí sinh trả lời từ câu 1 đến câu {n}. Mỗi câu hỏi thí sinh chỉ chọn một phương án.", "ex", "ans", "Ans"),
    "DS": ("Phần trắc nghiệm đúng sai", "Câu trắc nghiệm đúng sai. Thí sinh trả lời từ câu 1 đến câu {n}. Trong mỗi ý a), b), c), d) ở mỗi câu, thí sinh chọn đúng hoặc sai.", "ex", "ansbook", "Ansbook"),
    "TLN": ("Phần trả lời ngắn", "Câu trắc nghiệm trả lời ngắn. Thí sinh trả lời từ câu 1 đến câu {n}.", "bt", "ansbt", "Ansbook"),
    "TL": ("Phần tự luận", "Thí sinh trình bày lời giải từ câu 1 đến câu {n}.", "bt", None, None),
}

def bo_nguon(k):
    return k  # giữ nguyên khối câu (có %[mã dạng]%[ma:..] trong chú thích, không ảnh hưởng bản in)

def soan_ma_de(bo, ma_de):
    phan_tex, dap_an_rows, cuoi = [], [], []
    for loai in THU_TU:
        ds = list(bo.get(loai, []))
        if not ds:
            continue
        if mt.get("xao_cau", True):
            rng.shuffle(ds)
        tieu, loi, ct, sf, thu_muc = TIEU_DE_PHAN[loai]
        tep = f"{ten}_{ma_de}_{loai}"
        dong = [f"\\subsection{{{tieu}}}", loi.format(n=len(ds)), f"\\setcounter{{{ct}}}{{0}}"]
        if sf:
            dong.append(f"\\Opensolutionfile{{{sf}}}[{thu_muc}/{tep}]")
        for i, c in enumerate(ds, 1):
            k = c["noi_dung"]; da = c["dap_an"]
            if loai == "TN" and mt.get("xao_phuong_an", True):
                k, da = xao_phuong_an(k)
            dong.append(f"%%%==================== {loai} câu {i} ====================%%%\n{k}")
            dap_an_rows.append([ma_de, loai, i, da or "", c["ma"], c["id"]])
        if sf:
            dong.append(f"\\Closesolutionfile{{{sf}}}")
            cuoi.append(f"\\subsection{{{tieu}}}\n\\begin{{flushleft}}\n\t\\input{{{thu_muc}/{tep}}}\n\\end{{flushleft}}")
        phan_tex.append("\n".join(dong))
    than = [f"\\section{{{mt.get('tieu_de', ten)} — Mã đề {ma_de}}}"] + phan_tex
    if cuoi:
        than += ["\\newpage", "\\begin{center}\n\t{\\Large\\bfseries\\sffamily PHẦN ĐÁP ÁN}\n\\end{center}",
                 "\\setcounter{subsection}{0}"] + cuoi
    return "\n\n".join(than), dap_an_rows

# ---------------------------------------------------------------- chạy
so_ma = int(mt.get("so_ma_de", 1)); bat_dau = int(mt.get("ma_de_bat_dau", 101))
khac_cau = mt.get("moi_ma_de_cau_khac_nhau", False)
bo_chung, thieu = chon_bo_cau()
for x in thieu:
    print("  ⚠ thiếu câu:", x)
tong = sum(len(v) for v in bo_chung.values())
print(f"Đã chọn {tong} câu: " + ", ".join(f"{LOAI_TEN[k]} {len(v)}" for k, v in bo_chung.items()))
if a.thu:
    for loai, ds in bo_chung.items():
        for c in ds:
            print(f"  {loai} {c['id']:<10} {c['ma']}  {c['ten_dang'] or ''}")
    sys.exit(0)

khung = mt.get("khung", cau_hinh().get("khung_mac_dinh", "DeThi"))
src = os.path.join(GOC, "khung", khung)
out = os.path.join(GOC, "de-da-ra", ten)
if os.path.exists(out):
    sys.exit(f"Đã có de-da-ra/{ten}. Đổi 'ten' trong ma trận hoặc đổi tên thư mục cũ.")
shutil.copytree(src, out, ignore=shutil.ignore_patterns("mau_de.tex", "*.bat"))
mau = doc(os.path.join(src, "mau_de.tex")).replace("<<CHAN_TRANG>>", mt.get("chan_trang", mt.get("tieu_de", ten)))

tat_ca_dap_an, ds_cau_dung = [], {}
for s in range(so_ma):
    ma_de = str(bat_dau + s)
    bo = chon_bo_cau()[0] if (khac_cau and s > 0) else bo_chung
    for v in bo.values():
        for c in v:
            ds_cau_dung[c["ma"]] = c
    noi_dung, rows = soan_ma_de(bo, ma_de)
    tat_ca_dap_an += rows
    ghi(os.path.join(out, f"{ten}_{ma_de}.tex"), mau.replace("<<CHE_DO_LOI_GIAI>>", "\\anloigiai").replace("<<NOI_DUNG>>", noi_dung))
    ghi(os.path.join(out, f"{ten}_{ma_de}_LoiGiai.tex"), mau.replace("<<CHE_DO_LOI_GIAI>>", "\\hienthiloigiai").replace("<<NOI_DUNG>>", noi_dung))

with open(os.path.join(out, "dap_an.csv"), "w", encoding="utf-8-sig", newline="") as fo:
    w = csv.writer(fo); w.writerow(["ma_de", "phan", "cau", "dap_an", "ma_cau", "ma_dang"]); w.writerows(tat_ca_dap_an)
with open(os.path.join(out, "danh_sach_cau.csv"), "w", encoding="utf-8-sig", newline="") as fo:
    w = csv.writer(fo); w.writerow(["ma_cau", "loai", "ma_dang", "muc", "ten_dang", "file"])
    for c in ds_cau_dung.values():
        w.writerow([c["ma"], c["loai"], c["id"], c["muc_chuan"], c["ten_dang"], c["file"]])
json.dump(mt, open(os.path.join(out, "ma_tran_da_dung.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

for ma in ds_cau_dung:
    lich_su.setdefault(ma, []).append(ten)
json.dump(lich_su, open(p_ls, "w", encoding="utf-8"), ensure_ascii=False)
print(f"Đã tạo {so_ma} mã đề trong de-da-ra/{ten}/ (đề + lời giải + dap_an.csv). Lịch sử dùng câu đã cập nhật.")

if a.bien_dich:
    for f in sorted(os.listdir(out)):
        if f.endswith(".tex") and f.startswith(ten):
            for _ in range(2):
                subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", f], cwd=out,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("  ", f.replace(".tex", ".pdf"), "✓" if os.path.exists(os.path.join(out, f[:-4] + ".pdf")) else "✗ (xem file .log)")
