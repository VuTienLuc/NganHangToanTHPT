# -*- coding: utf-8 -*-
"""
SẮP XẾP THƯ MỤC ĐỀ CŨ trong de-da-ra/ theo cấu trúc mới:
  de-da-ra/Lớp 10/<Tên chương>/<yyyy-mm-dd> <tên>              (phiếu, đề 1 chương, tạo nhanh theo bài)
  de-da-ra/Lớp 10/Đề kiểm tra – Ôn thi/<Giữa|Cuối học kì I|II>/…  (đề nhiều chương)
  de-da-ra/Tuyển sinh 10/…   ·   de-da-ra/Khác/…  (không xác định được lớp)
Chỉ DI CHUYỂN thư mục (không xoá), ghi nhật ký để hoàn tác; lịch sử dùng câu đổi tên theo.
Dùng: python3 sap_xep_de.py            (xem kế hoạch)
      python3 sap_xep_de.py --lam      (thực hiện)      --hoan-tac  (trả lại lần gần nhất)
"""
import os, re, sys, json, csv, time, datetime, glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nh_core import GOC, RA, nhom_thu_muc, ten_thu_muc_moi  # noqa: E402

GIU = {"TrinhChieu", "Khác", "Tuyển sinh 10"}
NHAT_KY = os.path.join(RA, "_sap_xep")
P_LS = os.path.join(GOC, "du-lieu", "lich_su_dung.json")


def _chi_muc():
    d = {}
    for l in open(os.path.join(GOC, "du-lieu", "chi_muc.jsonl"), encoding="utf-8"):
        c = json.loads(l); d[c["ma"]] = c.get("dang_key") or ""
    return d


def _khoa_dang(thu, CM):
    """Mã dạng của các câu trong thư mục đề cũ."""
    p = os.path.join(thu, "_ma_cau_dung.json")
    if os.path.exists(p):
        try:
            return [CM.get(m, "") for m in json.load(open(p, encoding="utf-8"))]
        except Exception:
            pass
    for p in (os.path.join(thu, "tex", "cau_hinh_phieu.json"), os.path.join(thu, "tex", "phieu_web.json")):
        if os.path.exists(p):
            try:
                c = json.load(open(p, encoding="utf-8"))
                return list(c.get("dang") or []) + list(c.get("pham_vi") or c.get("bai") or [])
            except Exception:
                pass
    p = os.path.join(thu, "tex", "danh_sach_cau.csv")
    if os.path.exists(p):
        try:
            return [CM.get(r["ma_cau"], "") or r.get("ma_dang", "") for r in csv.DictReader(open(p, encoding="utf-8-sig"))]
        except Exception:
            pass
    p = os.path.join(thu, "bo_de.json")
    if os.path.exists(p):
        try:
            c = json.load(open(p, encoding="utf-8"))
            return [k for l in c.get("cac_lan", []) for ph in l.get("ma_tran", {}).get("phan", [])
                    for y in ph.get("yeu_cau", []) for k in re.split(r"[+,;]", str(y.get("dang") or ""))]
        except Exception:
            pass
    return []


def _ngay_va_ten(ten, thu):
    m = re.search(r"\s*-\s*(\d{2})-(\d{2})-(\d{4})(\s*\(\d+\))?\s*$", ten)
    if m:
        ngay = datetime.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        ten = ten[:m.start()] + (m.group(4) or "")
    else:
        ngay = datetime.date.fromtimestamp(os.path.getmtime(thu))
    return ngay, ten.strip()


def ke_hoach():
    CM = _chi_muc()
    ra, da_co = [], set()
    for ten in sorted(os.listdir(RA)):
        thu = os.path.join(RA, ten)
        if not os.path.isdir(thu) or ten.startswith((".", "_")) or ten in GIU or re.match(r"Lớp \d+$", ten):
            continue
        loai = "ts10" if ten.startswith("Tuyển sinh 10") else "phieu" if ten.lower().startswith("phiếu") else "de"
        ngay, goc = _ngay_va_ten(ten, thu)
        if loai == "ts10":
            goc = re.sub(r"^Tuyển sinh 10\s*-\s*", "", goc)
        khoa = _khoa_dang(thu, CM)
        nhom = nhom_thu_muc(khoa, loai, goc)
        moi = os.path.join(nhom, ten_thu_muc_moi(goc, ngay))
        g, i = moi, 2
        while moi in da_co or os.path.exists(os.path.join(RA, moi)):
            moi = f"{g} ({i})"; i += 1
        da_co.add(moi)
        ra.append({"cu": ten, "moi": moi})
    return ra


def _doi_lich_su(doi):
    try:
        ls = json.load(open(P_LS, encoding="utf-8"))
    except Exception:
        return
    ls = {k: [doi.get(x, x) for x in v] for k, v in ls.items()}
    json.dump(ls, open(P_LS, "w", encoding="utf-8"), ensure_ascii=False)


def lam(in_ra=print):
    kh = ke_hoach()
    if not kh:
        in_ra("Không có thư mục cũ nào cần sắp xếp."); return None
    xong = []
    for x in kh:
        a, b = os.path.join(RA, x["cu"]), os.path.join(RA, x["moi"])
        try:
            os.makedirs(os.path.dirname(b), exist_ok=True)
            os.rename(a, b)
            xong.append(x)
        except Exception as e:
            in_ra(f"  ✗ {x['cu']}: {e}")
    os.makedirs(NHAT_KY, exist_ok=True)
    ten = f"{time.strftime('%Y%m%d-%H%M%S')}.json"
    json.dump(xong, open(os.path.join(NHAT_KY, ten), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    _doi_lich_su({x["cu"]: os.path.basename(x["moi"]) for x in xong})
    in_ra(f"Đã sắp xếp {len(xong)}/{len(kh)} thư mục. Nhật ký: de-da-ra/_sap_xep/{ten}")
    return ten


def hoan_tac(in_ra=print):
    ds = sorted(glob.glob(os.path.join(NHAT_KY, "*.json")))
    if not ds:
        in_ra("Chưa có lần sắp xếp nào để hoàn tác."); return 0
    p = ds[-1]; xong = json.load(open(p, encoding="utf-8")); n = 0
    for x in reversed(xong):
        a, b = os.path.join(RA, x["cu"]), os.path.join(RA, x["moi"])
        if os.path.isdir(b) and not os.path.exists(a):
            os.rename(b, a); n += 1
            d = os.path.dirname(b)
            while d != RA and os.path.isdir(d) and not os.listdir(d):
                os.rmdir(d); d = os.path.dirname(d)
    _doi_lich_su({os.path.basename(x["moi"]): x["cu"] for x in xong})
    os.rename(p, p + ".da_hoan_tac")
    in_ra(f"Đã trả {n} thư mục về chỗ cũ.")
    return n


def cay(sau=3):
    """Tóm tắt cây thư mục de-da-ra: [(đường dẫn, số đề)]."""
    ra = []
    for r, ds, fs in os.walk(RA):
        rel = os.path.relpath(r, RA)
        ds[:] = [d for d in ds if not d.startswith(("_", ".")) and d != "tex" and d != "TrinhChieu"]
        if rel == "." or rel.count(os.sep) >= sau:
            ds[:] = [] if rel != "." and rel.count(os.sep) >= sau else ds
            continue
        con = [d for d in ds if re.match(r"\d{4}-\d{2}-\d{2} ", d)]
        if con:
            ra.append((rel, len(con)))
    return sorted(ra)


if __name__ == "__main__":
    if "--lam" in sys.argv:
        lam()
    elif "--hoan-tac" in sys.argv:
        hoan_tac()
    else:
        for x in ke_hoach():
            print(f"{x['cu']}\n   → {x['moi']}")
