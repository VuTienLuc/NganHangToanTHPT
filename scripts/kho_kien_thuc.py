# -*- coding: utf-8 -*-
"""
KHO KIẾN THỨC TRỌNG TÂM — mỗi bài một file du-lieu/kien_thuc/<mã bài>.tex (vd 0H5_4.tex cho bài 0H5?4).
  • Phần chung (định nghĩa, công thức) + phương pháp từng dạng, mỗi dạng mở bằng dòng  %% DANG <mã dạng>.
  • Khi lưu, phương pháp từng dạng được tách sang du-lieu/phuong_phap/<mã dạng>.tex (Beamer chiếu từng dạng).
  • Nhập nhiều bài một lần: dán kết quả AI có các dòng  %%% BAI <mã bài>  ngăn từng bài.
Phiếu bài học tự lấy kiến thức: đúng tổ hợp đã lưu → nếu không có thì ghép các bài trong phạm vi.
"""
import os, re, collections
from nh_core import GOC, tai_id_map, lop_tu_so

THU_MUC = os.path.join(GOC, "du-lieu", "kien_thuc")


def tep(khoa):
    return os.path.join(THU_MUC, re.sub(r"[^0-9A-Za-z]+", "_", khoa) + ".tex")


def doc(khoa):
    p = tep(khoa)
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""


def cac_bai(id_map=None):
    """{mã bài: {ten_bai, ten_chuong, lop, dang: [mã dạng…]}} theo id_map."""
    id_map = id_map or tai_id_map()
    ra = collections.OrderedDict()
    for k, v in id_map.items():
        m = re.match(r"(\d)([A-Z])(\d+)\?(\d+)-(\d+)$", k)
        if not m:
            continue
        b = k.split("-")[0]
        x = ra.setdefault(b, {"ten_bai": (v.get("lesson_name") or "").strip(), "ten_chuong": (v.get("chap_name") or "").strip(),
                              "lop": lop_tu_so(m.group(1)), "chuong": b[:-len(b.split("?")[1]) - 1], "so_bai": int(m.group(4)), "dang": []})
        x["dang"].append(k)
    return ra


def danh_sach(lop):
    """Danh sách bài của một lớp + đã có kiến thức chưa, bao nhiêu dạng đã có phương pháp."""
    import beamer_phieu
    ra = []
    for b, x in cac_bai().items():
        if x["lop"] != int(lop):
            continue
        so_pp = sum(1 for d in x["dang"] if os.path.exists(beamer_phieu.tep_pp(d)))
        ra.append({"bai": b, "ten_bai": x["ten_bai"], "ten_chuong": x["ten_chuong"], "chuong": x["chuong"], "so_bai": x["so_bai"],
                   "so_dang": len(x["dang"]), "co_kt": bool(doc(b).strip()), "so_pp": so_pp})
    ra.sort(key=lambda r: (r["so_bai"], r["bai"]) if int(lop) <= 9 else
            ("DHC".find(r["chuong"][1]), int(r["chuong"][2:] or 0), r["so_bai"]))
    return ra


def luu(bai, noi_dung):
    """Lưu kiến thức 1 bài; tách phương pháp từng dạng sang kho phương pháp. → số dạng có phương pháp."""
    import beamer_phieu
    nd = (noi_dung or "").strip()
    os.makedirs(THU_MUC, exist_ok=True)
    if not nd:
        if os.path.exists(tep(bai)):
            os.remove(tep(bai))
        return 0
    open(tep(bai), "w", encoding="utf-8").write(nd + "\n")
    x = cac_bai().get(bai, {"dang": []})
    _, pp = beamer_phieu.tach_phuong_phap(nd, x["dang"])
    pp = {k: v for k, v in pp.items() if k in x["dang"] or not x["dang"]}
    beamer_phieu.luu_pp(pp)
    return len(pp)


def bo_khoi_ma(t):
    """Bỏ ```latex … ``` nếu AI bọc kết quả trong khối mã."""
    t = (t or "").strip()
    m = re.search(r"```(?:latex|tex)?\s*\n(.*?)```", t, re.S)
    return m.group(1).strip() if m else t


def nhap(van_ban, bai_mac_dinh=None):
    """Dán kết quả AI: nhiều bài ngăn bằng '%%% BAI <mã bài>' (hoặc 1 bài → bai_mac_dinh). → [(bài, số dạng có PP)]."""
    t = bo_khoi_ma(van_ban)
    phan = re.split(r"^[ \t]*%%%[ \t]*BAI[ \t]+(\S+)[ \t]*$", t, flags=re.M)
    ds = cac_bai()
    ra = []
    if len(phan) > 1:
        for i in range(1, len(phan) - 1, 2):
            b = phan[i].strip()
            if b in ds:
                ra.append((b, luu(b, phan[i + 1])))
            else:
                ra.append((b, -1))
    elif bai_mac_dinh:
        ra.append((bai_mac_dinh, luu(bai_mac_dinh, t)))
    return ra


def doc_pham_vi(pham_vi):
    """Kiến thức cho phiếu: đúng tổ hợp đã lưu; nếu không, ghép các bài (phạm vi chương → mọi bài của chương)."""
    khoa = "+".join(sorted(pham_vi))
    nd = doc(khoa)
    if nd.strip():
        return nd
    ds = cac_bai()
    bai = []
    for p in pham_vi:
        bai += [b for b in ds if b == p or (("?" not in p) and b.startswith(p + "?"))]
    phan = []
    for b in bai:
        t = doc(b).strip()
        if t:
            phan.append((r"\textbf{\color{mauPhieu}" + ds[b]["ten_bai"] + "}\n" if len(bai) > 1 else "") + t)
    return "\n\n".join(phan)


def prompt(cac_bai_chon):
    """Prompt AI soạn kiến thức trọng tâm cho 1 hay nhiều bài (đúng định dạng để dán lại vào kho)."""
    ds = cac_bai()
    bai = [b for b in cac_bai_chon if b in ds]
    if not bai:
        raise ValueError("Chưa chọn bài.")
    id_map = tai_id_map()
    lop = ds[bai[0]]["lop"]
    cap = (f"THCS – Toán {lop}, sách Kết nối tri thức với cuộc sống" if lop <= 9 else "THPT, sách Kết nối tri thức với cuộc sống")
    nhieu = len(bai) > 1
    dong = []
    for b in bai:
        x = ds[b]
        dong.append(f"\n### {('%%% BAI ' + b) if nhieu else 'Bài'}: {x['ten_bai']} ({x['ten_chuong']})")
        for j, d in enumerate(x["dang"], 1):
            dong.append(f"  - Dạng {j}. {(id_map.get(d, {}).get('type_name') or '').strip()}  (mã {d})")
    vi_du = bai[0]; d0 = ds[vi_du]["dang"][0]
    return f"""# NHIỆM VỤ
Bạn là giáo viên Toán {cap} (chương trình GDPT 2018), giỏi tóm tắt kiến thức cho học sinh.
Hãy soạn phần **KIẾN THỨC TRỌNG TÂM** cho {'TỪNG bài' if nhieu else 'bài'} dưới đây (đính kèm SGK nếu có thì bám sát SGK):
{chr(10).join(dong)}

# YÊU CẦU NỘI DUNG
- Ngắn gọn, đủ ý để học sinh làm bài: định nghĩa, định lí, tính chất, công thức cần nhớ (đúng phạm vi bài, không dùng kiến thức bài sau).
- Sau đó PHƯƠNG PHÁP GIẢI từng dạng (2–4 bước ngắn, mỗi bước 1–2 dòng) + "Lưu ý:" sai lầm hay gặp (nếu có).
- Mỗi bài khoảng nửa trang A4 (chữ 11). Không viết lời dẫn, không chào hỏi.

# ĐỊNH DẠNG BẮT BUỘC (LaTeX, để dán thẳng vào phần mềm)
- Trả về DUY NHẤT một khối ```latex … ```; không \\documentclass, không \\begin{{document}}.
{"- Mỗi bài mở đầu bằng MỘT dòng riêng: %%% BAI <mã bài> (đúng mã ghi ở tiêu đề ### mỗi bài)." if nhieu else ""}
- Cấu trúc mỗi bài:
{"  %%% BAI " + vi_du if nhieu else ""}
  \\textbf{{1. Kiến thức cần nhớ}}
  \\begin{{itemize}}
  \\item …
  \\end{{itemize}}
  \\textbf{{2. Phương pháp giải các dạng}}
  %% DANG {d0}
  \\textbf{{Dạng 1. <tên dạng>}}
  \\begin{{enumerate}}
  \\item <bước 1>
  \\item <bước 2>
  \\end{{enumerate}}
  Lưu ý: …
  (lặp lại cho từng dạng: dòng %% DANG <mã dạng> đứng riêng một dòng ngay trước mỗi dạng, đúng mã đã cho)
- Công thức trong $…$; số thập phân viết $0{{,}}5$; công thức quan trọng có thể \\boxed{{…}}. Không dùng gói lạ, không dùng \\section.
"""
