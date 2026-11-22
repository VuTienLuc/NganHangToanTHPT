#!/usr/bin/env python3
"""🧬 KHUÔN CÂU — một câu mẫu thành vô số câu song sinh, có kiểm chứng.

AI đọc câu mẫu và viết MỘT LẦN một "khuôn" Python (bốc số · công thức đáp án · cách tính lại độc lập · viết LaTeX).
Python chạy khuôn trong hộp cách ly (khuon_chay.py), chỉ nhận biến thể khi công thức và cách tính lại cho cùng đáp án,
khuôn tái tạo đúng câu mẫu, phương án / đáp số đúng cấu trúc. Khuôn lỗi → gửi lỗi cụ thể cho AI sửa (tối đa 3 lần).
Khuôn đạt được lưu ở du-lieu/khuon/<mã câu mẫu>.py để lần sau sinh tiếp không tốn lượt AI.
"""
import os, re, json, sys, time, random, subprocess, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nh_core import GOC

THU_MUC = os.path.join(GOC, "du-lieu", "khuon")
CHAY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "khuon_chay.py")
MUC_SAU = {"N": "H", "H": "V", "V": "C", "C": "C"}
MOI_TRUONG = {"TN": "ex", "DS": "ex", "TLN": "bt", "TL": "bt"}


class LoiKhuon(Exception):
    pass


# ───────────── câu mẫu ─────────────
def mau_tu_kho(ma):
    from xem_truoc import kho
    from k12word import tach_cau
    c = kho().get(ma)
    if not c:
        raise LoiKhuon(f"Không thấy câu {ma} trong kho")
    try:
        p = tach_cau(c)
    except Exception:
        p = {}
    return {"ma": ma, "loai": c["loai"], "dang_key": c.get("dang_key") or "", "muc": c.get("muc_chuan") or "H",
            "ten_dang": c.get("ten_dang") or "", "ten_bai": c.get("ten_bai") or "", "lop": c.get("lop") or "",
            "noi_dung": c.get("noi_dung") or "", "dap_an": c.get("dap_an") or "", "pa": p.get("pa") or []}


# ───────────── prompt ─────────────
NGOAC = ('- Viết chuỗi bằng f-string (không dùng .format). Trong f-string, ngoặc nhọn LaTeX phải nhân đôi: f"\\dfrac{{1}}{{{a}}}" '
         '— nên dùng so(), da_thuc(), hang_tu() cho gọn và đúng dấu.')
THU_VIEN = r"""Thư viện có sẵn trong khuôn (KHÔNG cần import): Fraction, math, gcd, sqrt, isqrt và các hàm viết số LaTeX:
  so(x)            số → LaTeX: 3 · -3 · \dfrac{1}{2} · -\dfrac{3}{4} · 2{,}5   (Fraction tự rút gọn, float gần nguyên → nguyên)
  ngoac(x)         số âm có ngoặc khi thế vào biểu thức: ngoac(-3) = "(-3)"
  dau(x)           viết nối sau số hạng: dau(3) = "+3", dau(-3) = "-3"
  hang_tu(a, "x")  hệ số × biến: hang_tu(1,"x")="+x", hang_tu(-1,"x^2")="-x^2", hang_tu(0,"x")=""  (dau_cong=False cho số hạng đầu)
  da_thuc([a,b,c], "x")  đa thức bậc cao → thấp, tự bỏ hệ số 0/1 và xử lí dấu: da_thuc([1,-2,3]) = "x^2-2x+3"
  can(n)           căn rút gọn: can(12) = "2\sqrt{3}"
  lam_tron(x, n)   làm tròn kiểu Việt Nam;   tln(x, n=None) đáp số trả lời ngắn "2,5" (quá 4 ô → báo lỗi)"""

YEU_CAU_LOAI = {
    "TN": """- viet(p) trả {"de": đề, "pa": [ĐÚNG, nhiễu1, nhiễu2, nhiễu3], "gt": [giá trị số của 4 phương án] (bỏ nếu phương án không phải số),
   "loi": ["", lỗi sai sinh ra nhiễu1, lỗi sai sinh ra nhiễu2, lỗi sai sinh ra nhiễu3], "loigiai": lời giải}.
   pa[0] LUÔN là đáp án đúng (máy tự xáo). Mỗi phương án nhiễu phải sinh từ MỘT LỖI SAI THƯỜNG GẶP của học sinh (quên dấu,
   nhầm công thức, quên điều kiện, tính nhầm bước…), tính bằng code từ chính bộ số — không bịa số ngẫu nhiên.
   4 phương án phải khác nhau với MỌI bộ số (nếu trùng thì đổi nhiễu dự phòng hoặc return None ở tham_so).
- dap_an(p) và kiem(p) trả giá trị của phương án đúng.""",
    "DS": """- dap_an(p) trả list 4 giá trị True/False (mệnh đề a, b, c, d đúng hay sai) — TÍNH từ bộ số, không gán cứng.
- kiem(p) tính lại 4 giá trị đó bằng cách khác (thế số, vét cạn, tính trực tiếp).
- viet(p) trả {"de": đề (phần dẫn), "y": [mệnh đề a, b, c, d], "loigiai": lời giải từng ý}.
   Mệnh đề sai phải "sai một cách hợp lí" (số lệch do lỗi thường gặp), tỉ lệ Đúng/Sai nên thay đổi theo bộ số.""",
    "TLN": """- dap_an(p) và kiem(p) trả đáp số (số). viet(p) trả {"de", "dap": tln(đáp số[, n]), "loigiai"}.
   Đáp số ghi được trong 4 ô (kể cả dấu - và dấu phẩy): chọn bộ số cho đáp số gọn, hoặc yêu cầu làm tròn trong đề.""",
    "TL": """- dap_an(p) và kiem(p) trả kết quả cuối (số, Fraction, hoặc list số). viet(p) trả {"de", "loigiai"} với lời giải đủ bước.""",
}

VI_DU = r'''```python
# Ví dụ khuôn cho câu: "Cho parabol $y=x^2-2x+3$. Trục đối xứng là đường thẳng" (TN)
def tham_so(r, nang_cao=False):
    a = r.choice([1, 2, -1, -2]) if not nang_cao else r.choice([2, 3, -3, 4])
    b = r.randint(-8, 8); c = r.randint(-6, 6)
    if b == 0 or (not nang_cao and b % (2 * a) != 0):
        return None                      # bộ số xấu → máy bốc lại
    return dict(a=a, b=b, c=c)

def dap_an(p):
    return Fraction(-p["b"], 2 * p["a"])

def kiem(p):                             # cách khác: f(x)=f(0) có nghiệm x1=-b/a; trục là trung điểm của 0 và x1
    a, b, c = p["a"], p["b"], p["c"]
    f = lambda x: a * x * x + b * x + c
    x1 = Fraction(-b, a)
    assert f(x1) == f(0)
    return x1 / 2

def viet(p):
    a, b, c = p["a"], p["b"], p["c"]
    x0 = dap_an(p)
    gt = [x0, Fraction(b, 2 * a), Fraction(-b, a), Fraction(c)]
    if len(set(gt)) < 4:
        gt[3] = x0 + 1
    return {"de": f"Cho parabol $y={da_thuc([a, b, c])}$. Trục đối xứng của đồ thị là đường thẳng",
            "pa": [f"$x={so(g)}$" for g in gt], "gt": gt,
            "loi": ["", "quên dấu trừ trong $-\\dfrac{b}{2a}$", "quên chia 2", "lấy hệ số tự do"],
            "loigiai": f"Trục đối xứng $x=-\\dfrac{{b}}{{2a}}=-\\dfrac{{{b}}}{{2\\cdot {ngoac(a)}}}={so(x0)}$."}

MAU = dict(a=1, b=-2, c=3)
```'''


def prompt_khuon(m):
    return f"""Em là giáo viên Toán kiêm lập trình viên Python cẩn thận. Hãy viết KHUÔN CÂU (code Python) để sinh vô số câu SONG SINH
của câu mẫu dưới đây: cùng cấu trúc, cùng cách giải, cùng mức độ, chỉ đổi số liệu (và ngữ cảnh nhỏ nếu có).

## Câu mẫu ({m['loai']} · mức {m['muc']} · lớp {m['lop']} · {m['ten_bai']} — {m['ten_dang']})
```latex
{m['noi_dung'].strip()}
```
Đáp án trong kho: {m['dap_an'] or '(tự luận)'}

## Khuôn gồm đúng các phần sau
- tham_so(r, nang_cao=False): bốc bộ số bằng r (random.Random) → dict; return None nếu bộ số xấu (nghiệm xấu, chia 0, trùng
  trường hợp đặc biệt, đáp số không đẹp). Miền số vừa sức lớp {m['lop']}, đáp số đẹp như câu mẫu. nang_cao=True: số lớn hơn /
  thêm một chút biến đổi nhưng VẪN cùng dạng.
- dap_an(p): đáp án đúng theo công thức. Dùng Fraction cho phân số — KHÔNG dùng float khi có thể tính chính xác.
- kiem(p): tính lại đáp án bằng CÁCH KHÁC HẲN (vét cạn, thế ngược nghiệm vào phương trình, tính trực tiếp từ định nghĩa,
  tính số gần đúng…) — máy so dap_an(p) với kiem(p), lệch là loại. Không được gọi dap_an() trong kiem().
- viet(p): đề + lời giải LaTeX (cùng văn phong câu mẫu, công thức trong $...$), xem yêu cầu riêng bên dưới.
- MAU = dict(...): bộ số của CHÍNH câu mẫu — máy dùng để kiểm khuôn tái tạo đúng câu mẫu.
{YEU_CAU_LOAI.get(m['loai'], YEU_CAU_LOAI['TL'])}

## Quy định code (hộp cách ly sẽ từ chối nếu vi phạm)
- Chỉ import: math, fractions, random, itertools, functools, decimal, statistics. Không file, không mạng, không class/global.
{NGOAC}
- Không dùng tên / chuỗi có "__".
{THU_VIEN}

## Ví dụ một khuôn đạt yêu cầu
{VI_DU}

Chỉ trả về MỘT khối ```python chứa toàn bộ khuôn, không giải thích thêm."""


def prompt_sua(m, code, loi):
    return f"""Khuôn câu Python dưới đây (cho câu mẫu {m['loai']}) chưa đạt khi máy chạy kiểm tra:

LỖI: {loi}

```python
{code}
```

Câu mẫu:
```latex
{m['noi_dung'].strip()}
```
Đáp án trong kho: {m['dap_an'] or '(tự luận)'}
{YEU_CAU_LOAI.get(m['loai'], YEU_CAU_LOAI['TL'])}
Nhắc lại: tham_so(r, nang_cao=False) · dap_an(p) · kiem(p) (cách tính KHÁC) · viet(p) · MAU (bộ số câu mẫu); chỉ import math, fractions,
random, itertools, functools, decimal, statistics; f-string, không .format, không "__".
{THU_VIEN}

Sửa đúng lỗi trên (kiểm lại cả công thức lẫn cách tính lại), trả về MỘT khối ```python chứa toàn bộ khuôn đã sửa."""


def tach_code(t):
    ds = re.findall(r"```(?:python|py)?\s*\n(.*?)```", t or "", re.S)
    if ds:
        return max(ds, key=len).strip()
    return (t or "").strip() if "def tham_so" in (t or "") else ""


# ───────────── chạy khuôn ─────────────
def chay_khuon(code, loai, so=5, seed=None, nang_cao=False, toi_da_thu=None):
    vao = {"code": code, "loai": loai, "so": so, "seed": seed if seed is not None else random.randrange(1 << 30),
           "nang_cao": nang_cao, "toi_da_thu": toi_da_thu}
    env = {k: os.environ[k] for k in ("PATH", "SYSTEMROOT", "LANG") if k in os.environ}
    env["PYTHONIOENCODING"] = "utf-8"
    with tempfile.TemporaryDirectory() as tam:
        try:
            r = subprocess.run([sys.executable, "-I", CHAY], input=json.dumps(vao), capture_output=True, text=True,
                               encoding="utf-8", timeout=45, cwd=tam, env=env)
        except subprocess.TimeoutExpired:
            return {"ok": False, "loi": "Khuôn chạy quá 45 giây (vòng lặp vô hạn hoặc vét cạn quá lớn)"}
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"ok": False, "loi": "Khuôn làm hỏng tiến trình chạy: " + (r.stderr or r.stdout or "")[-300:]}


def _chuan(s):
    s = str(s or "")
    for a, b in ((r"\dfrac", r"\frac"), (r"\tfrac", r"\frac"), (r"\left", ""), (r"\right", ""), ("{,}", ","), (r"\,", ""), ("$", "")):
        s = s.replace(a, b)
    return re.sub(r"[\s.]+", "", s)


def doi_chieu_mau(m, kq):
    """Khuôn có tái tạo đúng đáp án câu mẫu không? → chuỗi lỗi hoặc ''."""
    mau = kq.get("mau") or {}
    if m["loai"] == "TN" and m["pa"] and m["dap_an"] in "ABCD" and m["dap_an"]:
        goc = m["pa"]["ABCD".index(m["dap_an"])]
        if _chuan(goc) != _chuan(mau.get("pa0")):
            return (f"Với MAU, phương án đúng khuôn viết là «{mau.get('pa0')}» nhưng câu mẫu có đáp án đúng «{goc.strip()}». "
                    "Kiểm tra lại MAU, công thức đáp án hoặc cách viết phương án.")
    if m["loai"] == "DS" and len(m["dap_an"]) == 4:
        goc = [x == "Đ" for x in m["dap_an"]]
        if mau.get("dap_an") != goc:
            return f"Với MAU, dap_an = {mau.get('dap_an')} nhưng câu mẫu có Đúng/Sai là {m['dap_an']} ({goc})."
    if m["loai"] == "TLN" and m["dap_an"]:
        if _chuan(mau.get("dap")) != _chuan(m["dap_an"]):
            return f"Với MAU, đáp số khuôn ghi «{mau.get('dap')}» nhưng câu mẫu có đáp số «{m['dap_an']}»."
    return ""


def duong_dan(ma):
    return os.path.join(THU_MUC, f"{ma}.py")


def doc_khuon(ma):
    if not re.fullmatch(r"[0-9a-f]{8}", ma or ""):
        return None
    p = duong_dan(ma)
    return open(p, encoding="utf-8").read() if os.path.exists(p) else None


def luu_khuon(m, code, nguon):
    os.makedirs(THU_MUC, exist_ok=True)
    dau = (f"# Khuôn câu cho mẫu {m['ma']} ({m['loai']} · {m['dang_key']} · {m['ten_dang']})\n"
           f"# {nguon} · {time.strftime('%d/%m/%Y')} — thầy sửa tay được; xoá file để AI viết lại.\n")
    open(duong_dan(m["ma"]), "w", encoding="utf-8").write(dau + code.strip() + "\n")


def tao_khuon(m, xoay, ghi=print, lan=3):
    """AI viết khuôn → máy chạy thử → lỗi thì gửi lại AI sửa. → code đạt (đã lưu) hoặc LoiKhuon."""
    code, loi = "", ""
    for i in range(1, lan + 1):
        p = prompt_khuon(m) if not code else prompt_sua(m, code, loi)
        t, _, k = xoay.goi(p)
        moi = tach_code(t)
        if not moi:
            loi = "Không thấy khối ```python trong câu trả lời"
            ghi(f"      lần {i}: {loi}")
            continue
        code = moi
        kq = chay_khuon(code, m["loai"], so=8, seed=1000 + i)
        loi = (kq.get("loi") or "") if not kq.get("ok") else doi_chieu_mau(m, kq)
        if kq.get("ok") and not loi and len(kq.get("bien_the") or []) < 3:
            loi = f"Khuôn chỉ sinh được {len(kq.get('bien_the') or [])} biến thể khác nhau trong {kq['thong_ke']['thu']} lần bốc — mở rộng miền số."
        if not loi:
            from sinh_tuong_tu import TEN_NHA
            luu_khuon(m, code, f"AI {TEN_NHA.get(k.get('nha'), k.get('nha'))} viết khuôn, đạt kiểm tra lần {i}")
            ghi(f"      ✓ khuôn đạt kiểm tra (lần {i}) — đã lưu du-lieu/khuon/{m['ma']}.py")
            return code
        ghi(f"      lần {i}: {loi[:220]}")
    raise LoiKhuon(f"AI chưa viết được khuôn đạt kiểm tra sau {lan} lần: {loi[:200]}")


# ───────────── biến thể → khối LaTeX ─────────────
def _thut(s, n=1):
    return "\n".join("\t" * n + x.strip() for x in str(s).strip().split("\n") if x.strip())


def khoi_latex(m, b, nang_cao, rng):
    loai = m["loai"]
    env = MOI_TRUONG.get(loai, "bt")
    muc = MUC_SAU.get(m["muc"], "V") if nang_cao else m["muc"]
    ma_dang = (m["dang_key"] or "").replace("?", muc)
    dong = [f"\\begin{{{env}}}%[{ma_dang}]",
            f"% nguon: Khuôn câu (AI viết khuôn · Python sinh & kiểm) từ mẫu {m['ma']}",
            f"% mau: {m['ma']}{' nang_cao' if nang_cao else ''}",
            f"% khuon: {m['ma']}"]
    if loai == "TN":
        thu_tu = [0, 1, 2, 3]
        rng.shuffle(thu_tu)
        loi = list(b.get("loi") or []) + [""] * 4
        nhieu = [f"{'ABCD'[j]}={loi[i]}" for j, i in enumerate(thu_tu) if i != 0 and str(loi[i]).strip()]
        if nhieu:
            dong.append("% nhieu: " + "; ".join(nhieu).replace("\n", " "))
        dong += [_thut(b["de"]), "\t\\choice"]
        for i in thu_tu:
            dong.append("\t\t{" + ("\\True " if i == 0 else "") + str(b["pa"][i]).strip() + "}")
    elif loai == "DS":
        dong += [_thut(b["de"]), "\t\\choiceTF"]
        for y, d in zip(b["y"], b["dung"]):
            dong.append("\t\t{" + ("\\True " if d else "") + str(y).strip() + "}")
    elif loai == "TLN":
        dong += [_thut(b["de"]), "\t\\shortans{" + str(b["dap"]).strip() + "}"]
    else:
        dong.append(_thut(b["de"]))
    dong += ["\t\\loigiai{", _thut(b["loigiai"], 2), "\t}", f"\\end{{{env}}}"]
    return "\n".join(dong)


def chon_nha_khuon():
    import hoi_dong_ai as HD
    vai = HD.phan_vai()
    return vai.get("khuon")


def sinh(ds_ma, so=3, so_nc=0, ghi=print, xoay=None, viet_lai=False, seed=None):
    """Mỗi câu mẫu: dùng khuôn đã lưu (hoặc nhờ AI viết) → so câu giống + so_nc câu nâng cao, đã kiểm chứng.
    → (khối LaTeX, {dạng: mã mẫu}, thống kê)."""
    rng = random.Random(seed if seed is not None else time.time())
    khoi, vdm, tk = [], {}, {"mau": 0, "khuon_moi": 0, "khuon_cu": 0, "cau": 0, "bo": []}
    for i, ma in enumerate(ds_ma, 1):
        try:
            m = mau_tu_kho(ma)
        except LoiKhuon as e:
            ghi(f"  [{i}/{len(ds_ma)}] {e}"); tk["bo"].append(ma); continue
        ghi(f"  [{i}/{len(ds_ma)}] mẫu {ma} ({m['loai']} · {m['dang_key']} · {m['ten_dang'][:50]})")
        code = None if viet_lai else doc_khuon(ma)
        if code:
            tk["khuon_cu"] += 1
            ghi("      dùng khuôn đã lưu (không tốn lượt AI)")
        else:
            if xoay is None:
                import hoi_dong_ai as HD
                nha = chon_nha_khuon()
                if not nha:
                    raise LoiKhuon("Chưa có khoá API AI — bấm ⚙ Khoá AI… (cần AI viết khuôn lần đầu).")
                xoay = HD.xoay_cho("khuon", nha, ghi=ghi)
                ghi(f"      🧬 {HD.ST.TEN_NHA.get(nha, nha)} viết khuôn…")
            try:
                code = tao_khuon(m, xoay, ghi)
                tk["khuon_moi"] += 1
            except LoiKhuon as e:
                ghi(f"      ✗ {e}"); tk["bo"].append(ma); continue
        tk["mau"] += 1
        for nc, can in ((False, so), (True, so_nc)):
            if can <= 0:
                continue
            kq = chay_khuon(code, m["loai"], so=can, seed=rng.randrange(1 << 30), nang_cao=nc)
            if not kq.get("ok"):
                ghi(f"      ⚠ {'nâng cao' if nc else 'giống mẫu'}: {kq.get('loi', '')[:200]}")
                continue
            for b in kq["bien_the"]:
                khoi.append(khoi_latex(m, b, nc, rng))
            tk["cau"] += len(kq["bien_the"])
            th = kq["thong_ke"]
            ghi(f"      +{len(kq['bien_the'])} câu {'nâng cao' if nc else 'giống mẫu'} · đã kiểm {th['thu']} bộ số "
                f"(loại {th['bo_so_xau']} xấu, {th['trung']} trùng, {th['lech']} lệch đáp án)")
        if m["dang_key"]:
            vdm[m["dang_key"]] = ma
    return khoi, vdm, tk
