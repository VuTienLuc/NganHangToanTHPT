# -*- coding: utf-8 -*-
"""ĐỒNG BỘ đề tuyển sinh 10 từ KHO LỚP 9 sang KHO TUYỂN SINH 10 (cau-hoi-ts10/BaiN.tex).

Bài nào trong cau-hoi/ có dòng  % nguon: … Tuyển sinh 10 …  (đề chính thức, đề tham khảo các quận…)
→ xếp vào Bài 1–7 của đề TS10 THEO NỘI DUNG (đề tham khảo các quận hay đảo thứ tự bài),
→ gán mã dạng TS10 (du-lieu/ts10_dang.json) bằng dấu hiệu trong đề,
→ biên dịch thử bằng phần đầu đề TS10: bài lỗi KHÔNG vào kho (ghi ai-nhap/_loi/),
→ bỏ bài đã có (so nội dung). Chạy lại bao nhiêu lần cũng được.

Dùng:  python3 scripts/ts10_tu_kho9.py [--thu]      (--thu: chỉ báo cáo, chưa ghi)
Tự chạy sau mỗi lần nhap_cau.py nhập bài có nguồn tuyển sinh 10.
"""
import os, re, glob, hashlib, argparse, collections, datetime
from nh_core import GOC, doc, tach_khoi
import ts10

NGUON = re.compile(r"^%\s*ngu[oồ]n\s*:(.*)$", re.M | re.I)
LA_TS10 = re.compile(r"tuy[eể]n\s*sinh\s*(?:lớp\s*)?10|\bTS10\b|vào\s*(?:lớp\s*)?10", re.I)


def khong_chu_thich(t):
    return re.sub(r"(?<!\\)%[^\n]*", "", t)


def tach(khoi):
    """Khối ex/bt của kho lớp 9 → (mã dạng, nguồn, đề, lời giải)."""
    dau, than = khoi.split("\n", 1) if "\n" in khoi else (khoi, "")
    md = re.search(r"%\[([0-9][A-Z][0-9A-Z?]+-\d+)\]", dau)
    env = re.match(r"\\begin\{(ex|bt)\}", dau).group(1)
    than = than[:than.rfind("\\end{" + env + "}")]
    ng = NGUON.search(than)
    lg = ""
    k = re.search(r"\\loigiai\s*\{", than)
    if k:
        a = k.end() - 1; b = ts10.khop_ngoac(than, a)
        if b > 0:
            lg = than[a + 1:b].strip(); than = than[:k.start()] + than[b + 1:]
    de = NGUON.sub("", than).strip()
    return (md.group(1) if md else ""), (ng.group(1).strip() if ng else ""), de, lg


def chu_de(md):
    """Mã dạng lớp 9 → chủ đề (bỏ kí tự mức độ ở vị trí 4)."""
    return (md[:3] + md[4:]).split("-")[0] if len(md) > 4 else md


def xep_bai(md, nguon, de):
    cd = chu_de(md)
    m = re.search(r"(?:Bài|Câu)\s*(\d)", nguon)
    so = int(m.group(1)) if m else 0
    t = de.lower()
    if cd.startswith("9D618") or "parabol" in t:
        return 1
    if cd.startswith("9D620") or re.search(r"x_\{?1\}?.*x_\{?2\}?", t) and "nghiệm" in t:
        return 2
    if cd.startswith("9D8") or "xác suất" in t:
        return 3
    if cd.startswith("9H929") or cd.startswith("9H9") or re.search(r"đường tròn \(o", t) and "chứng minh" in t:
        return 7
    if cd.startswith("9H031") or cd.startswith("9H0") or re.search(r"hình (trụ|nón|cầu)|thể tích", t):
        return 5
    if so in (4, 6):
        return so
    if cd.startswith("9D13") or cd.startswith("9D1"):
        return 6
    return 4


def co(t, *mau):
    return any(re.search(x, t) for x in mau)


def y_cau(de):
    """Tách các ý a), b), c) (enumerate \\item hoặc \\textbf{a)})."""
    if "\\item" in de:
        return [x for x in re.split(r"\\item\b", de)[1:]]
    p = re.split(r"\\textbf\{[a-d]\)\}", de)
    return p[1:] if len(p) > 1 else [de]


def doi_xung(bt):
    """Biểu thức của x1, x2 có đối xứng không (đổi chỗ x1 ↔ x2, so tập các số hạng)."""
    def hang(s):
        s = re.sub(r"\s+", "", s)
        muc, cur, ds = 0, "", []
        for ch in s:
            if ch in "{(":
                muc += 1
            elif ch in "})":
                muc -= 1
            if ch in "+-" and muc == 0 and cur:
                ds.append(cur); cur = ch
            else:
                cur += ch
        ds.append(cur)
        return sorted(x.lstrip("+") for x in ds if x)
    doi = bt.replace("x_1", "X_T").replace("x_{1}", "X_T").replace("x_2", "x_1").replace("x_{2}", "x_1").replace("X_T", "x_2")
    return hang(bt.replace("x_{1}", "x_1").replace("x_{2}", "x_2")) == hang(doi)


def dang(bai, de):
    t = khong_chu_thich(de).lower()
    chac = True
    if bai == 1:
        ma = ["1.0"] if "vẽ" in t else []
        if co(t, r"\(d\)", r"đường thẳng"):
            b = "1.4"
        elif co(t, r"gấp", r"bằng nhau", r"đối nhau", r"cách đều", r"bằng (hai|ba|bốn) lần", r"bằng \$?-?\d+\$? lần"):
            b = "1.2"
        elif co(t, r"(tổng|hiệu|tích).{0,40}(hoành|tung) độ", r"(hoành|tung) độ.{0,30}(lớn|nhỏ) hơn"):
            b = "1.3"
        elif co(t, r"tam giác", r"diện tích", r"\boa\b"):
            b = "1.6"
        elif co(t, r"có thuộc", r"thuộc .{0,10}không", r"hệ số \$?a", r"tìm \$?a\$?", r"cổng", r"cầu", r"quỹ đạo"):
            b = "1.5"
        elif co(t, r"(hoành|tung) độ (bằng|là)", r"có (hoành|tung) độ"):
            b = "1.1"
        else:
            b, chac = "1.1", False
        return ma + [b], chac
    if bai == 2:
        ma = ["2.0"] if co(t, r"chứng (minh|tỏ)", r"hai nghiệm phân biệt", r"có nghiệm") else []
        if re.search(r"(?<![a-z\\])m(?![a-z])", re.sub(r"\\[a-z]+", "", t)) and co(t, r"tham số", r"\bm\b"):
            return ma + ["2.4"], True
        if co(t, r"\^\{?(3|4|5|20\d\d)", r"x_\{?[12]\}?\^\{?[3-9]"):
            return ma + ["2.3"], True
        m = re.search(r"(?:biểu thức|tính)[^$]*\$(.*?)\$", t, re.S)
        bt = (m.group(1).split("=", 1)[-1] if m else "")
        if bt and "x_" in bt:
            return ma + (["2.1"] if doi_xung(bt) else ["2.2"]), True
        return ma + ["2.1"], False
    if bai == 3:
        ds = []
        for mau, ma in ((r"cột (kép|ghép)|hai nhóm|nam.{0,20}nữ", "3.2"), (r"đoạn thẳng", "3.3"),
                        (r"quạt|biểu đồ (hình )?tròn", "3.4"), (r"ghép nhóm|\[\s*\d+\s*;\s*\d+\s*\)", "3.6"),
                        (r"biểu đồ cột|bảng (số liệu|thống kê)|thống kê|số liệu|ghi nhận|như sau", "3.1")):
            if co(t, mau):
                ds.append(ma); break
        for mau, ma in ((r"xúc xắc|đồng xu", "3.8"), (r"vòng quay|ném", "3.10"), (r"thực nghiệm", "3.11"),
                        (r"thẻ|viên bi|quả bóng|\bbi\b|bóng", "3.7"),
                        (r"chọn (ngẫu nhiên )?(cùng lúc |đồng thời )?(hai|2|ba|3|4|bốn) (bạn|học sinh|người|bông)|sơ đồ cây|cách chọn", "3.9"),
                        (r"sinh con|con trai|con gái|thứ tự|chọn món", "3.12"),
                        (r"trung bình", "3.5")):
            if co(t, mau):
                ds.append(ma); break
        return (ds or ["3.12"]), bool(ds)
    if bai == 4:
        for mau, ma in ((r"hình quạt|cung|vành khăn|hình tròn|bán kính", "4.2"), (r"km/h|vận tốc|chuyển động", "4.4"),
                        (r"y\s*=\s*a\s*x|hàm số bậc nhất|cước|taxi", "4.6"), (r"\\tan|\\sin|\\cos|pythagore|pytago|cột cờ|góc nghiêng", "4.7"),
                        (r"phương án|có lợi|tiết kiệm hơn|lớn nhất|nhỏ nhất|ít nhất|tối đa|tối thiểu", "4.5"),
                        (r"\\%|giảm giá|khuyến mãi|lãi|thuế|vat", "4.3"),
                        (r"diện tích|chu vi|mảnh đất|khu vườn|hình chữ nhật|lối đi|hình vuông", "4.1")):
            if co(t, mau):
                return [ma], True
        return ["4.8"], False
    if bai == 5:
        hinh = [ma for mau, ma in ((r"trụ", "5.2"), (r"nón", "5.3"), (r"cầu", "5.4")) if co(t, mau)]
        ds = ["5.1"] if len(hinh) > 1 or co(t, r"nửa (hình )?cầu") else hinh[:1]
        if not ds and co(t, r"hình hộp|lập phương|lăng trụ|hình chóp|kim tự tháp"):
            ds = ["5.8"]
        if co(t, r"sơn|chi phí|vật liệu|m\^2|m\^\{2\}"):
            ds.append("5.5")
        if co(t, r"dâng|thả|nhúng|đổ (đầy|nước)"):
            ds.append("5.6")
        elif co(t, r"lít"):
            ds.append("5.7")
        return (ds or ["5.2"]), bool(ds)
    if bai == 6:
        for mau, ma in ((r"dung dịch|hợp kim|protein|lipit|potassium|nồng độ|hóa|vật lí", "6.7"),
                        (r"làm chung|vòi|năng suất|một mình", "6.4"), (r"km|vận tốc|xuôi|ngược dòng", "6.3"),
                        (r"chữ số|tuổi|điểm trung bình", "6.8"), (r"\\%|vượt mức|tăng|giảm", "6.1"),
                        (r"chiều dài|chiều rộng|diện tích|chu vi", "6.6"), (r"giá|đồng|mua|bán|vé", "6.2"),
                        (r"ghế|xe|học sinh|dãy|tổ|người", "6.5")):
            if co(t, mau):
                return [ma], True
        return ["6.8"], False
    # Bài 7: cấu hình + dạng từng câu
    if co(t, r"hai tiếp tuyến", r"các tiếp tuyến", r"tiếp tuyến .{0,40}\(\s*[a-z]\s*,\s*[a-z]\s*là các tiếp điểm"):
        ch = "7.C1"
    elif co(t, r"đường cao", r"trực tâm"):
        ch = "7.C2"
    elif co(t, r"nửa đường tròn"):
        ch = "7.C4"
    elif co(t, r"đường kính"):
        ch = "7.C3"
    else:
        ch = "7.C5"
    y = [khong_chu_thich(x).lower() for x in y_cau(de)] + ["", "", ""]
    a = "7.a1" if co(y[0], r"nội tiếp", r"cùng (thuộc|nằm trên) một đường tròn") else (
        "7.a2" if co(y[0], r"\\cdot|\.\s*[a-z]{2}\s*=") else ("7.a3" if co(y[0], r"vuông góc|trung trực|song song") else "7.a1"))
    b = "7.b4" if co(y[1], r"nội tiếp") else ("7.b1" if co(y[1], r"\\cdot|đồng dạng") else (
        "7.b2" if co(y[1], r"song song|vuông góc|thẳng hàng|tiếp tuyến") else ("7.b3" if co(y[1], r"bằng|trung điểm|phân giác") else "7.b1")))
    c = "7.c1" if co(y[2], r"tính|theo \$?r|diện tích|độ dài") else (
        "7.c2" if co(y[2], r"vuông góc|song song|thẳng hàng|đồng quy") else "7.c3")
    return [ch, a, b, c], ch != "7.C5"


def chay(thu=False, in_ra=print, bien_dich=True):
    co_san = {ts10.chuan_hoa(khong_chu_thich(x["de"])) for x in ts10.doc_kho()}
    them, khong_chac, gap = [], [], collections.Counter()
    for f in sorted(glob.glob(os.path.join(GOC, "cau-hoi", "**", "*.tex"), recursive=True)):
        for k in tach_khoi(doc(f)):
            md, nguon, de, lg = tach(k)
            if not nguon or not LA_TS10.search(nguon):
                continue
            n = ts10.chuan_hoa(khong_chu_thich(de))
            if n in co_san:
                gap["đã có"] += 1; continue
            co_san.add(n)
            bai = xep_bai(md, nguon, de)
            cac, chac = dang(bai, de)
            ma = hashlib.sha1(n.encode()).hexdigest()[:8]
            khoi = f"\\begin{{bt}}%[TS10 {' '.join(cac)}]%[ma:{ma}]\n% nguon: {nguon}\n{de}\n\\loigiai{{\n{lg}\n}}\n\\end{{bt}}"
            them.append((bai, khoi, nguon, cac))
            if not chac:
                khong_chac.append(f"Bài {bai} [{' '.join(cac)}] ← {nguon}")
    loi = ts10.kiem_bien_dich([x[1] for x in them], in_ra) if them and bien_dich else {}
    tot = [x for i, x in enumerate(them) if i not in loi]
    theo = collections.Counter(x[0] for x in tot)
    in_ra(f"Kho lớp 9 có {len(them) + gap['đã có']} bài nguồn tuyển sinh 10: đã có trong kho TS10 {gap['đã có']}, "
          f"mới {len(them)}, lỗi biên dịch {len(loi)}.")
    in_ra("  " + " · ".join(f"Bài {b}: +{theo[b]}" for b in range(1, 8)))
    for i, ly in sorted(loi.items()):
        in_ra(f"  ✗ LOẠI Bài {them[i][0]} ({them[i][2]}): {'; '.join(ly)}")
    if khong_chac:
        in_ra(f"  ⚠ {len(khong_chac)} bài máy gán mã dạng chưa chắc (vẫn nhập, sửa mã trên dòng đầu nếu cần):")
        for x in khong_chac:
            in_ra("     " + x)
    if not thu and tot:
        for b in range(1, 8):
            ds = [x[1] for x in tot if x[0] == b]
            if not ds:
                continue
            p = os.path.join(ts10.P_KHO, f"Bai{b}.tex")
            co_file = os.path.exists(p) and os.path.getsize(p)
            with open(p, "a", encoding="utf-8") as f:
                f.write(("\n\n" if co_file else f"% NGÂN HÀNG TUYỂN SINH 10 – BÀI {b}\n\n") + "\n\n".join(ds) + "\n")
        if loi:
            p = ts10.ghi_loi([(them[i][1], ly) for i, ly in loi.items()], "ts10_tu_kho9")
            in_ra(f"  Bài lỗi ghi vào {os.path.relpath(p, GOC)}")
        in_ra(f"Đã thêm {len(tot)} bài vào cau-hoi-ts10/.")
    elif thu:
        in_ra("(Chế độ thử: chưa ghi gì.)")
    return {"them": len(tot), "loi": len(loi), "khong_chac": khong_chac, "theo_bai": dict(theo)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--thu", action="store_true")
    ap.add_argument("--khong-bien-dich", action="store_true")
    a = ap.parse_args()
    chay(a.thu, bien_dich=not a.khong_bien_dich)
