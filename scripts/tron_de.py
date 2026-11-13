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

Kết quả: thư mục de-da-ra/<Tên kỳ thi> - <dd-mm-yyyy>/ gồm
  De_101.pdf…  LoiGiai_101.pdf…   (khi có --bien-dich và máy có pdflatex)
  DapAn.xlsx                      đáp án mọi mã đề theo mẫu Chấm Phiếu AI (sheet "Đáp án")
  tex/                            De_101.tex, De_101_LoiGiai.tex, TatCa_De.tex, khung LaTeX, dap_an.csv
"""
import os, sys, json, re, random, shutil, csv, argparse, subprocess, time, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nh_core import *

ap = argparse.ArgumentParser()
ap.add_argument("ma_tran")
ap.add_argument("--thu", action="store_true")
ap.add_argument("--bien-dich", action="store_true")
ap.add_argument("--word", action="store_true", help="xuất thêm Word theo mẫu K12Online (công thức Equation)")
ap.add_argument("--word-svg", action="store_true", help="xuất Word K12Online với công thức là ảnh SVG thẳng dòng")
ap.add_argument("--so-ma-de", type=int)
ap.add_argument("--ten")
a = ap.parse_args()

CH = cau_hinh()
THONG_TIN_MAC_DINH = {
    "so_gd": "SỞ GD&ĐT TP. HỒ CHÍ MINH", "truong": "TRƯỜNG THPT NGUYỄN HỮU CẢNH",
    "ten_ky_thi": "ĐỀ KIỂM TRA", "nam_hoc": "NĂM HỌC 2026 -- 2027", "mon": "TOÁN -- Lớp 12",
    "thoi_gian": "90 phút", "giao_vien": "Vũ Tiến Lực", "de_cuong": True, "khung": "DeThiChinhThuc", "so_ma_de": 4, "ma_de_bat_dau": 101,
    "xao_cau": True, "xao_phuong_an": True, "xao_y_dung_sai": True,
    "tiet_kiem": False, "co_chu": 12, "hai_cot": False, "sap_xep": "ngau_nhien",
    "moi_ma_de_cau_khac_nhau": False, "tranh_cau_da_dung": True, "bu_cung_nhom": True, "mo_rong_dang_khac": True,
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

NHOM_MUC = {"N": "NH", "H": "NH", "V": "VC", "C": "VC"}      # nhóm 1: nhận biết + thông hiểu; nhóm 2: vận dụng + VDC
CHE_DO_DA_DUNG = mt.get("cau_da_dung") or ("uu_tien" if mt.get("tranh_cau_da_dung", True) else "khong")

def so_lan_dung(c):
    return len(lich_su.get(c["ma"], []))

def ung_vien(loai, yc):
    """Các tầng câu ứng viên theo thứ tự ưu tiên: (danh sách, ghi chú bù)."""
    rx = mau_dang(yc["dang"])
    muc = yc.get("muc"); muc = [muc] if isinstance(muc, str) else list(muc or [])
    co_ban = [c for c in tat_ca if c["loai"] == loai and hop_le(c, loai)
              and (CHE_DO_DA_DUNG != "loai_bo" or not so_lan_dung(c))]
    tang = []
    def xen_ke_dang(ds):
        """Xếp xen kẽ theo dạng (dạng A, dạng B, dạng C, dạng A…) để chọn theo bài/chương được nhiều dạng khác nhau."""
        nhom = collections.OrderedDict()
        for c in ds:
            nhom.setdefault(c["dang_key"], []).append(c)
        hang = list(nhom.values()); rng.shuffle(hang)
        out = []
        while any(hang):
            for h in hang:
                if h:
                    out.append(h.pop(0))
        return out
    def them(ds, ghi_chu):
        ds = list(ds); rng.shuffle(ds)
        if CHE_DO_DA_DUNG == "uu_tien":
            ds = xen_ke_dang([c for c in ds if not so_lan_dung(c)]) + \
                 sorted(xen_ke_dang([c for c in ds if so_lan_dung(c)]), key=so_lan_dung)
        else:
            ds = xen_ke_dang(ds)
        tang.append((ds, ghi_chu))
    khop = [c for c in co_ban if rx.match(c["dang_key"])]
    them([c for c in khop if not muc or c["muc_chuan"] in muc], None)
    nhom = ({x for m in muc for x in NHOM_MUC.get(m, "")} - set(muc)) if muc else set()
    if mt.get("bu_cung_nhom", True) and nhom:
        them([c for c in khop if c["muc_chuan"] in nhom], "mức cùng nhóm (N↔H / V↔C)")
    if mt.get("mo_rong_dang_khac", True):
        mm = set(muc) | (nhom if mt.get("bu_cung_nhom", True) else set())
        k = yc["dang"]
        mb = re.match(r"(\d[A-Z]\d+)[?A-Z](\d+)-", k)
        mc = re.match(r"(\d[A-Z]\d+)", k)
        tien_to_bai = f"{mb.group(1)}?{mb.group(2)}-" if mb else None
        if tien_to_bai:
            them([c for c in co_ban if c["dang_key"].startswith(tien_to_bai) and not rx.match(c["dang_key"])
                  and (not mm or c["muc_chuan"] in mm)], "dạng khác cùng bài")
        if mc:
            them([c for c in co_ban if c["dang_key"].startswith(mc.group(1) + "?") and not rx.match(c["dang_key"])
                  and not (tien_to_bai and c["dang_key"].startswith(tien_to_bai))
                  and (not mm or c["muc_chuan"] in mm)], "bài khác cùng chương")
    return tang

def lap_ke_hoach(so_ma, khac_cau):
    """Chọn câu cho mọi mã đề một lượt. Thiếu câu đúng mức thì bù mức cùng nhóm (N↔H, V↔C),
    rồi dạng khác cùng bài, rồi bài khác cùng chương. Nhiều mã đề khác câu: rải đều câu bù cho các mã."""
    da_lay = set()
    bo = [collections.OrderedDict() for _ in range(so_ma)]
    ghi_chu, thieu = [], []
    for phan in mt["phan"]:
        loai = phan["loai"]
        for b in bo:
            b.setdefault(loai, [])
        for yc in phan["yeu_cau"]:
            k = int(yc["so"]); can = k * so_ma if khac_cau else k
            lay, co = [], set()
            for ds, gc in ung_vien(loai, yc):
                for c in ds:
                    if len(lay) >= can:
                        break
                    if c["ma"] in da_lay or c["ma"] in co:
                        continue
                    lay.append((c, gc)); co.add(c["ma"])
                if len(lay) >= can:
                    break
            da_lay |= co
            nhan = f"{LOAI_TEN[loai]} {yc['dang']} mức {yc.get('muc') or '*'}"
            bu = collections.Counter(gc for _, gc in lay if gc)
            if bu:
                ghi_chu.append(f"{nhan}: thiếu câu đúng mức → đã bù " + ", ".join(f"{v} câu {g}" for g, v in bu.items()))
            if len(lay) < k:
                thieu.append(f"{nhan}: cần {k}, kho (kể cả bù) chỉ có {len(lay)}")
            elif khac_cau and len(lay) < can:
                ghi_chu.append(f"{nhan}: có {len(lay)} câu cho {so_ma} mã đề × {k} → vài câu dùng chung giữa các mã")
            dong = [c for c, _ in lay]
            if not khac_cau:
                for b in bo:
                    b[loai].extend(dong[:k])
                continue
            # Chia câu cho các mã đề: mỗi lượt mỗi mã nhận 1 câu; ưu tiên dạng mà mã đó CHƯA có
            # và dạng ít được chia nhất → mỗi mã đề phủ nhiều dạng, các mã đề khác nhau về dạng.
            con = list(dong)                      # câu chưa chia (theo thứ tự ưu tiên)
            dem_dang = collections.Counter()
            rieng = [set() for _ in range(so_ma)]; dang_de = [collections.Counter() for _ in range(so_ma)]
            for _ in range(min(k, len(dong))):
                for s_ in range(so_ma):
                    nguon = con                     # ưu tiên câu chưa chia cho mã nào
                    ung = [c for c in nguon if c["ma"] not in rieng[s_]]
                    if not ung:                     # hết câu riêng → dùng lại câu đã chia (không trùng trong mã)
                        nguon = dong
                        ung = [c for c in nguon if c["ma"] not in rieng[s_]]
                    if not ung:
                        continue
                    thu_tu = {id(c): i for i, c in enumerate(nguon)}
                    c = min(ung, key=lambda c: (dang_de[s_][c["dang_key"]], dem_dang[c["dang_key"]], thu_tu[id(c)]))
                    rieng[s_].add(c["ma"]); dang_de[s_][c["dang_key"]] += 1; dem_dang[c["dang_key"]] += 1
                    bo[s_][loai].append(c)
                    if c in con:
                        con.remove(c)
    return bo, ghi_chu, thieu

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

THAM_CHIEU_Y = re.compile(r"(ý|Ý|câu|Câu|mệnh đề|khẳng định)\s*[abcd]\b|\b[abcd]\)")
def xao_y_dung_sai(k, da):
    """Câu Đúng/Sai: đảo thứ tự ý a, b, c (giữ ý d — ý khó — ở cuối); lời giải \\itemch đảo theo.
    Bỏ qua câu mà lời giải không chia đúng 4 \\itemch hoặc nội dung có nhắc "ý a", "b)"…"""
    m = tim_lenh(k, "choiceTF")
    if not m or THAM_CHIEU_Y.search(k):
        return k, da
    ds, _ = doc_tham_so(k, m.end(), 4)
    ml = tim_lenh(k, "loigiai")
    if not ds or not ml or ml.start() < ds[-1][1]:
        return k, da
    lg, _ = doc_tham_so(k, ml.end(), 1)
    if not lg:
        return k, da
    lg_dau, lg_cuoi, lg_nd = lg[0]
    mi = re.search(r"\\begin\{itemchoice\}(.*)\\end\{itemchoice\}", lg_nd, re.S)
    if not mi:
        return k, da
    phan = re.split(r"\\itemch(?![A-Za-z])", mi.group(1))
    if len(phan) != 5:
        return k, da
    hv = [0, 1, 2]; rng.shuffle(hv); hv.append(3)
    lg_moi = lg_nd[:mi.start(1)] + phan[0] + "".join("\\itemch" + phan[1 + i] for i in hv) + lg_nd[mi.end(1):]
    out = k[:lg_dau] + "{" + lg_moi + "}" + k[lg_cuoi:]
    moi = [ds[i][2] for i in hv]
    for (dau, cuoi, _), nd in sorted(zip(ds, moi), key=lambda x: -x[0][0]):
        out = out[:dau] + "{" + nd + "}" + out[cuoi:]
    da_moi = "".join("Đ" if re.search(r"\\True(?![A-Za-z])", nd) else "S" for nd in moi)
    return out, da_moi

# ---------------------------------------------------------------- soạn thân đề
SO_LA_MA = ["I", "II", "III", "IV"]
PHAN = {
    "TN": ("Câu trắc nghiệm nhiều phương án lựa chọn.", "Thí sinh trả lời từ câu 1 đến câu {n}. Mỗi câu hỏi thí sinh chỉ chọn một phương án.", "ex", "ans", "Ans"),
    "DS": ("Câu trắc nghiệm đúng sai.", "Thí sinh trả lời từ câu 1 đến câu {n}. Trong mỗi ý a), b), c), d) ở mỗi câu, thí sinh chọn đúng hoặc sai.", "ex", "ansbook", "Ansbook"),
    "TLN": ("Câu trắc nghiệm trả lời ngắn.", "Thí sinh trả lời từ câu 1 đến câu {n}.", "bt", "ansbt", "Ansbook"),
    "TL": ("Tự luận.", "Thí sinh trình bày lời giải từ câu 1 đến câu {n}.", "bt", None, None),
}
CHINH_THUC = mt.get("khung", "DeThiChinhThuc") == "DeThiChinhThuc"
TIET_KIEM = bool(mt.get("tiet_kiem")) and CHINH_THUC
HAI_COT = TIET_KIEM and bool(mt.get("hai_cot"))

CAU_THEO_DE = {}          # mã đề → danh sách câu (đã xáo) cho bản Word K12Online

def soan_ma_de(bo, ma_de):
    """Trả (thân đề, phần đáp án cuối, các dòng đáp án)."""
    khoi, dap_an_rows, bang = [], [], []
    stt = 0
    if CHINH_THUC:
        khoi.append(f"\\dauDe{{{ma_de}}}")
        if HAI_COT:
            khoi.append("\\begin{multicols}{2}")
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
            if loai == "DS" and mt.get("xao_y_dung_sai", True):
                k, da = xao_y_dung_sai(k, da)
            khoi.append(k)
            dap_an_rows.append([ma_de, loai, i, da or "", c["ma"], c["id"]])
            CAU_THEO_DE.setdefault(ma_de, []).append({"loai": loai, "noi_dung": k, "dap_an": da or "", "muc": c["muc_chuan"]})
        if sf:
            khoi.append(f"\\Closesolutionfile{{{sf}}}")
            bang.append(f"\\par\\noindent\\textbf{{PHẦN {so_la_ma}.}}\\par\n\\begin{{flushleft}}\n\\input{{{tm}/{tep}}}\n\\end{{flushleft}}")
    if CHINH_THUC:
        if HAI_COT:
            khoi.append("\\end{multicols}")
        khoi.append(f"\\hetDe{{{ma_de}}}")
    cuoi = ""
    if bang:
        tieu_da = (f"\\phanDapAn{{{ma_de}}}\n" if CHINH_THUC else
                   f"\\newpage\n\\begin{{center}}{{\\large\\bfseries ĐÁP ÁN -- MÃ ĐỀ {ma_de}}}\\end{{center}}\n")
        cuoi = tieu_da + "\n".join(bang)
    return "\n\n".join(khoi), cuoi, dap_an_rows

# ---------------------------------------------------------------- chạy
so_ma = int(mt["so_ma_de"]); bat_dau = int(mt["ma_de_bat_dau"])
if not any(p["yeu_cau"] for p in mt.get("phan", [])):
    sys.exit("Ma trận chưa có số câu nào. Mở file ma trận (CSV) bằng Numbers/Excel, điền số câu vào các cột "
             "TN_N, TN_H, DS_H, TLN_V… ở dòng dạng toán cần lấy, lưu lại dạng CSV rồi chạy lại.")
khac_cau = bool(mt.get("moi_ma_de_cau_khac_nhau"))
cac_bo, ghi_chu_bu, thieu = lap_ke_hoach(so_ma, khac_cau)
bo_chung = cac_bo[0]
for x in thieu:
    print("  ⚠ thiếu câu:", x)
for x in ghi_chu_bu:
    print("  ↻", x)
dem = {l: len(v) for l, v in bo_chung.items() if v}
print("Đã chọn: " + ", ".join(f"{LOAI_TEN[k]} {v}" for k, v in dem.items()))
if not dem:
    sys.exit("Không chọn được câu nào (kho không có câu khớp ma trận).")
if CHINH_THUC and (dem.get("TN"), dem.get("DS"), dem.get("TLN")) != (12, 4, 6):
    print("  (lưu ý: cấu trúc đề tốt nghiệp 2025 là 12 TN – 4 Đúng/Sai – 6 Trả lời ngắn)")
if khac_cau and so_ma > 1:
    tap = [set(c["ma"] for v in b.values() for c in v) for b in cac_bo]
    chung = len(set.intersection(*tap))
    tong_rieng = len(set.union(*tap))
    print(f"  Mỗi mã đề một bộ câu: dùng {tong_rieng} câu khác nhau cho {so_ma} mã đề; số câu có mặt ở mọi mã: {chung}")
print(f"  Câu đã dùng ở đề trước: " + {"uu_tien": "ưu tiên câu chưa dùng", "loai_bo": "KHÔNG lấy lại",
      "khong": "không xét"}.get(CHE_DO_DA_DUNG, CHE_DO_DA_DUNG))
if a.thu:
    for loai, ds in bo_chung.items():
        for c in ds:
            dd = f" (đã dùng {so_lan_dung(c)} lần)" if so_lan_dung(c) else ""
            print(f"  {loai:<3} {c['id']:<10} {c['ma']}  {c['muc_chuan'] or '?'}  {c['ten_dang'] or ''}{dd}")
    sys.exit(0)

khung = mt["khung"]
src = os.path.join(GOC, "khung", khung)

def ten_thu_muc(s):
    s = unicodedata.normalize("NFC", s.replace("--", "–"))
    s = re.sub(r'[\\/:*?"<>|\n\r\t]+', " ", s)
    return re.sub(r"\s+", " ", s).strip(" .") or "De thi"
import unicodedata
ngay = time.strftime("%d-%m-%Y")
goc_ten = ten_thu_muc(f"{mt['ten_ky_thi']} - {ngay}")
out_goc, i = os.path.join(GOC, "de-da-ra", goc_ten), 2
while os.path.exists(out_goc):
    out_goc = os.path.join(GOC, "de-da-ra", f"{goc_ten} ({i})"); i += 1
out = os.path.join(out_goc, "tex")                        # mã nguồn LaTeX + khung
os.makedirs(out_goc)
shutil.copytree(src, out, ignore=shutil.ignore_patterns("mau_de.tex", "*.bat"))
mau = doc(os.path.join(src, "mau_de.tex"))
for k, v in {"<<SO_GD>>": mt["so_gd"], "<<TRUONG>>": mt["truong"], "<<TEN_KY_THI>>": mt["ten_ky_thi"],
             "<<NAM_HOC>>": mt["nam_hoc"], "<<MON>>": mt["mon"], "<<THOI_GIAN>>": mt["thoi_gian"],
             "<<CHAN_TRANG>>": mt.get("chan_trang", mt["ten_ky_thi"])}.items():
    mau = mau.replace(k, re.sub(r"(?<!\\)([&%#])", r"\\\1", v))   # tự thoát ký tự & % # cho LaTeX
if TIET_KIEM:
    # ĐỀ TIẾT KIỆM GIẤY: chữ 10/11pt, lề hẹp, giãn dòng sát, (tuỳ chọn) 2 cột
    co = str(int(mt.get("co_chu") or 11))
    if co not in ("10", "11", "12"):
        co = "11"
    mau = re.sub(r"\\documentclass\[\d+pt,", f"\\\\documentclass[{co}pt,", mau, count=1)
    mau = re.sub(r"\\usepackage\[a4paper,[^\]]*\]\{geometry\}",
                 lambda m: "\\usepackage[a4paper,left=1.1cm,right=1.0cm,top=0.9cm,bottom=1.1cm,footskip=0.5cm]{geometry}", mau, count=1)
    mau = mau.replace("\\setstretch{1.1}", "\\setstretch{1.0}").replace("\\setlength{\\parskip}{6pt}", "\\setlength{\\parskip}{1pt}")
    gon = ["%==================== TIẾT KIỆM GIẤY ====================",
           "\\makeatletter\\g@addto@macro\\normalsize{\\setlength{\\abovedisplayskip}{2pt}\\setlength{\\belowdisplayskip}{2pt}"
           "\\setlength{\\abovedisplayshortskip}{1pt}\\setlength{\\belowdisplayshortskip}{1pt}}\\makeatother",
           "\\renewcommand{\\phanDe}[1]{\\par\\smallskip\\noindent #1\\par}"]
    if HAI_COT:
        gon += ["\\usepackage{multicol}\\setlength{\\columnsep}{0.55cm}\\setlength{\\columnseprule}{0.3pt}",
                "\\tikzset{every picture/.append style={scale=0.75,transform shape}}",
                # hình cạnh đề (\\immini) quá hẹp trong 2 cột → đặt hình xuống dưới, căn giữa
                "\\renewcommand{\\immini}[3][]{{\\tieudehinh #2}\\par\\nopagebreak{\\centering #3\\par}}"]
    mau = mau.replace("\\begin{document}", "\n".join(gon) + "\n\\begin{document}", 1)

def tai_lieu(than, loi_giai):
    return mau.replace("<<CHE_DO_LOI_GIAI>>", "\\hienthiloigiai" if loi_giai else "\\anloigiai").replace("<<NOI_DUNG>>", than)

tat_ca_dap_an, ds_cau_dung, gop_de, gop_lg, gop_cuoi, cac_ma = [], {}, [], [], [], []
for s in range(so_ma):
    ma_de = str(bat_dau + s).zfill(3); cac_ma.append(ma_de)
    bo = cac_bo[s]
    for v in bo.values():
        for c in v:
            ds_cau_dung[c["ma"]] = c
    than, cuoi, rows = soan_ma_de(bo, ma_de)
    tat_ca_dap_an += rows
    ghi(os.path.join(out, f"De_{ma_de}.tex"), tai_lieu(than, False))
    ghi(os.path.join(out, f"De_{ma_de}_LoiGiai.tex"), tai_lieu(than + "\n\n" + cuoi, True))
    gop_de.append(than); gop_lg.append(than + "\n\n" + cuoi); gop_cuoi.append(cuoi)
ghi(os.path.join(out, "TatCa_De.tex"), tai_lieu("\n\n\\newpage\n".join(gop_de), False))
ghi(os.path.join(out, "TatCa_LoiGiai.tex"), tai_lieu("\n\n\\newpage\n".join(gop_lg), True))

# ---- QUYỂN ĐỀ CƯƠNG ÔN TẬP: bìa + mục lục + tất cả mã đề + đáp án & lời giải; chân trang có tên giáo viên
def thoat(v):
    return re.sub(r"(?<!\\)([&%#])", r"\\\1", v or "")

def lam_de_cuong():
    gv, ky = thoat(mt.get("giao_vien") or "Vũ Tiến Lực"), thoat(mt["ten_ky_thi"])
    pre, _ = mau.split("\\begin{document}", 1)
    pre = pre.replace("(Đề thi có \\pageref{cuoide#1} trang)", "(Đề số \\thesoDeDC)")
    pre += (
        "%==================== QUYỂN ĐỀ CƯƠNG ====================\n"
        "\\usepackage{fancyhdr}\\newcounter{soDeDC}\n"
        "\\newcommand{\\chanTrangDC}{\\fancyhf{}\\renewcommand{\\headrulewidth}{0pt}\\renewcommand{\\footrulewidth}{0.4pt}%\n"
        f"  \\fancyfoot[L]{{\\small GV: {gv}}}\\fancyfoot[C]{{\\small {ky}}}"
        "\\fancyfoot[R]{\\small Trang \\thepage/\\pageref{trangcuoiDC}}}\n"
        "\\fancypagestyle{plain}{\\chanTrangDC}\n"
        "\\makeatletter\n"
        "\\@ifundefined{dauDe}{}{\\let\\dauDeGoc\\dauDe\n"
        "  \\renewcommand{\\dauDe}[1]{\\stepcounter{soDeDC}\\edef\\trangDC{\\the\\value{page}}\\dauDeGoc{#1}"
        "\\setcounter{page}{\\trangDC}\\chanTrangDC}}\n"
        "\\@ifundefined{phanDapAn}{}{\\let\\phanDapAnGoc\\phanDapAn"
        "\\renewcommand{\\phanDapAn}[1]{\\phanDapAnGoc{#1}\\chanTrangDC}}\n"
        "\\makeatother\n")
    hoa = lambda x: thoat((x or "").upper())
    bia = (
        "\\begin{titlepage}\n"
        "\\begin{tikzpicture}[remember picture,overlay]\n"
        "\\draw[line width=2pt] ([shift={(1.3cm,1.3cm)}]current page.south west) rectangle ([shift={(-1.3cm,-1.3cm)}]current page.north east);\n"
        "\\draw[line width=0.6pt] ([shift={(1.5cm,1.5cm)}]current page.south west) rectangle ([shift={(-1.5cm,-1.5cm)}]current page.north east);\n"
        "\\end{tikzpicture}\n\\centering\n"
        f"{{\\large {thoat(mt['so_gd'])}}}\\\\[4pt]{{\\large\\bfseries {thoat(mt['truong'])}}}\\\\[2pt]\\rule{{5cm}}{{0.6pt}}\n"
        "\\vspace*{5cm}\n\n"
        "{\\fontsize{34}{42}\\selectfont\\bfseries ĐỀ CƯƠNG ÔN TẬP}\\\\[18pt]\n"
        f"{{\\LARGE\\bfseries {hoa(mt['ten_ky_thi'])}}}\\\\[14pt]\n"
        f"{{\\Large Môn: {thoat(mt['mon'])}}}\\\\[8pt]{{\\large {thoat(mt['nam_hoc'])}}}\\\\[24pt]\n"
        f"{{\\large\\itshape Gồm {len(cac_ma)} đề, có đáp án và lời giải chi tiết}}\n"
        "\\vfill\n"
        f"{{\\Large Giáo viên: \\textbf{{{hoa(mt.get('giao_vien') or 'Vũ Tiến Lực')}}}}}\\\\[2cm]\n"
        "\\end{titlepage}\n\\setcounter{page}{2}\\pagestyle{fancy}\\chanTrangDC\n")
    muc = ["\\begin{center}{\\Large\\bfseries MỤC LỤC}\\end{center}\\medskip",
           "\\noindent\\textbf{PHẦN 1. ĐỀ ÔN TẬP}\\par\\smallskip"]
    muc += [f"\\noindent\\hspace*{{1em}}Đề số {i} -- Mã đề {m}\\dotfill\\pageref{{dcde{m}}}\\par" for i, m in enumerate(cac_ma, 1)]
    muc += ["\\medskip\\noindent\\textbf{PHẦN 2. ĐÁP ÁN VÀ LỜI GIẢI CHI TIẾT}\\dotfill\\pageref{dclg}\\par\\smallskip"]
    muc += [f"\\noindent\\hspace*{{1em}}Lời giải đề số {i} -- Mã đề {m}\\dotfill\\pageref{{dclg{m}}}\\par" for i, m in enumerate(cac_ma, 1)]
    phan1 = [f"\\newpage\\phantomsection\\label{{dcde{m}}}\n{t}" for m, t in zip(cac_ma, gop_de)]
    phan2 = ["\\newpage\\phantomsection\\label{dclg}\n\\vspace*{6cm}\\begin{center}{\\fontsize{26}{32}\\selectfont\\bfseries PHẦN 2}\\\\[14pt]"
             "{\\LARGE\\bfseries ĐÁP ÁN VÀ LỜI GIẢI CHI TIẾT}\\end{center}\n\\hienthiloigiai"]
    for i, (m, t, c) in enumerate(zip(cac_ma, gop_de, gop_cuoi), 1):
        t2 = t.replace(f"\\dauDe{{{m}}}", "").replace(f"\\hetDe{{{m}}}", "")
        t2 = re.sub(r"\\section\{[^\n]*\}", "", t2, count=1)
        phan2.append(f"\\newpage\\phantomsection\\label{{dclg{m}}}\n"
                     f"\\begin{{center}}{{\\large\\bfseries LỜI GIẢI ĐỀ SỐ {i} -- MÃ ĐỀ {m}}}\\end{{center}}\n{t2}\n\n{c}")
    than = (bia + "\n".join(muc) + "\n\n" + "\n\n".join(phan1)
            + "\n\n"
            + "\n\n".join(phan2) + "\n\\label{trangcuoiDC}\n")
    ghi(os.path.join(out, "DeCuong.tex"), pre + "\\begin{document}\n\\anloigiai\n" + than + "\\end{document}\n")
    ghi(os.path.join(out, "_ten_de_cuong.txt"), ten_thu_muc(f"Đề cương ôn tập - {mt['ten_ky_thi']}"))

if mt.get("de_cuong", True):
    lam_de_cuong()

# ---- Đáp án Excel theo mẫu Chấm Phiếu AI: sheet "Đáp án", A1 = Câu, dòng 1 = mã đề, các dòng 1…, II.1…, III.1…
def chuan_tln(v):
    v = (v or "").replace("$", "").replace("{,}", ",").replace(" ", "").replace("−", "-").replace(".", ",")
    return v
tra = {(r[0], r[1], r[2]): r[3] for r in tat_ca_dap_an}
so = {l: max([r[2] for r in tat_ca_dap_an if r[1] == l] or [0]) for l in ("TN", "DS", "TLN")}
bang = [["Câu"] + cac_ma]
for i in range(1, so["TN"] + 1):
    bang.append([str(i)] + [tra.get((m, "TN", i), "") for m in cac_ma])
for i in range(1, so["DS"] + 1):
    bang.append([f"II.{i}"] + [tra.get((m, "DS", i), "") for m in cac_ma])
for i in range(1, so["TLN"] + 1):
    bang.append([f"III.{i}"] + [chuan_tln(tra.get((m, "TLN", i), "")) for m in cac_ma])
canh_bao = [f"Mã {m}: {r[0]} còn trống" for r in bang[1:] for m, v in zip(cac_ma, r[1:]) if not v]
canh_bao += [f"Mã {m}: câu {r[0]} đáp số '{v}' dài hơn 4 ô của phiếu" for r in bang[1:] if r[0].startswith("III")
             for m, v in zip(cac_ma, r[1:]) if len(v) > 4]
hd = [[f"{mt['ten_ky_thi']} · {mt['mon'].replace('--', '–')} · {ngay}"],
      [f"Cấu trúc: Phần I {so['TN']} câu · Phần II {so['DS']} câu · Phần III {so['TLN']} câu · {len(cac_ma)} mã đề: {', '.join(cac_ma)}"],
      ["Nạp vào app Chấm Phiếu AI: ô Đáp án → Nhập từ file Excel → chọn file này (app đọc sheet \"Đáp án\")."],
      ["Phần I: A/B/C/D · Phần II: 4 ký tự Đ/S theo ý a, b, c, d · Phần III: đáp số, dấu phẩy thập phân."],
      ["Ô tô vàng ở sheet Đáp án là ô còn trống."]] + [[f"⚠ {w}"] for w in canh_bao]
ghi_xlsx(os.path.join(out_goc, "DapAn.xlsx"), [("Đáp án", bang, {"do_rong": [8] + [10] * len(cac_ma)}),
                                              ("Hướng dẫn", hd, {"kieu": "van_ban", "do_rong": [110]})])

with open(os.path.join(out, "dap_an.csv"), "w", encoding="utf-8-sig", newline="") as fo:
    w = csv.writer(fo); w.writerow(["ma_de", "phan", "cau", "dap_an", "ma_cau", "ma_dang"]); w.writerows(tat_ca_dap_an)
with open(os.path.join(out, "danh_sach_cau.csv"), "w", encoding="utf-8-sig", newline="") as fo:
    w = csv.writer(fo); w.writerow(["ma_cau", "loai", "ma_dang", "muc", "ten_dang", "file"])
    for c in ds_cau_dung.values():
        w.writerow([c["ma"], c["loai"], c["id"], c["muc_chuan"], c["ten_dang"], c["file"]])
json.dump(mt, open(os.path.join(out, "ma_tran_da_dung.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
json.dump(CAU_THEO_DE, open(os.path.join(out, "_k12_cau.json"), "w", encoding="utf-8"), ensure_ascii=False)

for ma in ds_cau_dung:
    lich_su.setdefault(ma, []).append(os.path.basename(out_goc))
json.dump(lich_su, open(p_ls, "w", encoding="utf-8"), ensure_ascii=False)
rel = os.path.relpath(out_goc, GOC)
print(f"Đã tạo {so_ma} mã đề ({', '.join(cac_ma)}) trong {rel}/: DapAn.xlsx + thư mục tex/. Lịch sử dùng câu đã cập nhật.")
for w in canh_bao:
    print("  ⚠", w)
print("THU_MUC:" + rel)

if a.bien_dich:
    bien_dich_thu_muc(out_goc)
if a.word or a.word_svg or mt.get("xuat_word_k12"):
    import k12word
    try:
        k12word.xuat(out_goc, cong_thuc="svg" if a.word_svg or mt.get("word_cong_thuc") == "svg" else "equation")
    except Exception as e:
        print("  ✗ Không xuất được Word:", e)
