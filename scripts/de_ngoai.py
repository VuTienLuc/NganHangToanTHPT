# -*- coding: utf-8 -*-
"""ĐỀ TỪ NGUỒN NGOÀI (Word / PDF / ảnh) → gõ lại hoặc AI soạn mới → xem trước, bổ sung hình TikZ → trộn nhiều mã đề.

Hai chế độ tạo prompt cho AI bên ngoài (ChatGPT, Gemini, Claude… — thầy đính kèm file đề/tài liệu):
  go_lai : gõ lại NGUYÊN VĂN đề có sẵn thành 3 loại câu (TN, Đúng/Sai, Trả lời ngắn; tự luận nếu có), giải lại để kiểm đáp án,
           câu có hình thì gõ mã TikZ ngay trong câu đó (không vẽ chắc → chỗ trống % CAN_VE_HINH để thầy bổ sung).
  soan   : đọc tài liệu (đề, bài học) rồi SOẠN ĐỀ MỚI xoay quanh nội dung đó theo số câu từng loại × mức thầy chọn,
           lời giải chi tiết từng bước (để chiếu Beamer sửa bài).
Kết quả AI (khối LaTeX ex/bt hoặc JSON) → doc() tách câu + soát lỗi → xem_truoc() biên dịch từng câu thành ảnh
→ chen_hinh() chèn TikZ đúng câu → ứng dụng gửi sang Trộn đề (nhiều mã đề, đáp án Excel, Beamer lời giải).
"""
import os, re, json, base64, shutil, tempfile, subprocess
from nh_core import GOC, tach_khoi, phan_tich_cau, tim_pdflatex, doc as doc_file, tai_id_map, chuan_vecto

LOAI_TEN = {"TN": "Trắc nghiệm", "DS": "Đúng/Sai", "TLN": "Trả lời ngắn", "TL": "Tự luận"}
MUC_TEN = {"N": "Nhận biết", "H": "Thông hiểu", "V": "Vận dụng", "C": "Vận dụng cao"}
TIKZ = re.compile(r"\\begin\{tikzpicture\}[\s\S]*?\\end\{tikzpicture\}")
CHO_HINH = re.compile(r"[ \t]*[^\n]*CAN_VE_HINH[^\n]*\n?")
MO_TA = re.compile(r"\[\s*H[iì]nh\s*:?\s*([^\]]*)\]")


def so_lop(lop):
    lop = int(lop or 10)
    return {10: "0", 11: "1", 12: "2"}.get(lop, str(lop))


# ------------------------------------------------------------------ PROMPT
def _phan_chung(pham_vi):
    import tao_prompt
    mau = tao_prompt.MAU
    chung = mau[mau.index("# ĐỊNH DẠNG BẮT BUỘC"):mau.index("# KẾT QUẢ TRẢ VỀ")]
    dm, so = tao_prompt.danh_muc(pham_vi) if pham_vi else ("", 0)
    return chung, dm, so


def prompt(kieu, cfg):
    cfg = cfg or {}
    lop = int(cfg.get("lop") or 10)
    pham_vi = [x for x in (cfg.get("pham_vi") or []) if x] or ([so_lop(lop)] if cfg.get("kem_ma_dang", True) else [])
    chung, dm, so = _phan_chung(pham_vi)
    if not cfg.get("kem_ma_dang", True):
        chung = chung[:chung.find("# CHỌN MÃ DẠNG")] + chung[chung.find("# TỰ KIỂM TRA"):] if "# CHỌN MÃ DẠNG" in chung else chung
        chung = chung.replace("- [ ] Mọi mã `%[…]` có trong DANH MỤC (sau khi thay `?` bằng N/H/V/C).\n", "")
        ma_dang = ("- Dòng mở khối chỉ cần mức: `\\begin{ex}%[?]` — KHÔNG cần mã dạng (thầy chỉ trộn đề, chưa nhập kho).\n")
        chung = chung.replace("Mã lấy từ DANH MỤC DẠNG ở cuối: chép mã `2D1?1-2` rồi **thay dấu `?` bằng chữ mức**:",
                              "**Lần này KHÔNG cần mã dạng** (không có danh mục): mọi câu ghi `%[?]`. Thang mức để tham khảo:")
    else:
        ma_dang = ""
    nguon = (cfg.get("nguon") or "").strip()
    ghi = (cfg.get("ghi_chu") or "").strip()
    if kieu == "go_lai":
        dau = f"""# NHIỆM VỤ
Thầy là giáo viên Toán. Đính kèm là **một đề kiểm tra / phiếu bài tập / bài học** (file Word, PDF hoặc ảnh chụp){(': ' + nguon) if nguon else ''}.
Hãy **gõ lại TOÀN BỘ các câu hỏi** thành mã LaTeX theo đúng định dạng bên dưới để thầy **trộn thành nhiều mã đề**.

## Yêu cầu quan trọng
1. **KHÔNG thay đổi nội dung**: giữ nguyên văn lời dẫn, số liệu, kí hiệu, cách hỏi, thứ tự phương án và thứ tự câu của đề.
   Không bỏ câu, không gộp câu, không thêm câu. Chỉ sửa lỗi chính tả hiển nhiên.
2. **Xếp đúng 3 loại câu** theo cấu trúc đề:
   - Phần I – Trắc nghiệm nhiều phương án → `\\begin{{ex}}` + `\\choice` (4 phương án, đúng một `\\True`).
   - Phần II – Đúng/Sai → `\\begin{{ex}}` + `\\choiceTF` (4 ý a, b, c, d).
   - Phần III – Trả lời ngắn → `\\begin{{bt}}` + `\\shortans{{đáp số}}`.
   {'- Tự luận (nếu đề có) → `\\begin{bt}` không có `\\shortans`.' if cfg.get("giu_tl", True) else '- Đề có phần tự luận: BỎ QUA phần đó (chỉ gõ 3 loại câu trên).'}
3. **Kiểm lại đáp án**: tự giải lại TỪNG câu, tính lại từng phép tính.
   - Đề có đáp án: so với kết quả giải. Khớp → dùng. KHÔNG khớp → đánh `\\True` / `\\shortans` theo kết quả **đúng** và ghi ở dòng mở khối
     `% KIEM_TRA: đề ghi <x>, giải ra <y> – <lý do ngắn>`.
   - Đề không có đáp án: tự giải, viết lời giải ngắn gọn đúng chuẩn; câu nào chưa chắc chắn ghi `% KIEM_TRA: <lý do>`.
   - Câu đề sai/thiếu dữ kiện (không có phương án đúng, nhiều đáp án): vẫn gõ nguyên văn và ghi `% KIEM_TRA: <mô tả>`.
4. **Hình vẽ**: câu nào có hình (đồ thị, hình học, bảng biến thiên, bảng xét dấu, sơ đồ) thì gõ **mã TikZ ngay trong câu đó**,
   đúng vị trí như mục HÌNH VẼ bên dưới (bên phải đề bằng `\\immini` hoặc giữa đề trong `center`), vẽ đúng số liệu, nhãn điểm của hình gốc.
   Hình phức tạp không vẽ chắc chắn đúng → để chỗ trống `\\begin{{center}}\\textit{{[Hình: mô tả ngắn hình gốc]}}\\end{{center}} % CAN_VE_HINH`
   ngay chỗ hình trong câu (thầy sẽ bổ sung mã TikZ sau). Không bỏ qua hình.
{ma_dang}{('5. Yêu cầu thêm của thầy: ' + ghi) if ghi else ''}

"""
        cuoi = f"""# KẾT QUẢ TRẢ VỀ
Một khối mã duy nhất ```latex … ``` chứa lần lượt mọi câu **theo đúng thứ tự trong đề** (Phần I → II → III{' → Tự luận' if cfg.get('giu_tl', True) else ''}).
Dòng đầu khối: `% nguồn: <tên đề, trường, năm học nếu có>`.
Sau khối mã, liệt kê ngắn: số câu mỗi loại; các câu có `% KIEM_TRA` (đáp án đề khác kết quả giải…); các câu có `% CAN_VE_HINH`.
"""
    elif kieu == "soan":
        bang, tong = [], 0
        for l in ("TN", "DS", "TLN", "TL"):
            v = [max(0, int(x or 0)) for x in ((cfg.get("so") or {}).get(l) or [0, 0, 0, 0])][:4]
            v += [0] * (4 - len(v))
            if sum(v):
                tong += sum(v)
                bang.append(f"| {LOAI_TEN[l]} | " + " | ".join(str(x) for x in v) + f" | **{sum(v)}** |")
        if not tong:
            raise ValueError("Chưa nhập số câu.")
        cach = {"bam_sat": "BÁM SÁT tài liệu: lấy ý tưởng từ lý thuyết, ví dụ, bài tập trong tài liệu; ĐỔI số liệu, đổi ngữ cảnh thành câu mới (không chép nguyên văn).",
                "sang_tao": "SOẠN MỚI hoàn toàn cùng dạng, cùng mức với nội dung tài liệu (chỉ dùng kiến thức có trong tài liệu).",
                "ket_hop": "KẾT HỢP: khoảng một nửa bám sát ví dụ/bài tập của tài liệu (đổi số liệu), một nửa soạn mới cùng dạng."
                }.get(cfg.get("cach") or "ket_hop")
        dau = f"""# NHIỆM VỤ
Thầy là giáo viên Toán lớp {lop} (chương trình GDPT 2018, sách Kết nối tri thức). Đính kèm là **tài liệu** (đề kiểm tra, bài học, phiếu bài tập — Word, PDF hoặc ảnh){(': ' + nguon) if nguon else ''}.
Hãy **đọc kỹ toàn bộ tài liệu** (kiến thức, công thức, ví dụ, dạng bài, mức độ) rồi **SOẠN MỘT ĐỀ KIỂM TRA MỚI** xoay quanh đúng nội dung đó.

## Cách soạn
- {cach}
- Chỉ dùng kiến thức, kí hiệu có trong tài liệu (và các bài trước); phủ đều các nội dung chính của tài liệu, không dồn một dạng.
- Trắc nghiệm: phương án nhiễu lấy từ **lỗi sai thường gặp** (sai dấu, nhầm công thức, quên điều kiện…); đáp án đúng **rải đều A, B, C, D**.
- Đúng/Sai: 4 ý tăng dần độ khó a → d; các câu có số ý đúng khác nhau.
- Trả lời ngắn: đáp số là một số, tối đa 4 kí tự (kể cả `-` và `,`); cần làm tròn thì nói rõ trong đề.
- {'Ưu tiên **toán thực tế** ở các câu Vận dụng / Vận dụng cao.' if cfg.get('thuc_te') else 'Có một số câu vận dụng gắn tình huống thực tế khi phù hợp.'}
- **Lời giải chi tiết từng bước** (mỗi bước một dòng, cuối dòng `\\\\`) — thầy dùng để chiếu Beamer sửa bài; đáp án đã **giải lại hai lần** và khớp lời giải.
- Câu cần hình: gõ mã TikZ ngay trong câu (mục HÌNH VẼ); hình không vẽ chắc → `\\begin{{center}}\\textit{{[Hình: mô tả]}}\\end{{center}} % CAN_VE_HINH`.
{ma_dang}{('- Yêu cầu thêm của thầy: ' + ghi) if ghi else ''}

## Số câu cần soạn (tổng {tong} câu)
| Loại câu | Nhận biết (N) | Thông hiểu (H) | Vận dụng (V) | Vận dụng cao (C) | Cộng |
|---|---|---|---|---|---|
{chr(10).join(bang)}

Mức của từng câu đúng như bảng (chữ mức N/H/V/C ghi trong mã `%[…]`).

"""
        cuoi = """# KẾT QUẢ TRẢ VỀ
Một khối mã duy nhất ```latex … ``` chứa các câu xếp theo loại (Trắc nghiệm → Đúng/Sai → Trả lời ngắn → Tự luận), trong mỗi loại theo mức N → H → V → C.
Dòng đầu khối: `% nguồn: Soạn từ <tên tài liệu>`.
Sau khối mã, liệt kê ngắn: số câu theo loại × mức; các câu có `% KIEM_TRA` hoặc `% CAN_VE_HINH`.
"""
        chung = chung.replace("Đủ số câu như đề", "Đủ số câu theo loại × mức như bảng")
        chung = re.sub(r"- Đề có đáp án/lời giải: dùng của đề\. Đề \*\*không\*\* có: ", "- ", chung)
    else:
        raise ValueError("Kiểu prompt không hợp lệ.")
    p = dau + chung + cuoi + ((f"\n# DANH MỤC DẠNG ({so} dạng) — chỉ dùng các mã dưới đây\n" + dm) if dm and cfg.get("kem_ma_dang", True) else "")
    return re.sub(r"\n{3,}", "\n\n", p)


def prompt_ve_hinh(k):
    """Prompt nhỏ nhờ AI vẽ riêng hình TikZ cho một câu (kèm đề + mô tả chỗ trống)."""
    import tao_prompt
    mau = tao_prompt.MAU
    hd = mau[mau.index("# HÌNH VẼ (TikZ)"):mau.index("# CHỌN MÃ DẠNG")]
    mt = MO_TA.search(k)
    return ("# NHIỆM VỤ\nVẽ bằng TikZ hình minh hoạ cho câu hỏi Toán dưới đây"
            + (f" (hình gốc: {mt.group(1).strip()})" if mt else "") + ", đúng số liệu, đúng nhãn điểm như đề"
            + " (đính kèm ảnh hình gốc nếu có).\nChỉ trả về MỘT khối ```latex``` chứa đúng một `\\begin{tikzpicture} … \\end{tikzpicture}` "
            + "(không \\documentclass, không lời dẫn).\n\n# CÂU HỎI\n```latex\n" + k.strip() + "\n```\n\n" + hd)


# ------------------------------------------------------------------ ĐỌC KẾT QUẢ AI
def _bo_rao(t):
    t = (t or "").replace("\r", "").lstrip("\ufeff")
    khoi = re.findall(r"```[a-zA-Z]*\s*\n([\s\S]*?)```", t)
    return "\n\n".join(khoi) if khoi and any("\\begin{" in x or x.strip()[:1] in "{[" for x in khoi) else t


def chuan(k):
    from nhap_cau import sua_thap_phan
    k, _ = sua_thap_phan(k.strip())
    k, _ = chuan_vecto(k)
    return k


def doc(van_ban, ten="de_ai.tex"):
    """Văn bản AI trả về (LaTeX ex/bt hoặc JSON) → danh sách khối câu."""
    t = _bo_rao(van_ban)
    s = t.strip()
    if s[:1] in "{[" and "\\begin{ex}" not in s and "\\begin{bt}" not in s:
        import doc_nhap
        t = doc_nhap.doc_tep(os.path.splitext(ten)[0] + ".json", noi_dung=s)
    return [chuan(k) for k in tach_khoi(t)]


def _ngoac(s, i):
    """s[i] == '{' → vị trí ngay sau '}' tương ứng (bỏ qua \\{ \\})."""
    sau, j = 0, i
    while j < len(s):
        c = s[j]
        if c == "\\":
            j += 2; continue
        if c == "{":
            sau += 1
        elif c == "}":
            sau -= 1
            if sau == 0:
                return j + 1
        j += 1
    return -1


def _sach_hien(t):
    """LaTeX của đề → chuỗi để xem nhanh bằng MathJax (hình thay bằng nhãn)."""
    t = re.sub(r"(?<!\\)%[^\n]*", "", t)
    t = TIKZ.sub(lambda m: "[🖼 bảng biến thiên]" if "tkzTab" in m.group(0) else "[🖼 hình TikZ]", t)
    while True:
        m = re.search(r"\\immini(\[[^\]]*\])?\s*\{", t)
        if not m:
            break
        a = _ngoac(t, m.end() - 1)
        if a < 0:
            break
        b0 = re.match(r"\s*\{", t[a:])
        b = _ngoac(t, a + b0.end() - 1) if b0 else a
        t = t[:m.start()] + t[m.end():a - 1] + " " + (t[a + b0.end():b - 1] if b0 else "") + t[b:]
    t = re.sub(r"\\(begin|end)\{(center|enumerate|itemize|itemchoice|minipage)\}(\{[^}]*\})?", "", t)
    t = re.sub(r"\\(item|itemch)\b", "<br>• ", t)
    t = re.sub(r"\\textbf\{([^{}]*)\}", r"<b>\1</b>", t)
    t = re.sub(r"\\textit\{([^{}]*)\}|\\emph\{([^{}]*)\}", lambda m: "<i>" + (m.group(1) or m.group(2) or "") + "</i>", t)
    t = re.sub(r"\\\\(\[[^\]]*\])?", "<br>", t)
    return re.sub(r"\s*\n\s*", " ", t).strip()


def thong_tin(k):
    """Thông tin một khối câu để xem trước + danh sách lỗi cần sửa."""
    from kiem_bien_dich import kiem_tinh
    from k12word import tach_cau
    try:
        info = phan_tich_cau(k)
    except Exception:
        return {"loai": "?", "loi": ["khối câu không đọc được"], "de": "", "pa": None}
    loai = info["loai"]
    p = tach_cau({"loai": loai, "noi_dung": k})
    loi = kiem_tinh(k)
    if loai in ("TN", "DS") and not (p["pa"] and len(p["pa"]) == 4):
        loi.append("cần đúng 4 phương án / 4 ý")
    if loai == "TN" and not info["dap_an"]:
        loi.append("chưa đánh dấu đáp án đúng (\\True)")
    if loai == "DS" and p["lg"] and not p["y_giai"]:
        loi.append("lời giải Đúng/Sai chưa đủ 4 \\itemch")
    if not info["co_loi_giai"]:
        loi.append("thiếu lời giải")
    dong1 = k.split("\n", 1)[0]
    kt = re.findall(r"KIEM_TRA\s*:?\s*([^\n%]*)", k)
    can_ve = "CAN_VE_HINH" in k
    mo_ta = [x.strip() for x in MO_TA.findall(k)] if can_ve else []
    return {"loai": loai, "muc": info["muc"] or "", "ma_dang": info["id"] or "", "dap_an": info["dap_an"] or "",
            "so_hinh": len(TIKZ.findall(k)), "can_ve": can_ve, "mo_ta_hinh": mo_ta,
            "kiem_tra": [x.strip() for x in kt if x.strip()], "loi": loi, "nguon": "nguồn" in dong1,
            "de": _sach_hien(p["de"]), "pa": [_sach_hien(x) for x in p["pa"]] if p["pa"] else None,
            "lg": _sach_hien(p["lg"] or "")[:1500]}


def kiem_tat_ca(cac_khoi):
    ds = [dict(thong_tin(k), tex=k) for k in cac_khoi]
    dem = {l: sum(1 for c in ds if c["loai"] == l) for l in LOAI_TEN}
    return {"cau": ds, "dem": dem, "so_loi": sum(1 for c in ds if c["loi"]), "can_ve": sum(1 for c in ds if c["can_ve"]),
            "kiem_tra": sum(1 for c in ds if c["kiem_tra"])}


# ------------------------------------------------------------------ CHÈN HÌNH TIKZ VÀO ĐÚNG CÂU
MOC = re.compile(r"\\(choiceTF|choice|shortans|loigiai)(?![A-Za-z])")


def _bo_immini(than):
    m = re.search(r"\\immini(\[[^\]]*\])?\s*\{", than)
    if not m:
        return than
    a = _ngoac(than, m.end() - 1)
    b0 = re.match(r"\s*\{", than[a:]) if a > 0 else None
    if not b0:
        return than
    b = _ngoac(than, a + b0.end() - 1)
    return than[:m.start()] + than[m.end():a - 1].strip() + "\n" + than[b:]


def chen_hinh(k, tikz, vi_tri="giua", thay=False):
    """Chèn (các) khối tikzpicture vào câu k: thay chỗ trống % CAN_VE_HINH nếu có, ngược lại đặt trước \\choice/\\shortans/\\loigiai.
    vi_tri: 'giua' (center) | 'phai' (\\immini, hình bên phải đề). thay=True: bỏ hình cũ trong phần đề trước khi chèn."""
    hinh = TIKZ.findall(_bo_rao(tikz or ""))
    if not hinh:
        raise ValueError("Không thấy khối \\begin{tikzpicture} … \\end{tikzpicture} trong mã dán vào.")
    hinh = "\n".join(h.strip() for h in hinh)
    m0 = re.match(r"\\begin\{(ex|bt)\}[^\n]*\n?", k)
    dau, than = k[:m0.end()], k[m0.end():]
    mm = MOC.search(than)
    vt = mm.start() if mm else than.rfind("\\end{")
    de, sau = than[:vt], than[vt:]
    if thay:
        de = _bo_immini(de)
        de = re.sub(r"\\begin\{center\}\s*(?:\\resizebox\{[^}]*\}\{[^}]*\}\{)?\s*" + TIKZ.pattern + r"\s*\}?\s*\\end\{center\}", "", de)
        de = TIKZ.sub("", de)
    cho = CHO_HINH.search(de)
    if vi_tri == "phai" and "\\immini" not in de:
        if cho:
            de = de[:cho.start()] + de[cho.end():]
        de = "\t\\immini{" + de.strip() + "}\n\t{" + hinh + "}\n\t"
    else:
        khoi = "\\begin{center}\n" + hinh + "\n\\end{center}\n"
        if cho:
            de = de[:cho.start()] + "\t" + khoi + de[cho.end():]
        else:
            de = de.rstrip() + "\n\t" + khoi + "\t"
    return chuan(dau + de + sau)


def bo_cho_hinh(k):
    """Bỏ chỗ trống [Hình: …] % CAN_VE_HINH (thầy quyết định không cần hình)."""
    return CHO_HINH.sub("", k)


# ------------------------------------------------------------------ XEM TRƯỚC: BIÊN DỊCH TỪNG CÂU THÀNH ẢNH
def xem_truoc(cac_khoi, dpi=80, bat_dau=0):
    """→ {"ok", "loi_chung", "anh": [base64 png | None], "loi": {i: [lỗi LaTeX]}}. Một lần pdflatex cho cả đề."""
    pdfl = tim_pdflatex()
    if not pdfl:
        return {"ok": False, "loi_chung": "Máy chưa có pdflatex — chỉ xem nhanh được.", "anh": [None] * len(cac_khoi), "loi": {}}
    khung = os.path.join(GOC, "khung", "DeThiChinhThuc")
    mau = doc_file(os.path.join(khung, "mau_de.tex"))
    tam = tempfile.mkdtemp(prefix="xem_ngoai_")
    try:
        for x in os.listdir(khung):
            s, d = os.path.join(khung, x), os.path.join(tam, x)
            (shutil.copytree if os.path.isdir(s) else shutil.copy)(s, d)
        than = ["\\newwrite\\ngoaiw\\immediate\\openout\\ngoaiw=trang.txt",
                "\\Opensolutionfile{ans}[Ans/kt]\\Opensolutionfile{ansbook}[Ansbook/kt]\\Opensolutionfile{ansbt}[Ansbook/ktb]"]
        for i, k in enumerate(cac_khoi):
            than.append("\\clearpage\\setcounter{ex}{" + str(i + bat_dau) + "}\\setcounter{bt}{" + str(i + bat_dau) + "}\\immediate\\write\\ngoaiw{" + str(i) + " \\thepage}")
            than.append("%@@CAU " + str(i))
            than.append(k)
        than.append("\\clearpage\\immediate\\write\\ngoaiw{het \\thepage}\\immediate\\closeout\\ngoaiw")
        than.append("\\Closesolutionfile{ans}\\Closesolutionfile{ansbook}\\Closesolutionfile{ansbt}")
        t = mau.replace("<<CHE_DO_LOI_GIAI>>", "\\hienthiloigiai").replace("<<NOI_DUNG>>", "\n".join(than))
        t = re.sub(r"<<[A-Z_]+>>", "", t).replace("\\pagestyle{fancy}", "\\pagestyle{empty}")
        open(os.path.join(tam, "xem.tex"), "w", encoding="utf-8").write(t)
        dong_cau, cur = [], None
        for l in t.split("\n"):
            m = re.match(r"%@@CAU (\d+)$", l)
            if m:
                cur = int(m.group(1))
            dong_cau.append(cur)
        try:
            subprocess.run([pdfl, "-interaction=nonstopmode", "xem.tex"],
                           cwd=tam, capture_output=True, timeout=60 + 4 * len(cac_khoi),
                           env=dict(os.environ, TEXINPUTS=os.environ.get("NH_TEXINPUTS", "") + ":"))
        except subprocess.TimeoutExpired:
            return {"ok": False, "loi_chung": "Biên dịch quá lâu.", "anh": [None] * len(cac_khoi), "loi": {}}
        loi = {}
        try:
            log = open(os.path.join(tam, "xem.log"), encoding="latin-1").read().split("\n")
        except OSError:
            log = []
        for i, l in enumerate(log):
            if l.startswith("!"):
                for x in log[i:i + 14]:
                    m = re.match(r"l\.(\d+)", x)
                    if m:
                        n = int(m.group(1))
                        c = dong_cau[n - 1] if 0 < n <= len(dong_cau) else None
                        if c is not None:
                            thong = "LaTeX: " + l[2:80].strip()
                            loi.setdefault(c, [])
                            if thong not in loi[c] and len(loi[c]) < 3:
                                loi[c].append(thong)
                        break
        pdf = os.path.join(tam, "xem.pdf")
        anh = [None] * len(cac_khoi)
        if not os.path.exists(pdf):
            return {"ok": False, "loi_chung": "Không biên dịch được (lỗi LaTeX nặng).", "anh": anh, "loi": loi}
        trang = {}
        for l in open(os.path.join(tam, "trang.txt"), encoding="utf-8", errors="ignore"):
            p = l.split()
            if len(p) == 2 and p[1].isdigit():
                trang[p[0]] = int(p[1])
        subprocess.run(["pdftoppm", "-r", str(dpi), "-png", pdf, os.path.join(tam, "tr")], capture_output=True, timeout=120)
        tep = sorted(f for f in os.listdir(tam) if f.startswith("tr-") and f.endswith(".png"))
        so_trang = {int(re.search(r"(\d+)\.png$", f).group(1)): os.path.join(tam, f) for f in tep}
        from PIL import Image, ImageChops
        het = trang.get("het", max(so_trang or {0: 0}) + 1)
        for i in range(len(cac_khoi)):
            a = trang.get(str(i))
            if not a:
                continue
            b = trang.get(str(i + 1), het)
            hinh = []
            for pg in range(a, max(a + 1, b)):
                if pg in so_trang:
                    im = Image.open(so_trang[pg]).convert("RGB")
                    bb = ImageChops.difference(im, Image.new("RGB", im.size, "white")).getbbox()
                    if bb:
                        hinh.append(im.crop((max(0, bb[0] - 6), max(0, bb[1] - 6), min(im.width, bb[2] + 6), min(im.height, bb[3] + 6))))
            if hinh:
                w = max(h.width for h in hinh)
                g = Image.new("RGB", (w, sum(h.height for h in hinh)), "white")
                y = 0
                for h in hinh:
                    g.paste(h, (0, y)); y += h.height
                p = os.path.join(tam, f"cau_{i}.png")
                g.save(p, optimize=True)
                anh[i] = base64.b64encode(open(p, "rb").read()).decode()
        return {"ok": True, "loi_chung": "", "anh": anh, "loi": {str(k): v for k, v in loi.items()}}
    finally:
        shutil.rmtree(tam, ignore_errors=True)


def ghep(cac_khoi, nguon=""):
    """Các khối → nội dung file .tex để Trộn đề (giữ thứ tự)."""
    return ("% nguồn: " + nguon + "\n\n" if nguon else "") + "\n\n".join(k.strip() for k in cac_khoi) + "\n"
