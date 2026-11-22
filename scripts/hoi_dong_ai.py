#!/usr/bin/env python3
"""Hội đồng AI: nhiều hãng AI phản biện chéo câu hỏi trước khi nhập ngân hàng.

Phân vai theo sở trường (thầy đổi được ở ⚙ Khoá AI…):
  • Soạn câu        — Gemini   : nhanh, rẻ, tiếng Việt tốt, ngữ cảnh dài → soạn nhiều câu đa dạng theo mẫu.
  • Giải độc lập    — DeepSeek : mô hình suy luận (deepseek-reasoner) mạnh về toán → giải lại câu đã XOÁ đáp án,
                                 máy tự so đáp số với đáp án người soạn.
  • Phản biện       — ChatGPT  : soát sư phạm — đúng chương trình GDPT 2018, đúng dạng/mức độ, phương án nhiễu,
                                 câu chữ rõ ràng, đề đủ dữ kiện.
  • Tổng biên tập   — Claude   : sửa LaTeX/lời giải cẩn thận, chỉ sửa câu bị gắn cờ, quyết định giữ / loại.
Câu sau khi sửa được giải lại lần nữa; vẫn lệch đáp án → loại. Không đủ 4 hãng thì tự dồn vai,
cố giữ người GIẢI khác người SOẠN.
"""
import json, re

import sinh_tuong_tu as ST
from nh_core import phan_tich_cau, doc_tham_so, tim_lenh

VAI = {
    "soan":      {"ten": "Soạn câu",          "uu_tien": ["gemini", "claude", "openai", "deepseek"]},
    "giai":      {"ten": "Giải độc lập",      "uu_tien": ["deepseek", "openai", "claude", "gemini"]},
    "phan_bien": {"ten": "Phản biện sư phạm", "uu_tien": ["openai", "claude", "gemini", "deepseek"]},
    "bien_tap":  {"ten": "Tổng biên tập",     "uu_tien": ["claude", "openai", "gemini", "deepseek"]},
    "khuon":     {"ten": "Viết khuôn câu (code)", "uu_tien": ["claude", "openai", "deepseek", "gemini"]},
}
THU_TU = ["soan", "giai", "phan_bien", "bien_tap", "khuon"]
HOI_DONG = ["soan", "giai", "phan_bien", "bien_tap"]
LY_DO_VAI = {("khuon", "claude"): "viết code Python chặt chẽ, ít lỗi — hợp viết khuôn câu",
             ("khuon", "openai"): "viết code tốt, sửa lỗi theo phản hồi nhanh",
             ("khuon", "deepseek"): "giỏi toán và code, rẻ",
             ("khuon", "gemini"): "nhanh, rẻ; code đôi khi cần sửa nhiều lần"}
LY_DO = {
    "gemini": "nhanh, rẻ, tiếng Việt tốt, ngữ cảnh dài — hợp soạn nhiều câu đa dạng",
    "deepseek": "mô hình suy luận mạnh về toán — hợp giải lại để bắt đáp án sai",
    "openai": "soát lỗi sư phạm, câu chữ, phương án nhiễu tốt",
    "claude": "cẩn thận, LaTeX chuẩn, sửa lời giải chặt chẽ — hợp tổng biên tập",
}
# mô hình riêng theo vai (khoá thầy đặt mô hình cụ thể thì giữ của thầy)
MO_THEO_VAI = {("giai", "deepseek"): "deepseek-reasoner"}
LO = 6          # số câu mỗi lần gửi giải / phản biện


def cac_nha():
    return sorted({k["nha"] for k in ST.doc_khoa()["ds"]})


def phan_vai(cau_hinh=None, co=None):
    """→ {vai: nhà}. cau_hinh: {vai: nhà | "tu_dong"}; co: các nhà đang có khoá."""
    co = list(co if co is not None else cac_nha())
    if not co:
        return {}
    cau_hinh = cau_hinh if cau_hinh is not None else (ST.doc_khoa().get("vai") or {})
    ra = {}
    for v in THU_TU:
        chon = cau_hinh.get(v)
        if chon in co:
            ra[v] = chon
            continue
        uu = [n for n in VAI[v]["uu_tien"] if n in co]
        if v == "giai" and len(co) > 1:                 # người giải nên khác người soạn
            uu = [n for n in uu if n != ra.get("soan")] or uu
        if v == "phan_bien" and len(co) > 1:            # phản biện khác người soạn (đủ hãng thì khác cả người giải)
            uu = ([n for n in uu if n not in (ra.get("soan"), ra.get("giai"))] if len(co) > 2 else []) or \
                 [n for n in uu if n != ra.get("soan")] or uu
        ra[v] = uu[0]
    return ra


def mo_ta_vai(vai):
    return [{"vai": v, "ten": VAI[v]["ten"], "nha": vai.get(v), "ten_nha": ST.TEN_NHA.get(vai.get(v), vai.get(v) or "—"),
             "ly_do": LY_DO_VAI.get((v, vai.get(v))) or LY_DO.get(vai.get(v), "")} for v in THU_TU]


def xoay_cho(vai_ten, nha, ghi=print):
    ds = [dict(k) for k in ST.doc_khoa()["ds"] if k["nha"] == nha]
    mo = MO_THEO_VAI.get((vai_ten, nha))
    for k in ds:
        if mo and not k.get("mo_hinh"):
            k["mo_hinh"] = mo
    suy_luan = bool(mo and "reason" in mo)
    return ST.XoayKhoa(ds, ghi=ghi, timeout=480 if suy_luan else 240, max_tok=24000 if suy_luan else 8000)


# ───────────── tiện ích LaTeX ─────────────
def _bo_nhom(t, ten):
    """Xoá \\ten{...} (cả nhóm)."""
    while True:
        m = tim_lenh(t, ten)
        if not m:
            return t
        ds, sau = doc_tham_so(t, m.end(), 1)
        if not ds:
            return t[:m.start()] + t[m.end():]
        t = t[:m.start()] + t[sau:]


def de_khong_dap_an(khoi):
    """Đề cho người giải: bỏ dòng chú thích, \\loigiai, \\shortans, dấu \\True."""
    t = re.sub(r"^\\begin\{(?:ex|bt)\}[^\n]*\n", "", khoi)
    t = re.sub(r"\\end\{(?:ex|bt)\}\s*$", "", t.strip())
    t = "\n".join(l for l in t.split("\n") if not l.lstrip().startswith("%"))
    t = _bo_nhom(_bo_nhom(t, "loigiai"), "shortans")
    t = re.sub(r"\\True(?![A-Za-z])\s*", "", t)
    return t.strip()


def _so(x):
    x = str(x or "").strip().strip("$").replace("\\,", "").replace(" ", "").replace("−", "-")
    x = re.sub(r"\\(?:d|t)?frac\{(-?[\d.,]+)\}\{(-?[\d.,]+)\}", r"\1/\2", x)
    x = x.replace(",", ".")
    try:
        if "/" in x:
            a, b = x.split("/", 1)
            return float(a) / float(b)
        return float(x)
    except Exception:
        return None


def khop(loai, tac_gia, nguoi_giai):
    """True / False / None (không so được)."""
    a, b = (tac_gia or "").strip(), str(nguoi_giai or "").strip()
    if not a or not b or b in ("-", "?"):
        return None
    if loai == "TN":
        return a.upper() == re.sub(r"[^A-D]", "", b.upper())[:1]
    if loai == "DS":
        b = re.sub(r"[^ĐSDTF]", "", b.upper().replace("đ", "Đ")).replace("D", "Đ").replace("T", "Đ").replace("F", "S")
        return a == b[:4] if len(b) >= 4 else None
    if loai == "TLN":
        x, y = _so(a), _so(b)
        if x is None or y is None:
            return a.replace(" ", "") == b.replace(" ", "")
        return abs(x - y) <= max(0.051, 0.006 * abs(x))      # chấp nhận sai số làm tròn đáp số 4 ô
    return None


def _json(t):
    t = re.sub(r"```(?:json)?", "", t or "")
    i, j = t.find("["), t.rfind("]")
    if i < 0 or j <= i:
        return []
    try:
        return json.loads(t[i:j + 1])
    except Exception:
        try:
            return json.loads(re.sub(r",\s*([\]}])", r"\1", t[i:j + 1]))
        except Exception:
            return []


# ───────────── prompt từng vai ─────────────
def prompt_giai(cau):
    p = ["Em là giáo viên Toán giỏi. Hãy TỰ GIẢI độc lập từng câu dưới đây (đề đã xoá đáp án) — tính toán cẩn thận, kiểm tra lại.",
         "Trả về DUY NHẤT một mảng JSON, mỗi phần tử: {\"cau\": số thứ tự, \"dap_an\": ..., \"ghi_chu\": \"ngắn, nếu đề sai/thiếu dữ kiện/nhiều đáp án\"}.",
         "Quy ước dap_an: TN → một chữ A/B/C/D; DS → 4 ký tự Đ/S theo ý a,b,c,d (vd \"ĐSSĐ\"); TLN → đáp số (số thập phân dùng dấu phẩy); TL → kết quả cuối thật ngắn.",
         "Câu không có phương án nào đúng → dap_an \"?\" và ghi rõ trong ghi_chu.", ""]
    for i, c in enumerate(cau, 1):
        p.append(f"### Câu {i} ({c['loai']})\n{de_khong_dap_an(c['khoi'])}\n")
    return "\n".join(p)


def prompt_phan_bien(cau, ngu_canh):
    p = ["Em là chuyên gia thẩm định đề Toán theo chương trình GDPT 2018 (Việt Nam). Phản biện từng câu dưới đây:",
         "1) Đúng nội dung bài/dạng và lớp; không vượt chương trình. 2) Mức độ (NB/TH/VD/VDC) đúng như yêu cầu.",
         "3) Đề đủ dữ kiện, một cách hiểu, câu chữ tiếng Việt chuẩn. 4) TN: đúng 1 phương án đúng, phương án nhiễu hợp lý (sinh từ lỗi sai thường gặp).",
         "5) Lời giải đúng, đủ bước. 6) TLN: đáp số ghi được trong 4 ô (kể cả dấu - và dấu phẩy).",
         "Trả về DUY NHẤT mảng JSON: [{\"cau\": số, \"ket_luan\": \"dat\"|\"sua\"|\"loai\", \"ly_do\": \"ngắn, nêu cụ thể cần sửa gì\"}].",
         "Chỉ \"loai\" khi câu sai bản chất/không cứu được; lỗi nhỏ → \"sua\".", ""]
    if ngu_canh:
        p.insert(1, f"Bối cảnh: {ngu_canh}")
    for i, c in enumerate(cau, 1):
        p.append(f"### Câu {i} ({c['loai']}{', mức ' + c['muc'] if c.get('muc') else ''})\n{c['khoi']}\n")
    return "\n".join(p)


def prompt_bien_tap(cau):
    p = ["Em là tổng biên tập ngân hàng đề Toán LaTeX. Các câu dưới đây bị hội đồng gắn cờ. Với MỖI câu:",
         "- Sửa cho đúng (đề, phương án, đánh dấu \\True, \\shortans, lời giải) dựa trên ý kiến người giải và người phản biện; tự kiểm tra lại phép tính.",
         "- Giữ nguyên dòng đầu \\begin{..}%[mã]... và mọi dòng chú thích %; giữ cấu trúc môi trường (\\choice / \\choiceTF / \\shortans / \\loigiai).",
         "- Nếu người giải đúng mà đáp án tác giả sai → sửa đáp án và lời giải; nếu tác giả đúng → giữ đáp án, làm lời giải rõ hơn.",
         "Định dạng trả lời cho từng câu, đúng thứ tự:",
         "% cau: <số>\n\\begin{ex}...\\end{ex}   (hoặc \\begin{bt}...\\end{bt})",
         "hoặc nếu không thể cứu: một dòng `LOAI <số>: <lý do>`.",
         "Không viết gì khác ngoài các khối trên.", ""]
    for c in cau:
        p.append(f"### Câu {c['so']} ({c['loai']})\nÝ kiến hội đồng: {'; '.join(c['co'])}\n{c['khoi']}\n")
    return "\n".join(p)


def tach_bien_tap(t):
    """→ ({so: khối mới}, {so: lý do loại})"""
    t = re.sub(r"```(?:latex|tex)?", "", t or "")
    sua, loai = {}, {}
    for m in re.finditer(r"^\s*LOAI\s+(\d+)\s*:?\s*(.*)$", t, re.M):
        loai[int(m.group(1))] = m.group(2).strip()
    for m in re.finditer(r"%\s*cau:\s*(\d+)\s*\n\s*(\\begin\{(ex|bt)\}.*?\\end\{\3\})", t, re.S):
        sua[int(m.group(1))] = m.group(2).strip()
    return sua, loai


def gan_nguon(khoi, vai):
    ten = lambda v: ST.TEN_NHA.get(vai.get(v), vai.get(v) or "?")
    dong = f"% nguon: Hội đồng AI ({ten('soan')} soạn · {ten('giai')} giải · {ten('phan_bien')} phản biện · {ten('bien_tap')} duyệt)"
    if re.search(r"^% nguon:.*$", khoi, re.M):
        return re.sub(r"^% nguon:.*$", lambda _: dong, khoi, count=1, flags=re.M)
    return re.sub(r"^(\\begin\{(?:ex|bt)\}[^\n]*\n)", lambda m: m.group(1) + dong + "\n", khoi, count=1)


# ───────────── quy trình duyệt ─────────────
class HoiDong:
    def __init__(self, ghi=print, vai=None):
        self.ghi = ghi
        self.vai = vai or phan_vai()
        if not self.vai:
            raise ST.HetKhoa("Chưa có khoá API AI — bấm ⚙ Khoá AI…")
        self._xoay = {}
        self.thong_ke = {"vao": 0, "dat": 0, "sua": 0, "loai": 0}

    def xoay(self, v):
        if v not in self._xoay:
            self._xoay[v] = xoay_cho(v, self.vai[v], ghi=self.ghi)
        return self._xoay[v]

    def ten(self, v):
        return ST.TEN_NHA.get(self.vai[v], self.vai[v])

    def gioi_thieu(self):
        self.ghi("🧑‍⚖️ Hội đồng AI: " + " · ".join(f"{VAI[v]['ten']} = {self.ten(v)}" for v in HOI_DONG))
        if len({self.vai[v] for v in HOI_DONG}) == 1:
            self.ghi("   ⚠ Chỉ có khoá một hãng — hội đồng vẫn chạy nhưng tự kiểm chính mình, nên thêm khoá hãng khác.")

    def _goi(self, v, prompt):
        try:
            t, _, k = self.xoay(v).goi(prompt)
            return t
        except ST.HetKhoa as e:
            self.ghi(f"    ⚠ {VAI[v]['ten']} ({self.ten(v)}) không gọi được: {e} — bỏ qua bước này.")
            return None

    def giai(self, cau):
        """→ {chỉ số trong cau: (dap_an, ghi_chu)}; None nếu không giải được."""
        ra = {}
        for i0 in range(0, len(cau), LO):
            lo = cau[i0:i0 + LO]
            t = self._goi("giai", prompt_giai(lo))
            if t is None:
                return None
            for x in _json(t):
                try:
                    j = int(x.get("cau")) - 1
                except Exception:
                    continue
                if 0 <= j < len(lo):
                    ra[i0 + j] = (str(x.get("dap_an", "")).strip(), str(x.get("ghi_chu", "") or "").strip())
        return ra

    def phan_bien(self, cau, ngu_canh):
        ra = {}
        for i0 in range(0, len(cau), LO):
            lo = cau[i0:i0 + LO]
            t = self._goi("phan_bien", prompt_phan_bien(lo, ngu_canh))
            if t is None:
                return {}
            for x in _json(t):
                try:
                    j = int(x.get("cau")) - 1
                except Exception:
                    continue
                if 0 <= j < len(lo):
                    kl = str(x.get("ket_luan", "dat")).lower().strip()
                    ra[i0 + j] = (kl if kl in ("dat", "sua", "loai") else "dat", str(x.get("ly_do", "") or "").strip())
        return ra

    def duyet(self, khoi_ds, ngu_canh="", muc=""):
        """Nhận các khối \\begin{ex|bt}…; trả các khối đạt (đã sửa nếu cần, gắn nguồn Hội đồng AI)."""
        cau = []
        for k in khoi_ds:
            try:
                info = phan_tich_cau(k)
            except Exception:
                continue
            cau.append({"khoi": k, "loai": info.get("loai") or "TL", "dap_an": info.get("dap_an"), "muc": muc, "co": []})
        if not cau:
            return []
        self.thong_ke["vao"] += len(cau)
        # 1. Giải độc lập
        self.ghi(f"    🔎 {self.ten('giai')} giải độc lập {len(cau)} câu (đề đã xoá đáp án)…")
        g = self.giai(cau)
        lech = 0
        for i, c in enumerate(cau):
            if c["loai"] in ("TN", "DS") and not c["dap_an"]:
                c["co"].append("tác giả chưa đánh dấu \\True đúng quy cách")
            if g is None or i not in g:
                continue
            da, gc = g[i]
            c["giai"] = da
            kq = khop(c["loai"], c["dap_an"], da)
            if kq is False or da == "?":
                lech += 1
                c["co"].append(f"người giải ({self.ten('giai')}) ra «{da}» khác đáp án tác giả «{c['dap_an']}»" + (f" — {gc}" if gc else ""))
            elif gc and c["loai"] == "TL":
                c["co"].append(f"người giải lưu ý: {gc}")
        if g is not None:
            self.ghi(f"       → {len(cau) - lech}/{len(cau)} câu khớp đáp án" + (f", {lech} câu lệch" if lech else ""))
        # 2. Phản biện sư phạm
        self.ghi(f"    🧑‍🏫 {self.ten('phan_bien')} phản biện sư phạm…")
        pb = self.phan_bien(cau, ngu_canh)
        bo = set()
        for i, c in enumerate(cau):
            kl, ld = pb.get(i, ("dat", ""))
            if kl == "loai" and not c["co"]:
                c["co"].append(f"phản biện đề nghị LOẠI: {ld}")
            elif kl in ("sua", "loai"):
                c["co"].append(f"phản biện ({kl}): {ld}")
        n_co = sum(1 for c in cau if c["co"])
        if pb:
            self.ghi(f"       → {len(cau) - n_co} câu đạt ngay, {n_co} câu cần biên tập")
        # 3. Tổng biên tập sửa câu bị gắn cờ
        can = [dict(c, so=i + 1) for i, c in enumerate(cau) if c["co"]]
        if can:
            self.ghi(f"    ✍ {self.ten('bien_tap')} biên tập {len(can)} câu bị gắn cờ…")
            sua, loai = {}, {}
            for i0 in range(0, len(can), LO):
                t = self._goi("bien_tap", prompt_bien_tap(can[i0:i0 + LO]))
                if t is None:
                    break
                s, l = tach_bien_tap(t)
                sua.update(s); loai.update(l)
            da_sua = []
            for c in can:
                i = c["so"] - 1
                if c["so"] in loai:
                    bo.add(i); self.ghi(f"       ✗ loại câu {c['so']}: {loai[c['so']][:120]}")
                elif c["so"] in sua:
                    moi = sua[c["so"]]
                    dau_cu = cau[i]["khoi"].split("\n", 1)[0]
                    if "%[" not in moi.split("\n", 1)[0]:      # giữ dòng mã của bản gốc
                        moi = re.sub(r"^\\begin\{(?:ex|bt)\}[^\n]*", lambda _: dau_cu, moi, count=1)
                    thieu = [l for l in cau[i]["khoi"].split("\n")[1:] if l.lstrip().startswith("%") and l.strip() not in moi]
                    if thieu:                                  # giữ các dòng % nguon / % mau… của bản gốc
                        dau, _, than = moi.partition("\n")
                        moi = dau + "\n" + "\n".join(thieu) + "\n" + than
                    info = phan_tich_cau(moi)
                    cau[i].update(khoi=moi, loai=info.get("loai") or "TL", dap_an=info.get("dap_an"), da_sua=True)
                    da_sua.append(i)
                else:
                    bo.add(i); self.ghi(f"       ✗ loại câu {c['so']}: không nhận được bản sửa ({'; '.join(c['co'])[:100]})")
            # 4. Giải lại câu đã sửa (TN/DS/TLN)
            kiem = [i for i in da_sua if cau[i]["loai"] in ("TN", "DS", "TLN")]
            if kiem:
                self.ghi(f"    🔁 {self.ten('giai')} giải lại {len(kiem)} câu vừa sửa…")
                g2 = self.giai([cau[i] for i in kiem])
                for j, i in enumerate(kiem):
                    if g2 is None or j not in g2:
                        continue
                    if khop(cau[i]["loai"], cau[i]["dap_an"], g2[j][0]) is False or g2[j][0] == "?":
                        bo.add(i)
                        self.ghi(f"       ✗ loại câu {i + 1}: sửa xong vẫn lệch («{g2[j][0]}» ≠ «{cau[i]['dap_an']}»)")
        elif g is None and not pb:
            self.ghi("    ⚠ Không có vai kiểm tra nào chạy được — giữ nguyên câu của người soạn.")
        ra = []
        for i, c in enumerate(cau):
            if i in bo:
                self.thong_ke["loai"] += 1
                continue
            self.thong_ke["sua" if c.get("da_sua") else "dat"] += 1
            ra.append(gan_nguon(c["khoi"], self.vai))
        self.ghi(f"    ✓ Hội đồng thông qua {len(ra)}/{len(cau)} câu")
        return ra


def luu_vai(cau_hinh):
    """Lưu phân vai thầy chọn vào ai_khoa.json (mục "vai"); giá trị "tu_dong" / rỗng = để máy tự phân."""
    k = ST.doc_khoa()
    k["vai"] = {v: n for v, n in (cau_hinh or {}).items() if v in VAI and n in ("gemini", "deepseek", "claude", "openai")}
    json.dump(k, open(ST.KHOA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return k["vai"]
