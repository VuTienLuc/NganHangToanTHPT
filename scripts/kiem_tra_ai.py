# -*- coding: utf-8 -*-
"""
KIỂM TRA CHẶT file câu hỏi do AI soạn (NotebookLM / Antigravity / ChatGPT…) TRƯỚC KHI NHẬP KHO.
Khác `nhap_cau.py --thu` (chỉ cảnh báo): ở đây lỗi định dạng là LỖI, trả mã thoát 1 để agent tự sửa rồi chạy lại.

  python3 scripts/kiem_tra_ai.py ai-nhap/file.tex              # báo cáo dễ đọc
  python3 scripts/kiem_tra_ai.py ai-nhap/file.json --json      # báo cáo máy đọc (cho Antigravity)
  python3 scripts/kiem_tra_ai.py ai-nhap/*.tex --cho-phep-chua-ma   # câu chưa có mã dạng chỉ là cảnh báo

Nhận .tex/.txt/.md (khối \\begin{ex}…\\end{ex}) và .json (mẫu 13 trường, hoặc mảng chuỗi khối tex) — đọc giống hệt nhap_cau.py.
"""
import os, sys, re, csv, json, glob, argparse, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nh_core import *          # GOC, doc, tach_khoi, phan_tich_cau, tim_lenh, doc_tham_so, ma_bam
import doc_nhap

MUC_TEN = {"N": "Nhận biết", "H": "Thông hiểu", "V": "Vận dụng", "C": "Vận dụng cao"}

def tai_danh_muc():
    p = os.path.join(GOC, "du-lieu", "danh_muc_ma_dang.csv")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8-sig") as f:
        return {r["ma_dang"].strip(): r for r in csv.DictReader(f)}

def can_ngoac(s):
    """Đếm { } không thoát; trả độ lệch (0 = cân)."""
    s = re.sub(r"\\\\", "", s)
    s = re.sub(r"\\[{}]", "", s)
    s = re.sub(r"(?<!\\)%[^\n]*", "", s)
    return s.count("{") - s.count("}")

def so_dau_dola(s):
    s = re.sub(r"(?<!\\)%[^\n]*", "", s)
    s = s.replace("\\$", "")
    return s.count("$")

def kiem_tra_khoi(k, danh_muc, cho_phep_chua_ma):
    loi, cb = [], []
    info = phan_tich_cau(k)
    dong_dau = k.split("\n", 1)[0]
    # --- mã dạng
    if not info["id"]:
        (cb if cho_phep_chua_ma else loi).append("chưa có mã dạng %[..] ngay sau \\begin{..}" +
                                                 (" (ghi %[?])" if "%[?]" in dong_dau else ""))
    else:
        if info["muc"] not in MUC_TEN:
            loi.append(f"mức '{info['muc']}' không hợp lệ (chỉ N/H/V/C)")
        if danh_muc is not None and info["dang_key"] not in danh_muc:
            loi.append(f"mã dạng {info['dang_key']} không có trong du-lieu/danh_muc_ma_dang.csv (tra: python3 scripts/tra_dang.py)")
    # --- môi trường đúng loại
    if info["loai"] in ("TN", "DS") and info["moi_truong"] != "ex":
        loi.append("Trắc nghiệm/Đúng-Sai phải dùng \\begin{ex}")
    if info["loai"] in ("TLN", "TL") and info["moi_truong"] != "bt":
        loi.append("Trả lời ngắn/Tự luận phải dùng \\begin{bt}")
    # --- phương án
    if info["loai"] in ("TN", "DS"):
        ten = "choiceTF" if info["loai"] == "DS" else "choice"
        mm = tim_lenh(k, ten)
        ds, _ = doc_tham_so(k, mm.end(), 4)
        if not ds or len(ds) < 4:
            loi.append(f"\\{ten} phải có đủ 4 nhóm {{…}}")
        else:
            so_true = sum(1 for x in ds if re.search(r"\\True(?![A-Za-z])", x[2]))
            if info["loai"] == "TN" and so_true != 1:
                loi.append(f"trắc nghiệm có {so_true} \\True (cần đúng 1)")
            if any(re.match(r"\s*(\\True\s*)?[A-D][.)]\s", x[2]) for x in ds):
                loi.append("phương án không được ghi chữ 'A.' 'B.' ở đầu")
    if info["loai"] == "DS":
        mi = re.search(r"\\begin\{itemchoice\}(.*?)\\end\{itemchoice\}", k, re.S)
        if not mi:
            loi.append("lời giải Đúng/Sai phải có \\begin{itemchoice} với 4 \\itemch")
        else:
            ys = re.split(r"\\itemch(?![A-Za-z])", mi.group(1))[1:]
            if len(ys) != 4:
                loi.append(f"itemchoice có {len(ys)} \\itemch (cần 4)")
            elif info.get("dap_an"):
                for j, y in enumerate(ys):
                    m = re.match(r"\s*(?:\\textbf\{)?\s*(Đúng|Sai)", y)
                    if not m:
                        cb.append(f"ý {'abcd'[j]}: lời giải nên mở đầu 'Đúng.' / 'Sai.'")
                    elif (m.group(1) == "Đúng") != (info["dap_an"][j] == "Đ"):
                        loi.append(f"ý {'abcd'[j]}: lời giải ghi '{m.group(1)}' nhưng \\True không khớp")
        if re.search(r"(ý|câu)\s*[abcd]\)?(?![A-Za-zÀ-ỹ])|\b[abcd]\)", re.sub(r"\\begin\{itemchoice\}.*?\\end\{itemchoice\}", "", k, flags=re.S)):
            cb.append("có nhắc 'ý a'/'b)' — câu này sẽ không được đảo ý khi trộn")
    if info["loai"] == "TLN":
        da = info.get("dap_an") or ""
        if not da:
            loi.append("\\shortans{} rỗng")
        else:
            if re.search(r"\d\.\d", da):
                loi.append(f"đáp số '{da}' dùng dấu chấm — phải dùng dấu phẩy thập phân")
            if len(da.replace("{,}", ",").replace("$", "").strip()) > 4:
                loi.append(f"đáp số '{da}' dài hơn 4 ô phiếu (làm tròn hoặc đổi câu hỏi)")
    # --- lời giải
    if not info["co_loi_giai"]:
        loi.append("thiếu \\loigiai{…} hoặc lời giải rỗng")
    if info["loai"] == "TN" and re.search(r"Chọn\s+[ABCD]\b|[Đđ]áp án\s+(?:là\s+)?[ABCD]\b|phương án\s+[ABCD]\b", k):
        loi.append("lời giải nhắc 'Chọn/Đáp án A..D' (sai khi đảo phương án)")
    # --- cú pháp
    lech = can_ngoac(k)
    if lech:
        loi.append(f"ngoặc {{ }} lệch {lech:+d}")
    if so_dau_dola(k) % 2:
        loi.append("số dấu $ lẻ (công thức chưa đóng)")
    if re.search(r"\\\(|\\\)|\\\[|\\\]", k):
        cb.append("dùng \\( \\) hoặc \\[ \\] — nên đổi sang $…$")
    toan = " ".join(re.findall(r"(?<!\\)\$(.+?)(?<!\\)\$", k, re.S))
    if re.search(r"(?<![\d{])\d+,\d", toan):
        cb.append("số thập phân trong $…$ nên viết {,} (nhập kho sẽ tự sửa)")
    if re.search(r"\*\*|^#+ ", k, re.M):
        loi.append("còn ký hiệu Markdown (** hoặc #)")
    for dau in ("KIEM_TRA", "CAN_VE_HINH"):
        if dau in k:
            cb.append(f"có đánh dấu % {dau}")
    return info, loi, cb

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--json", action="store_true", help="in báo cáo JSON")
    ap.add_argument("--cho-phep-chua-ma", action="store_true")
    a = ap.parse_args()
    danh_muc = tai_danh_muc()
    da_co = {}
    for f in glob.glob(os.path.join(GOC, "cau-hoi", "**", "*.tex"), recursive=True):
        for k in tach_khoi(doc(f)):
            da_co[ma_bam(k)] = os.path.relpath(f, GOC)
    bao_cao = {"tong": 0, "loi": 0, "canh_bao": 0, "trung_kho": 0, "theo_loai_muc": {}, "theo_dang": {}, "cau": []}
    dem_lm = collections.Counter(); dem_dang = collections.Counter(); trong_file = {}
    for f in a.files:
        if not os.path.isfile(f):
            print(f"Không thấy file: {f}", file=sys.stderr); continue
        try:
            t = doc_nhap.doc_tep(f)
        except Exception as e:
            bao_cao["cau"].append({"file": f, "stt": 0, "loi": [f"không đọc được file: {e}"], "canh_bao": []})
            bao_cao["loi"] += 1; continue
        khoi = tach_khoi(t)
        if not khoi:
            bao_cao["cau"].append({"file": f, "stt": 0, "loi": ["không tìm thấy khối \\begin{ex}/\\begin{bt} nào"], "canh_bao": []})
            bao_cao["loi"] += 1; continue
        for i, k in enumerate(khoi, 1):
            info, loi, cb = kiem_tra_khoi(k, danh_muc, a.cho_phep_chua_ma)
            mb = ma_bam(k)
            if mb in da_co:
                cb.append(f"TRÙNG câu đã có trong kho ({da_co[mb]}) — sẽ bị bỏ qua khi nhập")
                bao_cao["trung_kho"] += 1
            if mb in trong_file:
                loi.append(f"trùng với câu {trong_file[mb]} trong cùng lô")
            trong_file.setdefault(mb, f"{os.path.basename(f)}#{i}")
            bao_cao["tong"] += 1
            bao_cao["loi"] += bool(loi); bao_cao["canh_bao"] += bool(cb)
            dem_lm[f"{info['loai']}_{info['muc'] or '?'}"] += 1
            dem_dang[info["dang_key"] or "(chưa mã)"] += 1
            dau = re.sub(r"\s+", " ", re.sub(r"\\begin\{(ex|bt)\}\S*", "", k))[:80]
            bao_cao["cau"].append({"file": os.path.basename(f), "stt": i, "ma_dang": info["id"], "loai": info["loai"],
                                   "dap_an": info.get("dap_an"), "dau_cau": dau, "loi": loi, "canh_bao": cb})
    bao_cao["theo_loai_muc"] = dict(sorted(dem_lm.items()))
    bao_cao["theo_dang"] = dict(sorted(dem_dang.items()))
    if danh_muc is None:
        bao_cao["ghi_chu"] = "chưa có du-lieu/danh_muc_ma_dang.csv — chạy python3 scripts/lap_chi_muc.py để kiểm mã dạng"
    if a.json:
        print(json.dumps(bao_cao, ensure_ascii=False, indent=1))
    else:
        for c in bao_cao["cau"]:
            if c["loi"] or c["canh_bao"]:
                print(f"• {c['file']} câu {c['stt']} [{c.get('loai','?')}] {c.get('ma_dang') or ''}  {c.get('dau_cau','')}")
                for x in c["loi"]:
                    print(f"    ✗ LỖI: {x}")
                for x in c["canh_bao"]:
                    print(f"    ⚠ {x}")
        print("\nTheo loại_mức:", ", ".join(f"{k}={v}" for k, v in bao_cao["theo_loai_muc"].items()))
        print("Theo dạng:", ", ".join(f"{k}={v}" for k, v in bao_cao["theo_dang"].items()))
        if "ghi_chu" in bao_cao:
            print("Ghi chú:", bao_cao["ghi_chu"])
        print(f"\nTỔNG {bao_cao['tong']} câu · {bao_cao['loi']} câu LỖI · {bao_cao['canh_bao']} câu cảnh báo · {bao_cao['trung_kho']} trùng kho")
        print("→ ĐẠT, nhập được." if bao_cao["loi"] == 0 else "→ CHƯA ĐẠT: sửa các câu LỖI rồi chạy lại.")
    sys.exit(1 if bao_cao["loi"] else 0)

if __name__ == "__main__":
    main()
