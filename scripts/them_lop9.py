# -*- coding: utf-8 -*-
"""Nạp danh mục Toán 9 KNTT (du-lieu/toan9_kntt.json) vào du-lieu/id_map.json (chạy lại được, không trùng)."""
import os, json
GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def nap():
    src = json.load(open(os.path.join(GOC, "du-lieu", "toan9_kntt.json"), encoding="utf-8"))
    p = os.path.join(GOC, "du-lieu", "id_map.json")
    tho = open(p, "rb").read()
    xuong = "\r\n" if b"\r\n" in tho[:2000] else "\n"
    m = json.loads(tho.decode("utf-8"))
    them = 0
    for ch in src["chuong"]:
        for b in ch["bai"]:
            for j, d in enumerate(b["dang"], 1):
                k = f"{ch['ma']}?{b['so']}-{j}"
                v = {"chap_name": ch["ten"], "lesson_name": f"{b['ten']}", "type_name": d}
                if m.get(k) != v:
                    them += 1
                m[k] = v
    with open(p, "w", encoding="utf-8", newline=xuong) as f:
        f.write(json.dumps(m, ensure_ascii=False, indent=4))
    return them

if __name__ == "__main__":
    print(f"Đã nạp/cập nhật {nap()} dạng Toán 9 vào id_map.json")
