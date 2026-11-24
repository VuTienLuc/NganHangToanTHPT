# -*- coding: utf-8 -*-
"""🔬 PHIẾU NGHIÊN CỨU BÀI HỌC — một bài học SGK → phiếu nhiều mã đề.

  I.  KIẾN THỨC TRỌNG TÂM của bài (lấy từ kho kiến thức).
  II. THỰC HÀNH THEO MẪU — 3 loại câu như đề thi 2025:
        Phần 1 Trắc nghiệm · Phần 2 Đúng/Sai · Phần 3 Trả lời ngắn.
      Mỗi phần: 🔎 VÍ DỤ MINH HOẠ (có lời giải đầy đủ, đáp án) → ✍ ÁP DỤNG TƯƠNG TỰ (các câu chọn theo mẫu:
      câu con '% mau: <mã ví dụ>' trước, rồi cùng dạng – cùng loại – mức gần nhất). Thầy chọn số câu thực hành mỗi loại,
      số ví dụ mẫu mỗi loại.
  Nhiều mã đề (001, 002…): ví dụ giữ nguyên; câu thực hành đảo thứ tự trong nhóm, đảo phương án TN, đảo ý a–c Đúng/Sai.
  Ra: De_<mã>.pdf (phiếu học sinh) · LoiGiai_<mã>.pdf (đáp án + lời giải) · DapAn_UNT.xlsx (phần mềm chấm UNT).
  Cỡ chữ 14 (đọc rõ trên điện thoại), khổ A4 hoặc A5 (điện thoại); phiếu nhiều màu: mỗi loại câu một màu.
"""
import os, re, json, time, random, shutil, subprocess
from nh_core import (GOC, tai_id_map, doc as doc_tep, ghi, cau_hinh, thu_muc_xuat, chuan_vecto, lop_tu_so,
                     tim_lenh, doc_tham_so, ghi_dap_an_unt, MA_DANG)

LOAI = [("TN", "TRẮC NGHIỆM NHIỀU PHƯƠNG ÁN", "mauTN", r"\faListUl",
         "Mỗi câu chỉ chọn một phương án A, B, C hoặc D."),
        ("DS", "TRẮC NGHIỆM ĐÚNG – SAI", "mauDS", r"\faCheckSquareO",
         "Mỗi ý a), b), c), d) em ghi Đúng (Đ) hoặc Sai (S)."),
        ("TLN", "TRẢ LỜI NGẮN", "mauTLN", r"\faPencil",
         "Ghi đáp số vào ô (tối đa 4 kí tự, kể cả dấu - và dấu phẩy).")]
MAU = re.compile(r"%\s*mau:\s*([0-9a-f]{8})")
MUC = {"N": 0, "H": 1, "V": 2, "C": 3}
GOI_Y_DAP_AN = re.compile(r"([Cc]họn|[Đđ]áp án|[Pp]hương án)\s*(đúng\s*)?(là\s*)?\(?\s*(\\\w+\{)?[A-D]\b")
THAM_CHIEU_PA = re.compile(r"Cả|cả hai|Tất cả|tất cả|đáp án|phương án|\b[A-D] và [A-D]\b|\b[A-D], [A-D]\b")
THAM_CHIEU_Y = re.compile(r"(ý|Ý|câu|Câu|mệnh đề|khẳng định)\s*[abcd]\b|\b[abcd]\)")


def thoat(v):
    return re.sub(r"(?<!\\)([&%#_$])", r"\\\1", str(v or ""))


# ------------------------------------------------------------------ CHỌN CÂU
def _kho():
    from xem_truoc import kho
    return kho()


def _lich_su():
    try:
        return json.load(open(os.path.join(GOC, "du-lieu", "lich_su_dung.json"), encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _tach(c):
    from k12word import tach_cau
    try:
        p = tach_cau(c)
    except Exception:
        return None
    p["de"] = chuan_vecto(p.get("de") or "")[0].strip()
    p["lg"] = chuan_vecto(p.get("lg") or "")[0].strip()
    if p.get("pa"):
        p["pa"] = [chuan_vecto(x)[0].strip() for x in p["pa"]]
    return p


def _dung_duoc(c):
    from xem_truoc import hop_le
    if c.get("loai") not in ("TN", "DS", "TLN") or not hop_le(c):
        return False
    p = _tach(c)
    return bool(p and p["de"] and (c["loai"] == "TLN" or (p["pa"] and len(p["pa"]) == 4)))


def _lg_tot(c):
    p = _tach(c)
    return len(re.sub(r"\s", "", (p or {}).get("lg") or ""))


def bai_cua_lop(lop):
    """Danh sách bài của lớp + số câu TN / ĐS / TLN dùng được + đã có kiến thức chưa."""
    import kho_kien_thuc
    id_map = tai_id_map()
    K = _kho()
    dem = {}
    for c in K.values():
        d = c.get("dang_key") or ""
        if c.get("loai") in ("TN", "DS", "TLN"):
            b = d.split("-")[0]
            x = dem.setdefault(b, {"TN": 0, "DS": 0, "TLN": 0})
            x[c["loai"]] += 1
    ra = []
    for b, v in kho_kien_thuc.cac_bai(id_map).items():
        if str(v["lop"]) != str(lop):
            continue
        ra.append({"bai": b, "ten_bai": v["ten_bai"], "ten_chuong": v["ten_chuong"], "so_bai": v["so_bai"],
                   "dang": [{"k": d, "ten": (id_map.get(d, {}).get("type_name") or d).strip()} for d in v["dang"]],
                   "dem": dem.get(b, {"TN": 0, "DS": 0, "TLN": 0}), "co_kt": bool(kho_kien_thuc.doc(b).strip())})
    return ra


def _dang_cho_loai(dang, n, dem):
    """Mỗi dạng một ví dụ: n ≥ số dạng → mọi dạng; ít câu hơn → n dạng ít được dùng nhất ở các loại trước (giữ thứ tự bài)."""
    ds = list(dang) if n >= len(dang) else sorted(sorted(dang, key=lambda d: (dem.get(d, 0), dang.index(d)))[:n], key=dang.index)
    for d in ds:
        dem[d] = dem.get(d, 0) + 1
    return ds


def chon(cfg, rng):
    """→ {"TN": [ {"vd": câu, "dang": mã, "tt": [câu thực hành…]} …], …}, danh sách thiếu."""
    from phieu_bai_hoc import khoa_noi_dung
    import kho_kien_thuc
    bai = cfg["bai"]
    tat_ca_dang = (kho_kien_thuc.cac_bai().get(bai) or {}).get("dang") or []
    dang = [d for d in (cfg.get("dang") or tat_ca_dang) if d in tat_ca_dang] or tat_ca_dang
    so = {l: max(0, min(30, int((cfg.get("so") or {}).get(l, 0) or 0))) for l, *_ in LOAI}
    so_vd = max(1, min(4, int(cfg.get("so_vd") or 1)))
    theo_dang = bool(cfg.get("vd_theo_dang"))
    dem_dang = {}
    chi = set(cfg.get("chi_ma") or [])
    K, ls = _kho(), _lich_su()
    con = {}                                         # mã ví dụ → các câu con "% mau:"
    for c in K.values():
        m = MAU.search(c.get("noi_dung") or "")
        if m:
            con.setdefault(m.group(1), []).append(c)
    da, khoa_da, ra, thieu = set(), set(), {}, []

    def moi(c):
        return c["ma"] not in da and khoa_noi_dung(c) not in khoa_da

    def lay(c):
        da.add(c["ma"]); khoa_da.add(khoa_noi_dung(c))

    for l, ten_l, *_ in LOAI:
        if not so[l]:
            continue
        theo = {d: [c for c in K.values() if c.get("dang_key") == d and c.get("loai") == l and _dung_duoc(c)] for d in dang}
        if chi:                                      # chỉ câu AI vừa sinh: thực hành ⊂ chi, ví dụ là câu mẹ của chúng
            co = {d: [c for c in v if c["ma"] in chi] for d, v in theo.items()}
        else:
            co = theo
        # ví dụ theo trình tự bài học: dạng đứng trước, đủ câu để làm mẫu + thực hành thì chọn trước
        can1 = -(-so[l] // max(1, min(so_vd, so[l]))) + 1
        thu_dang = sorted([d for d in dang if co.get(d)], key=lambda d: (len(co[d]) < can1, dang.index(d)))
        if not thu_dang:
            thieu.append(f"{ten_l}: bài này chưa có câu nào dùng được — bỏ phần này.")
            continue
        nhom = []
        if theo_dang:                                # mỗi dạng đã chọn một ví dụ minh hoạ riêng
            thu_dang = _dang_cho_loai([d for d in dang if co.get(d)], so[l], dem_dang)
        n_vd = len(thu_dang) if theo_dang else min(so_vd, max(1, so[l]))
        for i in range(n_vd):
            d = thu_dang[i % len(thu_dang)]
            ung = [c for c in theo[d] if moi(c)]
            if chi:
                me = {MAU.search(c["noi_dung"]).group(1) for c in co[d] if MAU.search(c.get("noi_dung") or "")}
                ung = [c for c in ung if c["ma"] in me] or [c for c in ung if c["ma"] not in chi]
            # ví dụ: ưu tiên câu có nhiều câu con theo mẫu, mức N/H, lời giải đủ dài, ít dùng
            ung.sort(key=lambda c: (-len([x for x in con.get(c["ma"], []) if x.get("loai") == l]),
                                    MUC.get(c.get("muc_chuan") or "H", 1) > 1, _lg_tot(c) < 40,
                                    len(ls.get(c["ma"], [])), rng.random()))
            if not ung:
                continue
            vd = ung[0]
            lay(vd)
            nhom.append({"vd": vd, "dang": d, "tt": []})
        if not nhom:
            thieu.append(f"{ten_l}: không chọn được ví dụ mẫu.")
            continue
        chia = [so[l] // len(nhom) + (1 if i < so[l] % len(nhom) else 0) for i in range(len(nhom))]
        for g, can in zip(nhom, chia):
            vd, d = g["vd"], g["dang"]
            mv = MUC.get(vd.get("muc_chuan") or "H", 1)
            ds_con = [c for c in con.get(vd["ma"], []) if c.get("loai") == l and _dung_duoc(c)]
            khac = sorted((c for c in theo[d] if c not in ds_con),
                          key=lambda c: (abs(MUC.get(c.get("muc_chuan") or "H", 1) - mv), len(ls.get(c["ma"], [])), rng.random()))
            ung = [c for c in ds_con + khac if (not chi or c["ma"] in chi)]
            for c in ung:
                if len(g["tt"]) >= can:
                    break
                if moi(c):
                    lay(c); g["tt"].append(c)
            if len(g["tt"]) < can:
                thieu.append(f"{ten_l} – {d}: cần {can} câu theo mẫu, kho chỉ có {len(g['tt'])}.")
            g["tt"].sort(key=lambda c: MUC.get(c.get("muc_chuan") or "H", 1))   # dễ → khó
        ra[l] = nhom
    return ra, thieu


# ------------------------------------------------------------------ 🤖 AI SOẠN ĐÚNG CẤU TRÚC PHIẾU
P_LO = os.path.join(GOC, "du-lieu", "pnc_ai.json")
TEN_LOAI = {"TN": "Trắc nghiệm nhiều phương án", "DS": "Đúng/Sai", "TLN": "Trả lời ngắn"}


def ke_hoach(cfg):
    """Các nhóm 'ví dụ + câu tương tự' cần soạn: [(mã nhóm, loại, mã dạng, số câu tương tự)] — dạng theo trình tự bài."""
    import kho_kien_thuc
    bai = cfg["bai"]
    tat_ca = (kho_kien_thuc.cac_bai().get(bai) or {}).get("dang") or []
    dang = [d for d in (cfg.get("dang") or tat_ca) if d in tat_ca] or tat_ca
    so_vd = max(1, min(4, int(cfg.get("so_vd") or 1)))
    ra, dem = [], {}
    for l, *_ in LOAI:
        n = max(0, min(30, int((cfg.get("so") or {}).get(l, 0) or 0)))
        if not n or not dang:
            continue
        ds = _dang_cho_loai(dang, n, dem) if cfg.get("vd_theo_dang") else [dang[i % len(dang)] for i in range(min(so_vd, n))]
        k = len(ds)
        for i, d in enumerate(ds):
            ra.append((f"{l}{i + 1}", l, d, n // k + (1 if i < n % k else 0)))
    return ra


def prompt_ai(cfg, kem_kt=True):
    """Prompt nhờ AI soạn ĐÚNG cấu trúc phiếu: (kiến thức trọng tâm) + từng nhóm ví dụ minh hoạ có lời giải → câu tương tự theo mẫu."""
    import kho_kien_thuc, de_ngoai
    bai = cfg["bai"]
    x = kho_kien_thuc.cac_bai().get(bai)
    if not x:
        raise ValueError("Chưa chọn bài.")
    id_map = tai_id_map()
    kh = ke_hoach(cfg)
    if not kh:
        raise ValueError("Chưa nhập số câu thực hành.")
    lop = x["lop"]
    chung, dm, so_dm = de_ngoai._phan_chung([bai])
    ten = lambda d: (id_map.get(d, {}).get("type_name") or d).strip()
    bang = "\n".join(f"| `%%% NHOM {g} {d}` | {TEN_LOAI[l]} | {ten(d)} (mã `{d}`) | 1 | {n} |" for g, l, d, n in kh)
    cac_d = list(dict.fromkeys(d for _, _, d, _ in kh))
    ds_dang = "\n".join(f"- `{d}` — {ten(d)}" for d in cac_d)
    kt = ""
    if kem_kt:
        p = kho_kien_thuc.prompt([bai])
        dinh = p[p.index("# YÊU CẦU NỘI DUNG"):]
        kt = ("\n## PHẦN A — KIẾN THỨC TRỌNG TÂM (đặt ĐẦU khối mã, giữa hai dòng `%%% KIEN_THUC` và `%%% HET_KIEN_THUC`)\n"
              + dinh.replace("# YÊU CẦU NỘI DUNG", "### Yêu cầu nội dung").replace("# ĐỊNH DẠNG BẮT BUỘC (LaTeX, để dán thẳng vào phần mềm)", "### Định dạng")
              .replace("- Trả về DUY NHẤT một khối ```latex … ```; không \\documentclass, không \\begin{document}.\n", "") + "\n")
    p = f"""# NHIỆM VỤ
Bạn là giáo viên Toán lớp {lop} giỏi (chương trình GDPT 2018, sách Kết nối tri thức). Soạn nội dung cho **PHIẾU NGHIÊN CỨU BÀI HỌC**
— **Bài {x['so_bai']}. {x['ten_bai']}** ({x['ten_chuong']}) — đính kèm SGK / tài liệu nếu có thì bám sát.
Phiếu gồm {'kiến thức trọng tâm của bài, sau đó ' if kem_kt else ''}phần thực hành theo mẫu với 3 loại câu như đề thi 2025. Mỗi nhóm:
**1 VÍ DỤ MINH HOẠ có lời giải thật chi tiết** (học sinh đọc để học cách làm) → **các CÂU TƯƠNG TỰ** để học sinh tự làm theo đúng cách đó.

**Chỉ soạn các dạng sau** (giáo viên đã chọn) — **mỗi nhóm là MỘT dạng, có ví dụ minh hoạ RIÊNG của dạng đó**; câu thuộc dạng khác
thì nằm ở nhóm khác với ví dụ khác (vd câu 1–2 dạng A theo ví dụ 1, câu 3–4 dạng B theo ví dụ 2):
{ds_dang}
{kt}
## PHẦN {'B' if kem_kt else 'A'} — CÁC NHÓM VÍ DỤ + CÂU TƯƠNG TỰ (đúng bảng sau, đúng thứ tự)
| Dòng mở nhóm | Loại câu | Dạng | Ví dụ | Câu tương tự |
|---|---|---|---|---|
{bang}

Quy tắc từng nhóm:
1. Mở nhóm bằng một dòng riêng **chép đúng nguyên cột 1** (gồm cả mã dạng, vd `%%% NHOM TN1 {kh[0][2]}`).
2. Câu ĐẦU TIÊN của nhóm là **ví dụ minh hoạ**: dòng mở khối có thêm ` % vai: vi_du`, vd `\\begin{{ex}}%[mã] % vai: vi_du`.
   Mức Nhận biết – Thông hiểu, tiêu biểu cho dạng; **lời giải từng bước** (mỗi bước một dòng, nêu rõ công thức / lí do), cuối kết luận đáp án.
3. Sau đó đúng số **câu tương tự** ở cột 5: **cùng dạng, cùng cách giải** với ví dụ, đổi số liệu / hàm số / ngữ cảnh (không chép lại ví dụ),
   độ khó bằng hoặc nhỉnh hơn ví dụ một chút, câu sau khó hơn câu trước. Mỗi câu tương tự cũng có lời giải đầy đủ.
4. Mọi câu trong nhóm đúng loại của nhóm: TN → `\\begin{{ex}}` + `\\choice` (4 phương án, đúng một `\\True`, đáp án đúng rải đều A–D);
   Đúng/Sai → `\\begin{{ex}}` + `\\choiceTF` (4 ý a–d, lời giải `\\begin{{itemchoice}}` đủ 4 `\\itemch`); Trả lời ngắn → `\\begin{{bt}}` + `\\shortans{{…}}`
   (đáp số là một số, tối đa 4 kí tự kể cả dấu `-` và dấu `,`).
5. **Ví dụ và MỌI câu tương tự của nhóm đều đúng dạng ở cột 3** (cùng kiểu bài, cùng phương pháp giải) — không lấn sang dạng khác,
   không soạn dạng ngoài danh sách trên. Mã `%[…]` của từng câu là mã dạng của nhóm, thay `?` bằng chữ mức N / H / V / C.
6. Tự giải lại từng câu, tính lại từng phép tính trước khi viết đáp án.

""" + chung + f"""# KẾT QUẢ TRẢ VỀ
Một khối mã duy nhất ```latex … ``` gồm lần lượt: {'phần kiến thức (giữa `%%% KIEN_THUC` … `%%% HET_KIEN_THUC`), rồi ' if kem_kt else ''}các nhóm theo đúng bảng
(`%%% NHOM …` → ví dụ → câu tương tự). Không lời dẫn ngoài khối mã.

# DANH MỤC DẠNG CỦA BÀI ({so_dm} dạng)
{dm}"""
    return re.sub(r"\n{3,}", "\n\n", p)


def _doc_lo():
    try:
        return json.load(open(P_LO, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def lo_ai(bai):
    """Các lượt AI đã nhập cho bài (mới nhất trước)."""
    return list(reversed(_doc_lo().get(bai) or []))


def nhap_ai(bai, van_ban, ghi_kt="neu_trong", in_ra=print):
    """Kết quả AI → (kiến thức vào kho kiến thức) + câu vào ngân hàng (câu tương tự gắn '% mau: <mã ví dụ>')
    → lưu một 'lượt AI' (đúng nhóm ví dụ → câu tương tự) để tạo phiếu. ghi_kt: neu_trong | ghi_de | khong."""
    import kho_kien_thuc, nhap_cau
    from nh_core import tach_khoi, ma_bam, phan_tich_cau
    t = kho_kien_thuc.bo_khoi_ma(van_ban) if "```" in (van_ban or "") else (van_ban or "")
    ra = {"kien_thuc": None}
    m = re.search(r"^[ \t]*%%%[ \t]*KIEN_THUC[ \t]*$(.*?)^[ \t]*%%%[ \t]*HET_KIEN_THUC[ \t]*$", t, re.S | re.M)
    if m:
        kt = m.group(1).strip()
        t = t[:m.start()] + t[m.end():]
        co = bool(kho_kien_thuc.doc(bai).strip())
        if kt and (ghi_kt == "ghi_de" or (ghi_kt == "neu_trong" and not co)):
            kho_kien_thuc.luu(bai, kt)
            ra["kien_thuc"] = "đã lưu vào kho kiến thức"
            in_ra("📘 Kiến thức trọng tâm: đã lưu vào kho kiến thức của bài.")
        elif kt:
            ra["kien_thuc"] = "giữ kiến thức cũ (bài đã có)"
            in_ra("📘 Kiến thức trọng tâm: bài đã có — giữ bản cũ (tích “ghi đè” nếu muốn thay).")
    phan = re.split(r"^[ \t]*%%%[ \t]*NHOM[ \t]+(\S+)(?:[ \t]+(\d[A-Z]\d+[?A-Z]\d+-\d+))?[^\n]*$", t, flags=re.M)
    nhom = []                                       # [(mã nhóm, mã dạng, [khối…])]
    if len(phan) > 1:
        for i in range(1, len(phan) - 2, 3):
            nhom.append((phan[i].strip().upper(), phan[i + 1], tach_khoi(phan[i + 2])))
    else:
        nhom.append(("?", None, tach_khoi(t)))
    van, cau_truc, sua_dang = [], [], 0

    def ep_dang(k, d):                               # câu trong nhóm phải đúng dạng của nhóm: giữ mức, thay mã dạng
        nonlocal sua_dang
        dau, nl, sau = k.partition("\n")
        m = MA_DANG.search(dau)
        if m:
            muc = m.group(4) if m.group(4) != "?" else "H"
            moi = d.replace("?", muc)
            if m.group(0).strip("%[] ") == moi:
                return k
            sua_dang += 1
            return dau[:m.start()] + "%[" + moi + "]" + dau[m.end():] + nl + sau
        sua_dang += 1
        mb = re.match(r"\\begin\{(ex|bt)\}", dau)
        return (dau[:mb.end()] + "%[" + d.replace("?", "H") + "]" + dau[mb.end():] + nl + sau) if mb else k

    for g, dg, ks in nhom:
        ks = [k for k in ks if k.strip()]
        if dg:
            ks = [ep_dang(k, dg) for k in ks]
        if not ks:
            continue
        iv = next((i for i, k in enumerate(ks) if re.search(r"%\s*vai:\s*vi_du", k.split("\n", 1)[0])), 0)
        vd = ks[iv]
        h_vd = ma_bam(vd)
        tt = []
        for j, k in enumerate(ks):
            if j == iv:
                continue
            if not MAU.search(k):
                dau, _, sau = k.partition("\n")
                k = dau + "\n% mau: " + h_vd + "\n" + sau
            tt.append(k)
        try:
            l = phan_tich_cau(vd)["loai"]
        except Exception:
            l = re.sub(r"\d+$", "", g) or "?"
        cau_truc.append({"nhom": g, "loai": l, "dang": dg, "vd": h_vd, "tt": [ma_bam(k) for k in tt]})
        van += [f"%%% NHOM {g}" + (f" {dg}" if dg else ""), vd] + tt
    if not cau_truc:
        raise ValueError("Không thấy câu nào: kết quả AI cần các khối \\begin{ex}…\\end{ex} / \\begin{bt}…\\end{bt} (mỗi nhóm mở bằng %%% NHOM …).")
    if sua_dang:
        in_ra(f"🏷 Đã chỉnh mã dạng {sua_dang} câu cho đúng dạng của nhóm (theo dòng %%% NHOM).")
    thu = os.path.join(GOC, "ai-nhap")
    os.makedirs(thu, exist_ok=True)
    p = os.path.join(thu, time.strftime("%Y-%m-%d_%H%M%S") + f"_nghien_cuu_{re.sub(r'[^0-9A-Za-z]+', '_', bai)}.tex")
    ghi(p, "% nguon: AI soạn phiếu nghiên cứu bài học " + bai + "\n\n" + "\n\n".join(van) + "\n")
    bam = {}
    so_moi = nhap_cau.nhap([p], thu=False, in_ra=in_ra, bam_ra=bam)
    lo = {"id": time.strftime("%Y%m%d%H%M%S"), "luc": time.strftime("%Y-%m-%dT%H:%M"), "nhom": [], "so_moi": so_moi}
    mat = 0
    for g in cau_truc:
        vd = bam.get(g["vd"])
        tt = [bam[h] for h in g["tt"] if h in bam]
        mat += (0 if vd else 1) + len(g["tt"]) - len(tt)
        if not vd:
            in_ra(f"  ⚠ Nhóm {g['nhom']}: ví dụ minh hoạ bị loại (lỗi) — bỏ nhóm này.")
            continue
        lo["nhom"].append({"nhom": g["nhom"], "loai": g["loai"], "dang": g.get("dang"), "vd": vd, "tt": tt})
    if not lo["nhom"]:
        raise ValueError("Mọi ví dụ minh hoạ đều bị loại vì lỗi — xem nhật ký, sửa rồi nhập lại.")
    d = _doc_lo()
    d[bai] = (d.get(bai) or [])[-9:] + [lo]
    json.dump(d, open(P_LO, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    tom = {}
    for g in lo["nhom"]:
        x = tom.setdefault(g["loai"], [0, 0]); x[0] += 1; x[1] += len(g["tt"])
    in_ra("✅ Lượt AI đã lưu: " + " · ".join(f"{TEN_LOAI.get(l, l)} {v[0]} ví dụ + {v[1]} câu tương tự" for l, v in tom.items())
          + (f" (bị loại {mat} câu lỗi)" if mat else ""))
    ra.update(lo=lo, tom=tom)
    return ra


def _nhom_tu_lo(bai, lo_id):
    """Dựng nhóm phiếu đúng theo một lượt AI đã nhập."""
    lo = next((x for x in (_doc_lo().get(bai) or []) if x["id"] == lo_id), None)
    if not lo:
        raise ValueError("Không thấy lượt AI đã chọn.")
    K = _kho()
    ra, thieu = {}, []
    for g in lo["nhom"]:
        vd = K.get(g["vd"])
        if not vd:
            thieu.append(f"Nhóm {g['nhom']}: không còn ví dụ trong kho."); continue
        tt = [K[m] for m in g["tt"] if m in K]
        if len(tt) < len(g["tt"]):
            thieu.append(f"Nhóm {g['nhom']}: {len(g['tt']) - len(tt)} câu tương tự không còn trong kho.")
        l = vd.get("loai") or g["loai"]
        ra.setdefault(l, []).append({"vd": vd, "dang": vd.get("dang_key") or "", "tt": tt})
    return {l: ra[l] for l, *_ in LOAI if l in ra}, thieu


# ------------------------------------------------------------------ ĐẢO PHƯƠNG ÁN / Ý (mỗi mã đề)
def _dap_tn(k):
    m = tim_lenh(k, "choice")
    ds, _ = doc_tham_so(k, m.end(), 4) if m else (None, None)
    for i, x in enumerate(ds or []):
        if re.search(r"\\True(?![A-Za-z])", x[2]):
            return "ABCD"[i]
    return ""


def _dap_ds(k):
    m = tim_lenh(k, "choiceTF")
    ds, _ = doc_tham_so(k, m.end(), 4) if m else (None, None)
    return "".join("Đ" if re.search(r"\\True(?![A-Za-z])", x[2]) else "S" for x in (ds or []))


def _dap_tln(k):
    m = tim_lenh(k, "shortans")
    ds, _ = doc_tham_so(k, m.end(), 1) if m else (None, None)
    return re.sub(r"\s+", "", (ds[0][2] if ds else "")).replace("$", "")


def dap_an(k, loai):
    return {"TN": _dap_tn, "DS": _dap_ds, "TLN": _dap_tln}[loai](k)


def xao_tn(k, rng):
    m = tim_lenh(k, "choice")
    if not m:
        return k
    ds, _ = doc_tham_so(k, m.end(), 4)
    if not ds or GOI_Y_DAP_AN.search(k[m.end():]) or any(THAM_CHIEU_PA.search(x[2]) for x in ds):
        return k
    hv = list(range(4)); rng.shuffle(hv)
    out = k
    for (dau, cuoi, _), nd in sorted(zip(ds, [ds[i][2] for i in hv]), key=lambda x: -x[0][0]):
        out = out[:dau] + "{" + nd + "}" + out[cuoi:]
    return out


def xao_ds(k, rng):
    """Đảo ý a, b, c (giữ ý d — ý khó — ở cuối); lời giải \\itemch đảo theo."""
    m = tim_lenh(k, "choiceTF")
    if not m or THAM_CHIEU_Y.search(k):
        return k
    ds, _ = doc_tham_so(k, m.end(), 4)
    ml = tim_lenh(k, "loigiai")
    if not ds or not ml or ml.start() < ds[-1][1]:
        return k
    lg, _ = doc_tham_so(k, ml.end(), 1)
    if not lg:
        return k
    lg_dau, lg_cuoi, lg_nd = lg[0]
    mi = re.search(r"\\begin\{itemchoice\}(.*)\\end\{itemchoice\}", lg_nd, re.S)
    if not mi:
        return k
    phan = re.split(r"\\itemch(?![A-Za-z])", mi.group(1))
    if len(phan) != 5:
        return k
    hv = [0, 1, 2]; rng.shuffle(hv); hv.append(3)
    lg_moi = lg_nd[:mi.start(1)] + phan[0] + "".join("\\itemch" + phan[1 + i] for i in hv) + lg_nd[mi.end(1):]
    out = k[:lg_dau] + "{" + lg_moi + "}" + k[lg_cuoi:]
    for (dau, cuoi, _), nd in sorted(zip(ds, [ds[i][2] for i in hv]), key=lambda x: -x[0][0]):
        out = out[:dau] + "{" + nd + "}" + out[cuoi:]
    return out


# ------------------------------------------------------------------ DỰNG LATEX
def _pa_tn(pa, mau, dung=None, hep=False):
    o = [(r"\tikz[reset cm,baseline=(n.base)]\node[circle,inner sep=1pt,minimum size=1.35em,font=\bfseries\small,"
          + (f"fill={mau},text=white" if dung == "ABCD"[i] else f"draw={mau},text={mau}") + "](n){" + "ABCD"[i] + r"};\ " + pa[i])
         for i in range(4)]
    dai = max(len(re.sub(r"\\(?:dfrac|frac|left|right|limits)|[{}$\s]", "", re.sub(r"\\(?:overrightarrow|vec|sqrt|mathbb)", "##", x))) for x in pa)
    g1, g2 = (4, 11) if hep else (9, 22)
    if dai <= g1:
        return r"\par\noindent" + "".join(r"\makebox[0.25\linewidth][l]{" + x + "}" for x in o) + r"\par"
    if dai <= g2:
        return (r"\par\noindent\begin{tabular}{@{}p{0.48\linewidth}@{\hspace{0.02\linewidth}}p{0.48\linewidth}@{}}" + o[0] + " & " + o[1]
                + r"\\[3pt]" + o[2] + " & " + o[3] + r"\end{tabular}\par")
    return r"\par" + "".join(r"\noindent " + x + r"\par" for x in o)


def _bang_ds(pa, mau, dap=None):
    o = lambda ch, bat: (r"\tikz[reset cm,baseline=-0.6ex]\node[draw=" + mau + ",minimum size=1.15em,inner sep=0pt,font=\\bfseries\\small"
                         + (f",fill={mau},text=white" if bat else f",text={mau}!70") + "]{" + ch + "};")
    hang = []
    for i, x in enumerate(pa):
        d = dap[i] if dap and i < len(dap) else None
        hang.append(r"\textbf{" + "abcd"[i] + r")}\ " + x + r" & " + o("Đ", d == "Đ") + r"\ " + o("S", d == "S") + r"\\")
    return (r"\par\smallskip\noindent{\renewcommand{\arraystretch}{1.25}\begin{tabular}{@{}p{0.80\linewidth}@{\hspace{0.03\linewidth}}r@{}}"
            + r"\hline ".join(hang) + r"\end{tabular}}\par")


def _o_tln(mau, dap=None):
    ch = list((dap or "")[:4]) + [""] * (4 - len((dap or "")[:4]))
    return (r"\par\smallskip\noindent\hfill{\small Đáp số:}\ " + "".join(
        r"\tikz[reset cm,baseline=-0.7ex]\node[draw=" + mau + r",line width=0.7pt,minimum width=1.5em,minimum height=1.5em,inner sep=0pt,font=\bfseries]{"
        + x + "};" for x in ch) + r"\par")


def cau_latex(k, loai, so, mau, giai=False, nhan=None, hep=False):
    """Một câu (đã đảo nếu cần) → LaTeX in thường. giai: kèm đáp án + lời giải."""
    p = _tach({"loai": loai, "noi_dung": k})
    da = dap_an(k, loai)
    t = [r"\par\medskip\noindent{\color{" + mau + r"}\bfseries " + (nhan or f"Câu {so}.") + r"}\ " + p["de"]]
    if loai == "TN":
        t.append(_pa_tn(p["pa"], mau, da if giai else None, hep))
    elif loai == "DS":
        t.append(_bang_ds(p["pa"], mau, da if giai else None))
    else:
        t.append(_o_tln(mau, da.replace("{,}", ",") if giai else None))
    if giai:
        lg = p["lg"]
        if loai == "DS" and p.get("y_giai"):
            dau_lg, ys, cuoi_lg = p["y_giai"]
            lg = (dau_lg.strip() + r"\par" if dau_lg.strip() else "") + "".join(
                r"\par\noindent\textbf{" + "abcd"[i] + r")} " + chuan_vecto(y)[0].strip() for i, y in enumerate(ys)) + (r"\par " + cuoi_lg if cuoi_lg.strip() else "")
        t.append(r"\par\noindent\begin{tcolorbox}[enhanced,breakable,colback=" + mau + r"!4,colframe=" + mau + r"!45,boxrule=0.5pt,arc=1.5mm,"
                 r"left=2mm,right=2mm,top=1mm,bottom=1mm,title={\small\bfseries Lời giải}\hfill{\small Đáp án: \textbf{" + thoat(da.replace('{,}', ',')) + r"}},"
                 r"coltitle=white,colbacktitle=" + mau + r"!80,fonttitle=\small]" + (lg or r"\textit{(chưa có lời giải)}") + r"\end{tcolorbox}")
    return "\n".join(t)


TIEN_TO = r"""
%==================== PHIẾU NGHIÊN CỨU BÀI HỌC ====================
\definecolor{mauTN}{HTML}{4F46E5}\definecolor{mauDS}{HTML}{0D9488}\definecolor{mauTLN}{HTML}{EA580C}\definecolor{mauVD}{HTML}{0284C7}
\newcommand{\phanNC}[4]{\par\bigskip\noindent\begin{tcolorbox}[enhanced,colback=#1,colframe=#1,arc=2mm,boxrule=0pt,left=3mm,right=3mm,top=1.2mm,bottom=1.2mm,
  fontupper=\color{white}\bfseries]{#2}\ \ PHẦN #3. #4\end{tcolorbox}\par\nopagebreak}
\newtcolorbox{vdMau}[2]{enhanced,breakable,colback=#1!5,colframe=#1,boxrule=0.9pt,arc=2.5mm,left=3mm,right=3mm,top=1.5mm,bottom=2mm,
  title={\faSearch\ \ #2},fonttitle=\bfseries,coltitle=white,colbacktitle=#1,toptitle=0.6mm,bottomtitle=0.6mm}
\newcommand{\apDung}[2]{\par\medskip\noindent{\color{#1}\bfseries\faPencilSquareO\ \ ÁP DỤNG TƯƠNG TỰ}\ {\small\color{black!60}#2}\par\nopagebreak
  \noindent{\color{#1}\rule{\linewidth}{0.8pt}}\par\nopagebreak}
"""


TIEN_TO_TK = r"""
%==================== PHIẾU NGHIÊN CỨU BÀI HỌC — BẢN IN TIẾT KIỆM (chữ 11, 2 cột, ít mực) ====================
\definecolor{mauTN}{HTML}{4F46E5}\definecolor{mauDS}{HTML}{0D9488}\definecolor{mauTLN}{HTML}{EA580C}\definecolor{mauVD}{HTML}{0284C7}
\newcommand{\phanNC}[4]{\par\smallskip\noindent{\raggedright\color{#1}\bfseries #2\ PHẦN #3. #4\par}\nopagebreak\noindent{\color{#1}\rule{\linewidth}{0.6pt}}\par\nopagebreak}
\newtcolorbox{vdMau}[2]{enhanced,breakable,colback=white,colframe=#1!70,boxrule=0.4pt,arc=1mm,left=1.5mm,right=1.5mm,top=0.8mm,bottom=0.8mm,
  title={\faSearch\ #2},fonttitle=\bfseries\small,coltitle=#1,colbacktitle=white,toptitle=0.3mm,bottomtitle=0mm,titlerule=0pt}
\newcommand{\apDung}[2]{\par\smallskip\noindent{\color{#1}\bfseries\small\faPencilSquareO\ ÁP DỤNG TƯƠNG TỰ}\ {\scriptsize\color{black!60}#2}\par\nopagebreak}
\usepackage{multicol}\setlength{\columnsep}{0.5cm}\setlength{\columnseprule}{0.3pt}
\AtBeginEnvironment{multicols}{\tikzset{every picture/.append style={scale=0.75,transform shape}}}
\renewcommand{\immini}[3][]{{\tieudehinh #2}\par\nopagebreak{\centering #3\par}}
"""


def _kien_thuc(bai, kem_pp, dang):
    from phieu_bai_hoc import chuan_kien_thuc
    import kho_kien_thuc
    kt = kho_kien_thuc.doc(bai).strip()
    if not kt:
        return None
    if not kem_pp:
        import beamer_phieu
        gon = beamer_phieu.tach_phuong_phap(kt, dang)[0].strip()
        # phần chung quá ngắn (bài soạn kiến thức chủ yếu theo dạng) → giữ cả phương pháp cho đủ ý
        if gon and not (len(gon) < 400 and len(gon) < 0.35 * len(kt)):
            kt = gon
    return chuan_kien_thuc(kt)


def tao(cfg, in_ra=print, chi_tinh=False):
    """cfg: bai, dang[], so{TN,DS,TLN}, so_vd, so_ma, ma_bat_dau, co_chu (12|14), kho (a4|a5), mau_trinh_bay, kem_pp,
    giao_vien, ten, chi_ma[], seed.  chi_tinh=True: chỉ chọn câu để xem trước (không ghi file)."""
    import mau_phieu, kho_kien_thuc
    from phieu_bai_hoc import ten_tep, tieu_de_ten
    rng = random.Random(cfg.get("seed") or time.time())
    bai = cfg.get("bai") or ""
    tt_bai = kho_kien_thuc.cac_bai().get(bai)
    if not tt_bai:
        raise ValueError("Chưa chọn bài học.")
    nhom, thieu = _nhom_tu_lo(bai, cfg["lo"]) if cfg.get("lo") else chon(cfg, rng)
    id_map = tai_id_map()
    ten_dang = lambda d: (id_map.get(d, {}).get("type_name") or d).strip()
    if chi_tinh:
        return {"nhom": {l: [{"vd": {"ma": g["vd"]["ma"], "muc": g["vd"].get("muc_chuan"), "de": (_tach(g["vd"]) or {}).get("de", "")[:220]},
                              "dang": g["dang"], "ten_dang": ten_dang(g["dang"]), "tt": [x["ma"] for x in g["tt"]]} for g in v]
                         for l, v in nhom.items()},
                "thieu": thieu, "co_kt": bool(kho_kien_thuc.doc(bai).strip())}
    if not any(g["tt"] or g["vd"] for v in nhom.values() for g in v):
        raise ValueError("Bài này chưa có câu nào dùng được.")
    tt = {**cau_hinh().get("thong_tin_de", {}), **{k: v for k, v in cfg.items() if v not in (None, "")}}
    gv = (tt.get("giao_vien") or "").strip()
    lop = tt_bai["lop"]
    ten = (cfg.get("ten") or "").strip() or tt_bai["ten_bai"] or bai
    so_ma = max(1, min(12, int(cfg.get("so_ma") or 1)))
    bd = int(str(cfg.get("ma_bat_dau") or "1") or 1)
    cac_ma = [str(bd + i).zfill(3) for i in range(so_ma)]
    co = "14" if str(cfg.get("co_chu") or "14") == "14" else "12"
    a5 = cfg.get("kho") == "a5"
    # ---------- thư mục + khung
    out_goc = thu_muc_xuat(ten_tep(f"Phiếu Nghiên Cứu Bài Học - {ten} - {time.strftime('%d-%m-%Y')}", 90), tt_bai["dang"], "phieu")
    out = os.path.join(out_goc, "tex")
    os.makedirs(out_goc)
    src = os.path.join(GOC, "khung", "DeThiChinhThuc")
    shutil.copytree(src, out, ignore=shutil.ignore_patterns("mau_de.tex", "*.bat"))
    mau = doc_tep(os.path.join(src, "mau_de.tex"))
    for a, v in {"<<SO_GD>>": tt.get("so_gd", ""), "<<TRUONG>>": tt.get("truong", ""), "<<TEN_KY_THI>>": ten,
                 "<<NAM_HOC>>": tt.get("nam_hoc", ""), "<<MON>>": f"TOÁN – Lớp {lop}", "<<THOI_GIAN>>": "", "<<CHAN_TRANG>>": ten}.items():
        mau = mau.replace(a, thoat(v))
    mau_tk = mau                                   # bản in tiết kiệm dựng từ mẫu gốc
    co_ext = bool(shutil.which("kpsewhich") and subprocess.run(["kpsewhich", "extbook.cls"], capture_output=True, text=True).stdout.strip())
    if co == "14" and co_ext:
        mau = re.sub(r"\\documentclass\[\d+pt,a4paper", r"\\documentclass[14pt,a4paper", mau, count=1).replace("]{book}", "]{extbook}", 1)
    else:
        mau = re.sub(r"\\documentclass\[\d+pt,", r"\\documentclass[12pt,", mau, count=1)
    le = ("a5paper,left=0.9cm,right=0.8cm,top=0.9cm,bottom=1.2cm,footskip=0.55cm" if a5
          else "a4paper,left=1.5cm,right=1.3cm,top=1.2cm,bottom=1.5cm,footskip=0.65cm")
    mau = re.sub(r"\\usepackage\[a4paper,[^\]]*\]\{geometry\}", lambda m: "\\usepackage[" + le + "]{geometry}", mau, count=1)
    mau = mau.replace("\\setlength{\\parskip}{6pt}", "\\setlength{\\parskip}{3pt}")
    chan = thoat(f"Phiếu nghiên cứu bài học: {ten}"[:60])
    them = [r"\pagestyle{fancy}\fancyhf{}\renewcommand{\headrulewidth}{0pt}\renewcommand{\footrulewidth}{0.4pt}",
            r"\fancyfoot[L]{\footnotesize " + ("GV: " + thoat(gv) if gv else "") + r"}\fancyfoot[C]{\footnotesize " + ("" if a5 else chan)
            + r"}\fancyfoot[R]{\footnotesize Mã \maDeNC\ · Trang \thepage/\pageref{trangCuoiPhieu}}",
            r"\fancypagestyle{plain}{\fancyhf{}\fancyfoot[L]{\footnotesize " + ("GV: " + thoat(gv) if gv else "")
            + r"}\fancyfoot[R]{\footnotesize Mã \maDeNC\ · Trang \thepage/\pageref{trangCuoiPhieu}}}",
            mau_phieu.mo_dau(cfg.get("mau_trinh_bay")), TIEN_TO]
    if co == "14" and not co_ext:                  # máy không có gói extsizes: phóng chữ thường lên 14pt
        them.append(r"\usepackage{anyfontsize}\makeatletter\renewcommand\normalsize{\@setfontsize\normalsize{14}{17}}\normalsize\makeatother")
    mau = mau.replace("\\begin{document}", "\n".join(them) + "\n\\begin{document}", 1)
    mau_goc = mau_tk
    hai_cot = cfg.get("so_cot_tk", 2) != 1           # bản tiết kiệm / phiếu làm bài: 2 cột (mặc định) hoặc 1 cột
    cot_mo, cot_dong = ("\n\\begin{multicols}{2}\n", "\n\\end{multicols}\n") if hai_cot else ("\n", "\n")
    if cfg.get("lam_bai"):                          # ✏ phiếu làm bài tiết kiệm: chữ 10, 2 cột, mỗi câu 1 dòng làm bài
        mau_lb = re.sub(r"\\documentclass\[\d+pt,", r"\\documentclass[10pt,", mau_goc, count=1)
        mau_lb = re.sub(r"\\usepackage\[a4paper,[^\]]*\]\{geometry\}",
                        lambda m: "\\usepackage[a4paper,left=0.9cm,right=0.8cm,top=0.8cm,bottom=1.1cm,footskip=0.5cm]{geometry}", mau_lb, count=1)
        mau_lb = mau_lb.replace("\\setlength{\\parskip}{6pt}", "\\setlength{\\parskip}{1pt}").replace("\\setstretch{1.1}", "\\setstretch{1.0}")
        them_lb = [x for x in them if x is not TIEN_TO and "anyfontsize" not in x] + [TIEN_TO_TK,
                   r"\newcommand{\dongLam}{\par\nopagebreak\noindent\makebox[\linewidth]{\rule{0pt}{6.5mm}{\color{black!40}\dotfill}}\par\medskip}"]
        mau_lb = mau_lb.replace("\\begin{document}", "\n".join(them_lb) + "\n\\begin{document}", 1)
    if cfg.get("tiet_kiem"):
        mau_tk = re.sub(r"\\documentclass\[\d+pt,", r"\\documentclass[11pt,", mau_tk, count=1)
        mau_tk = re.sub(r"\\usepackage\[a4paper,[^\]]*\]\{geometry\}",
                        lambda m: "\\usepackage[a4paper,left=1.0cm,right=0.9cm,top=0.9cm,bottom=1.2cm,footskip=0.55cm]{geometry}", mau_tk, count=1)
        mau_tk = mau_tk.replace("\\setlength{\\parskip}{6pt}", "\\setlength{\\parskip}{1pt}").replace("\\setstretch{1.1}", "\\setstretch{1.0}")
        them_tk = [x for x in them if x is not TIEN_TO and "anyfontsize" not in x] + [TIEN_TO_TK]
        mau_tk = mau_tk.replace("\\begin{document}", "\n".join(them_tk) + "\n\\begin{document}", 1)
    # ---------- phần chung
    kt = _kien_thuc(bai, bool(cfg.get("kem_pp")), tt_bai["dang"])
    if kt is None:
        thieu.insert(0, "Bài này chưa có kiến thức trọng tâm trong kho — phiếu chừa dòng kẻ để học sinh tự ghi "
                        "(soạn kiến thức ở Phiếu bài học → Kiến thức trọng tâm).")
        kien = r"\begin{khungKT}{\small\itshape Học sinh tự ghi: định nghĩa, tính chất, công thức trọng tâm của bài.}\dongKe{7}\end{khungKT}"
    else:
        kien = r"\begin{khungKT}" + "\n{\\setstretch{1.25}\n" + kt + "\n\\par}\n\\end{khungKT}"
    chuong = (tt_bai.get("ten_chuong") or "").strip()
    phu = thoat(f"Toán {lop}" + (f" · {chuong}" if chuong else ""))

    def dau(tieu, ma, ho_ten):
        return (r"\dauPhieuKhung{" + thoat(tt.get("truong") or "") + "}{" + thoat(tt.get("nam_hoc") or "") + "}{" + tieu + "}{"
                + tieu_de_ten(ten, thoat) + "}{" + phu + r" · \textbf{Mã " + ma + "}}{" + ("1" if ho_ten else "0") + "}")

    cot_unt, tom, tc_nhom = {}, [], []
    tong_tt = sum(len(g["tt"]) for v in nhom.values() for g in v)
    for mi, ma in enumerate(cac_ma):
        r_ma = random.Random(f"{cfg.get('seed') or ''}{ma}{bai}")
        hs, gv_, hs_tk = [], [], []
        so, so_vd, phan = 0, 0, 0
        cot_unt[ma] = []
        for l, ten_l, mau_l, bt, hd in LOAI:
            v = nhom.get(l)
            if not v:
                continue
            phan += 1
            tieu = r"\phanNC{" + mau_l + "}{" + bt + "}{" + str(phan) + "}{" + ten_l + "}"
            hs += [tieu, r"{\small\itshape " + hd + "}"]
            hs_tk += [tieu, r"{\scriptsize\itshape " + hd + "}"]
            gv_.append(tieu)
            for g in v:
                so_vd += 1
                k_vd = chuan_vecto(g["vd"]["noi_dung"])[0]
                vd = (r"\begin{vdMau}{mauVD}{VÍ DỤ MINH HOẠ " + str(so_vd) + r" — " + thoat(ten_dang(g["dang"])) + "}\n"
                      + cau_latex(k_vd, l, 0, "mauVD", giai=True, nhan="Ví dụ.") + "\n\\end{vdMau}")
                hs.append(vd); gv_.append(vd)
                hs_tk.append(r"\begin{vdMau}{mauVD}{VÍ DỤ " + str(so_vd) + r" — " + thoat(ten_dang(g["dang"])) + "}\n"
                             + cau_latex(k_vd, l, 0, "mauVD", giai=True, nhan="Ví dụ.", hep=hai_cot) + "\n\\end{vdMau}")
                if mi == 0:
                    tc_nhom.append({"loai": l, "so_vd": so_vd, "dang": ten_dang(g["dang"]), "vd": k_vd, "tt": []})
                if not g["tt"]:
                    continue
                hd_tt = f"{len(g['tt'])} câu — làm theo cách của ví dụ {so_vd}"
                hs.append(r"\apDung{" + mau_l + "}{" + hd_tt + "}"); gv_.append(r"\apDung{" + mau_l + "}{" + hd_tt + "}")
                hs_tk.append(r"\apDung{" + mau_l + "}{" + hd_tt + "}")
                ds = list(g["tt"])
                if mi:                               # mã đầu giữ đúng thứ tự dễ → khó; các mã sau đảo thứ tự trong nhóm
                    r_ma.shuffle(ds)
                for c in ds:
                    k = chuan_vecto(c["noi_dung"])[0]
                    if mi:
                        k = xao_tn(k, r_ma) if l == "TN" else xao_ds(k, r_ma) if l == "DS" else k
                    so += 1
                    hs.append(cau_latex(k, l, so, mau_l))
                    hs_tk.append(cau_latex(k, l, so, mau_l, hep=hai_cot) + "\n<<DONG_LAM>>")
                    gv_.append(cau_latex(k, l, so, mau_l, giai=True))
                    if mi == 0:
                        tc_nhom[-1]["tt"].append((so, k))
                    cot_unt[ma].append((l, dap_an(k, l)))
        # bảng trả lời của học sinh + bảng đáp án
        def bang(dien):
            o, hang = [], []
            for i, (l, d) in enumerate(cot_unt[ma], 1):
                hang.append((str(i), (d.replace("{,}", ",") if dien else "")))
            for j in range(0, len(hang), 10):
                kh = hang[j:j + 10]
                o.append(r"\noindent\begin{tabular}{|l|" + "c|" * len(kh) + r"}\hline\textbf{Câu} & " + " & ".join(r"\textbf{" + a + "}" for a, _ in kh)
                         + r"\\\hline\textbf{" + ("Đáp án" if dien else "Trả lời") + "} & " + " & ".join(
                             (r"\rule{0pt}{5mm}" + thoat(b)) if b else r"\rule{0pt}{6mm}\hspace{7mm}" for _, b in kh) + r"\\\hline\end{tabular}\par\smallskip")
            return "\n".join(o)
        het = r"\par\bigskip\begin{center}{\small\itshape --- Hết ---}\end{center}\label{trangCuoiPhieu}"
        than_hs = ("\\def\\maDeNC{" + ma + "}\n" + dau("PHIẾU NGHIÊN CỨU BÀI HỌC", ma, True) + "\n"
                   + r"\phanPhieu{I. KIẾN THỨC TRỌNG TÂM}" + "\n" + kien + "\n" + r"\phanPhieu{II. THỰC HÀNH THEO MẪU}" + "\n"
                   + "\n".join(hs) + ("\n" + r"\phanPhieu{BẢNG TRẢ LỜI}" + "\n" + bang(False) if cot_unt[ma] else "") + "\n" + het)
        than_gv = ("\\def\\maDeNC{" + ma + "}\n" + dau("LỜI GIẢI – PHIẾU NGHIÊN CỨU BÀI HỌC", ma, False) + "\n"
                   + (r"\phanPhieu{BẢNG ĐÁP ÁN}" + "\n" + bang(True) + "\n" if cot_unt[ma] else "")
                   + r"\phanPhieu{THỰC HÀNH THEO MẪU – LỜI GIẢI CHI TIẾT}" + "\n" + "\n".join(gv_) + "\n" + het)
        ghi(os.path.join(out, f"De_{ma}.tex"), mau_phieu.gan_bieu_tuong(mau.replace("<<CHE_DO_LOI_GIAI>>", "\\anloigiai").replace("<<NOI_DUNG>>", than_hs)))
        if cfg.get("tiet_kiem"):
            than_tk = ("\\def\\maDeNC{" + ma + "}\n" + dau("PHIẾU NGHIÊN CỨU BÀI HỌC", ma, True) + "\n"
                       + r"\phanPhieu{I. KIẾN THỨC TRỌNG TÂM}" + "\n" + kien.replace("\\dongKe{7}", "\\dongKe{5}") + "\n"
                       + r"\phanPhieu{II. THỰC HÀNH THEO MẪU}" + cot_mo + "\n".join(hs_tk) + cot_dong
                       + (r"\phanPhieu{BẢNG TRẢ LỜI}" + "\n" + bang(False) if cot_unt[ma] else "") + "\n" + het)
            ghi(os.path.join(out, f"De_{ma}_TietKiem.tex"), mau_phieu.gan_bieu_tuong(
                mau_tk.replace("<<CHE_DO_LOI_GIAI>>", "\\anloigiai").replace("<<NOI_DUNG>>", than_tk.replace("<<DONG_LAM>>", ""))))
        if cfg.get("lam_bai"):
            than_lb = ("\\def\\maDeNC{" + ma + "}\n" + dau("PHIẾU NGHIÊN CỨU BÀI HỌC", ma, True) + "\n"
                       + r"\phanPhieu{I. KIẾN THỨC TRỌNG TÂM}" + "\n" + kien.replace("\\dongKe{7}", "\\dongKe{4}") + "\n"
                       + r"\phanPhieu{II. THỰC HÀNH THEO MẪU}" + cot_mo + "\n".join(hs_tk).replace("<<DONG_LAM>>", r"\dongLam")
                       + cot_dong + (r"\phanPhieu{BẢNG TRẢ LỜI}" + "\n" + bang(False) if cot_unt[ma] else "") + "\n" + het)
            ghi(os.path.join(out, f"De_{ma}_LamBai.tex"), mau_phieu.gan_bieu_tuong(
                mau_lb.replace("<<CHE_DO_LOI_GIAI>>", "\\anloigiai").replace("<<NOI_DUNG>>", than_lb)))
        ghi(os.path.join(out, f"De_{ma}_LoiGiai.tex"), mau_phieu.gan_bieu_tuong(mau.replace("<<CHE_DO_LOI_GIAI>>", "\\hienthiloigiai").replace("<<NOI_DUNG>>", than_gv)))
        tom.append(f"Mã {ma}: " + " ".join(d.replace("{,}", ",") for _, d in cot_unt[ma]))
    if tong_tt:
        ghi_dap_an_unt(os.path.join(out_goc, "DapAn_UNT.xlsx"), cac_ma, cot_unt)
    if cfg.get("trinh_chieu"):
        tao_trinh_chieu(out, ten, tt, lop, chuong, gv, kt, tc_nhom, cac_ma[0])
    json.dump({**cfg, "cac_ma": cac_ma,
               "chon": {l: [{"vd": g["vd"]["ma"], "tt": [c["ma"] for c in g["tt"]]} for g in v] for l, v in nhom.items()}},
              open(os.path.join(out, "cau_hinh_phieu_nghien_cuu.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    dem = {l: (len(v), sum(len(g["tt"]) for g in v)) for l, v in nhom.items()}
    in_ra(f"🔬 Phiếu nghiên cứu bài học «{ten}» — {len(cac_ma)} mã đề ({', '.join(cac_ma)}), cỡ chữ {co}{' · khổ A5' if a5 else ''}")
    for l, ten_l, *_ in LOAI:
        if l in dem:
            in_ra(f"   {ten_l.title()}: {dem[l][0]} ví dụ mẫu + {dem[l][1]} câu thực hành")
    for x in thieu:
        in_ra("  ⚠ " + x)
    if tong_tt:
        in_ra("📊 DapAn_UNT.xlsx — " + str(tong_tt) + " câu × " + str(len(cac_ma)) + " mã đề")
    if cfg.get("lam_bai"):
        in_ra(f"✏ Phiếu làm bài tiết kiệm: LamBai_<mã>.pdf (chữ 10, {2 if hai_cot else 1} cột, mỗi câu 1 dòng làm bài)")
    if cfg.get("tiet_kiem"):
        in_ra(f"📄 Bản in tiết kiệm giấy: TietKiem_<mã>.pdf (chữ 11, phần thực hành {2 if hai_cot else 1} cột, ít mực)")
    if cfg.get("trinh_chieu"):
        in_ra(f"🖥 Trình chiếu trên lớp: TrinhChieu_{cac_ma[0]}.pdf (16:9 — ví dụ → đáp án → lời giải; câu tự làm theo thứ tự mã {cac_ma[0]})")
    return out_goc


# ------------------------------------------------------------------ 🖥 TRÌNH CHIẾU TRÊN LỚP (Beamer 16:9)
MAU_TC = {"TN": ("4F46E5", "EEF2FF"), "DS": ("0D9488", "F0FDFA"), "TLN": ("EA580C", "FFF7ED"), "VD": ("0284C7", "E0F2FE")}


def tao_trinh_chieu(out_tex, ten, tt, lop, chuong, gv, kt, tc_nhom, ma):
    """TrinhChieu_<mã>.tex: bìa → lộ trình → kiến thức trọng tâm → từng phần: mở phần → ví dụ (đề → đáp án → lời giải)
    → câu tự làm (đề → đáp án → lời giải để chữa) → tổng kết. Dùng giao diện Beamer của Phiếu bài học."""
    from k12word import tach_cau
    from beamer_de import dau_beamer, khung_cau, tho
    from beamer_phieu import GIAO_DIEN, bo_ky_tu_toan
    tt2 = dict(tt, ten_ky_thi=f"GV: {gv}  ·  Phiếu nghiên cứu bài học: {ten}"[:90])
    dau = dau_beamer(out_tex, "xanh", tt2, ma, "2/3")
    dau = dau.replace(r"\begin{document}", GIAO_DIEN + r"\begin{document}", 1)
    dau = re.sub(r"\\setbeamertemplate\{footline\}\{\\hspace\*\{0\.3cm\}\{\\fontsize\{5\}\{6\}\\selectfont\\color\{xanhDam\}\\TENKY\\ -- Mã đề \\MADE\}.*?\n.*?\n",
                 "", dau, count=1, flags=re.S)
    f = [dau]
    dat = lambda k: r"\datMau{" + MAU_TC[k][0] + "}{" + MAU_TC[k][1] + "}" + "\n"
    f.append(dat("VD"))
    f.append(r"\begin{frame}[plain]\nenTrangTri\centering\vfill" "\n"
             r"{\small " + tho(tt.get("truong") or "") + r"}\par\bigskip" "\n"
             r"\begin{tcolorbox}[enhanced,colback=mauHT,colframe=mauHT,coltext=white,arc=4mm,boxrule=0pt,interior style={left color=mauHT,right color=mauHT!55!white},halign=center,width=0.86\linewidth,drop fuzzy shadow]"
             r"{\large\bfseries PHIẾU NGHIÊN CỨU BÀI HỌC}\par\smallskip{\LARGE\bfseries " + tho(ten.upper() if len(ten) <= 46 else ten) + r"}\end{tcolorbox}\par\medskip" "\n"
             r"{\normalsize Toán " + str(lop) + (r" \,·\, " + tho(chuong) if chuong else "") + r"}\par\vfill" "\n"
             r"{\small GV: " + tho(gv) + r"}\par\vspace*{0.6cm}\end{frame}" "\n")
    # lộ trình
    ten_l = {"TN": "Trắc nghiệm nhiều phương án", "DS": "Trắc nghiệm Đúng – Sai", "TLN": "Trả lời ngắn"}
    dem = {}
    for g in tc_nhom:
        x = dem.setdefault(g["loai"], [0, 0]); x[0] += 1; x[1] += len(g["tt"])
    dong = [r"\item[{\tikz[baseline=(n.base)]\node[rounded corners=2pt,fill=mauHT,text=white,font=\bfseries\scriptsize,inner sep=2.5pt](n){I};}] Kiến thức trọng tâm"]
    for j, l in enumerate([l for l in ("TN", "DS", "TLN") if l in dem], 1):
        dong.append(r"\definecolor{mauMuc}{HTML}{" + MAU_TC[l][0] + r"}\item[{\tikz[baseline=(n.base)]\node[rounded corners=2pt,fill=mauMuc,text=white,font=\bfseries\scriptsize,inner sep=2.5pt](n){Phần "
                    + str(j) + "};}] " + ten_l[l] + r" \,—\, {\small\color{black!60}" + str(dem[l][0]) + " ví dụ minh hoạ · " + str(dem[l][1]) + " câu tự làm}")
    f.append(r"\begin{frame}[t]{Lộ trình bài học}{" + tho(ten) + r"}\hieuung\nenTrangTri" "\n"
             r"\vuaKhung{\begin{itemize}[leftmargin=4.2em,itemsep=6pt,label={}]" + "\n".join(dong) + r"\end{itemize}}" "\n\\end{frame}\n")
    # kiến thức
    if kt and kt.strip():
        if len(kt) > 1800:
            f.append(r"\begin{frame}[t,allowframebreaks]{Kiến thức trọng tâm}{" + tho(ten) + "}\n\\small\n" + kt + "\n\\end{frame}\n")
        else:
            f.append(r"\begin{frame}[t]{Kiến thức trọng tâm}{" + tho(ten) + r"}\hieuung\nenTrangTri" "\n"
                     r"\begin{hopKT}{\setlength\caoToiDa{0.66\textheight}\vuaKhung{\kieuKT " + kt + r"}}\end{hopKT}" "\n\\end{frame}\n")
    # từng phần
    phan = 0
    for l in ("TN", "DS", "TLN"):
        ds = [g for g in tc_nhom if g["loai"] == l]
        if not ds:
            continue
        phan += 1
        f.append(dat(l))
        f.append(r"\begin{frame}[plain]\hieuung\nenTrangTri\centering\vfill" "\n"
                 r"\tikz\node[circle,fill=mauHT,text=white,minimum size=2.1cm,font=\bfseries\Huge,drop shadow]{" + str(phan) + r"};\par\medskip" "\n"
                 r"{\Large\bfseries\color{mauHT} PHẦN " + str(phan) + r"}\par\smallskip{\Large\bfseries " + ten_l[l].upper() + r"}\par\medskip"
                 r"{\small\color{black!60}" + str(dem[l][0]) + r" ví dụ minh hoạ \,·\, " + str(dem[l][1]) + r" câu áp dụng tương tự}\vfill\end{frame}" "\n")
        for g in ds:
            p = tach_cau({"loai": l, "noi_dung": g["vd"]})
            da = dap_an(g["vd"], l).replace("{,}", ",")
            fr = khung_cau(1, l, r"\nhanViDu\ " + tho(g["dang"]), p, da, True)
            fr = fr.replace("[t]{Câu 1}", "[t]{Ví dụ " + str(g["so_vd"]) + "}", 1).replace("{Lời giải câu 1", "{Lời giải ví dụ " + str(g["so_vd"]))
            f.append(fr)
            if g["tt"]:
                f.append(r"\begin{frame}[plain]\hieuung\nenTrangTri\centering\vfill{\Large\bfseries\color{mauHT}\faPencilSquareO\ ÁP DỤNG TƯƠNG TỰ}\par\medskip"
                         r"{\normalsize Làm " + str(len(g["tt"])) + r" câu theo cách của ví dụ " + str(g["so_vd"]) + r" \,·\, câu "
                         + ", ".join(str(s) for s, _ in g["tt"]) + r" trên phiếu}\vfill\end{frame}" "\n")
            for so, k in g["tt"]:
                p = tach_cau({"loai": l, "noi_dung": k})
                da = dap_an(k, l).replace("{,}", ",")
                fr = khung_cau(so, l, r"\nhanTuLam\ " + ten_l[l], p, da, True)
                f.append(fr)
    f.append(dat("VD"))
    f.append(r"\begin{frame}[plain]\nenTrangTri\centering\vfill{\LARGE\bfseries\color{mauHT} TỔNG KẾT}\par\bigskip" "\n"
             r"{\large Ôn lại kiến thức trọng tâm \,·\, hoàn thành các câu còn lại trên phiếu \,·\, đối chiếu đáp án}\par\bigskip"
             r"{\normalsize\itshape Chúc các em học tốt!}\vfill\end{frame}" "\n\\end{document}\n")
    ghi(os.path.join(out_tex, f"TrinhChieu_{ma}.tex"), bo_ky_tu_toan("".join(f)))
