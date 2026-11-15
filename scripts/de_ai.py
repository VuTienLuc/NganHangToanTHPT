# -*- coding: utf-8 -*-
"""Đọc & kiểm tra ĐỀ AI (JSON trac_nghiem / dung_sai / tra_loi_ngan) dán vào hoặc tải về từ ChatGPT/Gemini/Claude.

- Bỏ rào ```json, chữ thừa trước/sau, sửa dấu \\ LaTeX viết một gạch (doc_nhap.sua_gach).
- Tách nhiều mã đề AI ({"ma_de_1": {...}, "ma_de_2": {...}} hoặc [ {...}, {...} ]).
- Đếm câu từng phần so với ma trận (mặc định 12–4–6), soát lỗi từng câu (thiếu phương án, đáp án sai kiểu…).
- Trả mỗi mã đề thành một chuỗi JSON chuẩn để Trộn đề / Nhập ngân hàng dùng tiếp.
"""
import re, json
from doc_nhap import sua_gach, doc_tep, KHOI

NHOM = {"trac_nghiem": "TN", "dung_sai": "DS", "tra_loi_ngan": "TLN"}


def boc_json(t):
    """Lấy phần JSON từ văn bản AI trả về (có thể kèm lời dẫn, khối ```json, nhiều khối)."""
    t = (t or "").strip().lstrip("﻿")
    khoi = re.findall(r"```(?:json|JSON)?\s*\n?([\s\S]*?)```", t)
    if khoi:
        t = max(khoi, key=len).strip()
    i = min([x for x in (t.find("{"), t.find("[")) if x >= 0] or [0])
    j = max(t.rfind("}"), t.rfind("]"))
    return t[i:j + 1] if j > i else t


def doc(t):
    tho = boc_json(t)
    try:
        return json.loads(sua_gach(tho)), None
    except json.JSONDecodeError as e:
        dong = tho.splitlines()
        ngu = dong[e.lineno - 1][max(0, e.colno - 40):e.colno + 40] if 0 < e.lineno <= len(dong) else ""
        cut = "" if tho.rstrip().endswith(("}", "]")) else " — JSON bị CẮT giữa chừng (AI chưa viết hết): bảo AI \"viết tiếp\" rồi dán nối, hoặc yêu cầu từng mã đề một."
        return None, f"JSON không hợp lệ ở dòng {e.lineno}, cột {e.colno}: {e.msg}{cut}\n   …{ngu}…"


def la_de(o):
    return isinstance(o, dict) and any(isinstance(o.get(k), list) for k in NHOM)


def tach_ma(obj):
    """→ [(tên, đề)]"""
    if la_de(obj):
        return [("Mã AI 1", obj)]
    ds = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if la_de(v):
                so = re.findall(r"\d+", k)
                ds.append((f"Mã AI {so[0]}" if so else k, v))
            elif isinstance(v, (dict, list)):
                ds += [(f"{k} · {t}", d) for t, d in tach_ma(v)]
    elif isinstance(obj, list):
        de = [x for x in obj if la_de(x)]
        if de:
            ds = [(f"Mã AI {i + 1}", x) for i, x in enumerate(de)]
        elif obj and all(isinstance(x, dict) for x in obj):
            ds = [("Danh sách câu", {"trac_nghiem": obj})]
    return ds


def soat_cau(l, c, i):
    loi, ten = [], f"{l} câu {i}"
    if not isinstance(c, dict):
        return [f"{ten}: không phải đối tượng JSON"]
    if not str(c.get("cau") or "").strip():
        loi.append(f"{ten}: thiếu nội dung \"cau\"")
    if l == "TN":
        pa = c.get("phuong_an")
        if not (isinstance(pa, list) and len(pa) == 4):
            loi.append(f"{ten}: phuong_an phải có đúng 4 chuỗi")
        if str(c.get("dap_an") or "").strip().upper() not in ("A", "B", "C", "D"):
            loi.append(f"{ten}: dap_an phải là A/B/C/D (đang là {c.get('dap_an')!r})")
    elif l == "DS":
        y = c.get("y")
        if not (isinstance(y, list) and len(y) == 4):
            loi.append(f"{ten}: \"y\" phải có đúng 4 ý")
        elif not all(isinstance(x, dict) and isinstance(x.get("dung"), bool) for x in y):
            loi.append(f"{ten}: mỗi ý cần \"dung\": true/false")
    elif l == "TLN":
        da = str(c.get("dap_an") if c.get("dap_an") is not None else "").strip().replace(".", ",")
        if not re.fullmatch(r"-?\d+(,\d+)?", da):
            loi.append(f"{ten}: dap_an phải là số (đang là {c.get('dap_an')!r})")
        elif len(da) > 4:
            loi.append(f"{ten}: đáp số \"{da}\" dài hơn 4 ô phiếu")
    if not str(c.get("giai_thich") or "").strip():
        loi.append(f"{ten}: thiếu lời giải (giai_thich)")
    return loi


def kiem(van_ban, can=None):
    """can: {"TN":12,"DS":4,"TLN":6} — số câu ma trận cần. → {"ok", "loi", "ma": [{ten, so, can_ok, loi, json, so_khoi}]}"""
    can = can or {"TN": 12, "DS": 4, "TLN": 6}
    khoi = [k for k in re.findall(r"```(?:json|JSON)?\s*\n?([\s\S]*?)```", van_ban or "") if k.strip()[:1] in "{["]
    if len(khoi) > 1:            # mỗi lượt AI trả một mã đề → dán nối nhiều khối ```json
        cac = []
        for i, k in enumerate(khoi, 1):
            obj, loi = doc(k)
            if loi:
                return {"ok": False, "loi": f"Khối JSON thứ {i}: {loi}", "ma": []}
            cac += tach_ma(obj)
        cac = [(f"Mã AI {i}", d) for i, (_, d) in enumerate(cac, 1)]
    else:
        obj, loi = doc(van_ban)
        if loi:
            return {"ok": False, "loi": loi, "ma": []}
        cac = tach_ma(obj)
    if not cac:
        return {"ok": False, "loi": "Không thấy đề: JSON cần các mục trac_nghiem / dung_sai / tra_loi_ngan.", "ma": []}
    ra = []
    for ten, de in cac:
        so = {l: len(de.get(k) or []) for k, l in NHOM.items()}
        loi = []
        for k, l in NHOM.items():
            for i, c in enumerate(de.get(k) or [], 1):
                loi += soat_cau(l, c, i)
        lech = [f"{l}: có {so[l]}, ma trận cần {can[l]}" for l in can if can[l] and so.get(l, 0) != can[l]]
        js = json.dumps(de, ensure_ascii=False, indent=1)
        try:
            so_khoi = len(KHOI.findall(doc_tep("de_ai.json", noi_dung=js)))
        except Exception as e:
            so_khoi, loi = 0, loi + [f"Không đổi được sang LaTeX: {e}"]
        ra.append({"ten": ten, "so": so, "lech": lech, "loi": loi, "json": js, "so_khoi": so_khoi})
    return {"ok": True, "loi": "", "ma": ra}


if __name__ == "__main__":
    import sys
    print(json.dumps(kiem(open(sys.argv[1], encoding="utf-8").read()), ensure_ascii=False, indent=1)[:3000])
