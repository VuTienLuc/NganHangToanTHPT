#!/usr/bin/env python3
"""CHẠY KHUÔN CÂU TRONG HỘP CÁCH LY (tiến trình con, không đụng file / mạng).

Khuôn câu là đoạn Python do AI viết từ một câu mẫu:
    tham_so(r, nang_cao=False) -> dict | None   bốc bộ số (None = bộ số xấu, máy bốc lại)
    dap_an(p)                                    đáp án đúng theo công thức
    kiem(p)                                      tính lại đáp án bằng CÁCH KHÁC (vét cạn / thế ngược / tính số)
    viet(p) -> dict                              đề + phương án / mệnh đề / đáp số + lời giải (LaTeX)
    MAU = {...}                                  bộ số của chính câu mẫu
Máy chỉ nhận biến thể khi dap_an(p) == kiem(p) và cấu trúc hợp lệ.

Vào (stdin, JSON): {"code", "loai": TN|DS|TLN|TL, "so", "seed", "nang_cao": bool, "toi_da_thu"}
Ra (stdout, JSON): {"ok", "loi", "mau": {...}, "bien_the": [...], "thong_ke": {...}}
"""
import ast, json, sys, math, random, fractions, itertools, functools
from fractions import Fraction

MO_DUOC = {"math", "fractions", "random", "itertools", "functools", "decimal", "cmath", "statistics"}
# thuộc tính mở đường thoát hộp cách ly (khung lệnh, traceback, format chuỗi kiểu "{0.__class__}")
CAM_THUOC_TINH = {"gi_frame", "gi_code", "gi_yieldfrom", "f_back", "f_globals", "f_locals", "f_builtins", "f_code",
                  "tb_frame", "tb_next", "cr_frame", "cr_code", "ag_frame", "ag_code", "format", "format_map", "mro"}
CAM_TEN = {"open", "exec", "eval", "compile", "__import__", "globals", "locals", "getattr", "setattr", "delattr",
           "input", "breakpoint", "vars", "dir", "help", "exit", "quit", "memoryview", "type", "object", "super",
           "classmethod", "staticmethod", "property", "os", "sys", "subprocess", "shutil", "socket", "pathlib", "importlib",
           "builtins", "__builtins__", "__loader__", "__spec__"}
BUILTIN_CHO = ["abs", "all", "any", "bool", "dict", "divmod", "enumerate", "filter", "float", "int", "isinstance", "len",
               "list", "map", "max", "min", "pow", "range", "reversed", "round", "set", "sorted", "str", "sum", "tuple",
               "zip", "frozenset", "ValueError", "ZeroDivisionError", "ArithmeticError", "Exception", "StopIteration",
               "AssertionError", "TypeError", "IndexError", "KeyError", "OverflowError", "chr", "ord", "repr", "hash"]


class KhuonXau(Exception):
    pass


# ───────────── kiểm mã nguồn trước khi chạy ─────────────
def kiem_ma(code):
    try:
        cay = ast.parse(code)
    except SyntaxError as e:
        raise KhuonXau(f"Lỗi cú pháp Python dòng {e.lineno}: {e.msg}")
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name.split(".")[0] not in MO_DUOC:
                    raise KhuonXau(f"Không được import «{a.name}» (chỉ: {', '.join(sorted(MO_DUOC))})")
        elif isinstance(n, ast.ImportFrom):
            if (n.module or "").split(".")[0] not in MO_DUOC or n.level:
                raise KhuonXau(f"Không được import từ «{n.module}»")
        elif isinstance(n, ast.Name) and (n.id in CAM_TEN or n.id.startswith("__")):
            raise KhuonXau(f"Không được dùng «{n.id}»")
        elif isinstance(n, ast.Attribute) and (n.attr.startswith("_") or n.attr in CAM_THUOC_TINH):
            raise KhuonXau(f"Không được dùng thuộc tính «{n.attr}»" + (" — viết chuỗi bằng f-string" if n.attr.startswith("format") else ""))
        elif isinstance(n, (ast.Global, ast.Nonlocal, ast.AsyncFunctionDef, ast.Await, ast.ClassDef)):
            raise KhuonXau("Khuôn không được dùng global / nonlocal / class / async")
        elif isinstance(n, ast.Constant) and isinstance(n.value, str) and "__" in n.value:
            raise KhuonXau("Chuỗi trong khuôn không được chứa «__»")
    ten = {n.name for n in cay.body if isinstance(n, ast.FunctionDef)}
    thieu = {"tham_so", "dap_an", "kiem", "viet"} - ten
    if thieu:
        raise KhuonXau("Khuôn thiếu hàm: " + ", ".join(sorted(thieu)))


def _nhap_an_toan(ten, *a, **k):
    if ten.split(".")[0] not in MO_DUOC:
        raise ImportError(f"Không được import {ten}")
    return __import__(ten, *a, **k)


# ───────────── thư viện viết số LaTeX cho khuôn ─────────────
def _la_so(x):
    return isinstance(x, (int, Fraction, float)) and not isinstance(x, bool)


def _gon(x):
    """float gần nguyên / gần phân số đẹp → int / Fraction."""
    if isinstance(x, float):
        if abs(x - round(x)) < 1e-9:
            return int(round(x))
        f = Fraction(x).limit_denominator(1000)
        if abs(float(f) - x) < 1e-12:
            return f
    if isinstance(x, Fraction) and x.denominator == 1:
        return int(x)
    return x


def so(x, phan_so=True):
    """Số → LaTeX: 3 · -3 · \\dfrac{1}{2} · -\\dfrac{3}{4} · 2{,}5 (dấu phẩy thập phân)."""
    if not _la_so(x):
        return str(x)
    x = _gon(x)
    if isinstance(x, int):
        return str(x)
    if isinstance(x, Fraction):
        if not phan_so:
            return so(float(x))
        return ("-" if x < 0 else "") + r"\dfrac{%d}{%d}" % (abs(x.numerator), x.denominator)
    t = ("%.6f" % x).rstrip("0").rstrip(".")
    return t.replace(".", "{,}")


def ngoac(x):
    """Số âm có ngoặc: (-3) — dùng khi thế số vào biểu thức."""
    t = so(x)
    return "(" + t + ")" if t.startswith("-") else t


def dau(x):
    """+3 / -3 / +\\dfrac{1}{2} — viết nối sau một số hạng."""
    t = so(x)
    return t if t.startswith("-") else "+" + t


def hang_tu(a, bien="x", dau_cong=True):
    """Hệ số a nhân biến: hang_tu(1,'x')='+x', hang_tu(-1,'x')='-x', hang_tu(3,'x^2')='+3x^2', hang_tu(0,…)=''."""
    a = _gon(a)
    if a == 0:
        return ""
    if bien:
        t = "" if a == 1 else "-" if a == -1 else so(a)
    else:
        t = so(a)
    t = t + bien
    if dau_cong and not t.startswith("-"):
        t = "+" + t
    return t


def da_thuc(he_so, bien="x"):
    """[a, b, c] (bậc cao → thấp) → 'ax^2+bx+c' đã rút gọn dấu, bỏ hệ số 0 / 1."""
    n = len(he_so) - 1
    phan = []
    for i, a in enumerate(he_so):
        mu = n - i
        b = "" if mu == 0 else bien if mu == 1 else f"{bien}^{{{mu}}}" if mu > 9 else f"{bien}^{mu}"
        t = hang_tu(a, b, dau_cong=bool(phan))
        if t:
            phan.append(t)
    return "".join(phan) or "0"


def can(n):
    """Căn bậc hai số nguyên dương, rút gọn: can(12)='2\\sqrt{3}', can(9)='3'."""
    n = int(n)
    if n < 0:
        raise ValueError("can(): số âm")
    k, m = 1, n
    for d in range(int(math.isqrt(n)), 1, -1):
        if n % (d * d) == 0:
            k, m = d, n // (d * d)
            break
    if m == 1:
        return str(k)
    return ("" if k == 1 else str(k)) + r"\sqrt{%d}" % m


def lam_tron(x, n=0):
    """Làm tròn kiểu Việt Nam (0,5 → lên)."""
    q = Fraction(str(float(x))) if isinstance(x, float) else Fraction(x)
    k = Fraction(10) ** n
    v = q * k
    r = math.floor(abs(v) + Fraction(1, 2)) * (1 if v >= 0 else -1)
    return _gon(Fraction(r) / k) if n > 0 else int(r)


def tln(x, n=None):
    """Đáp số trả lời ngắn (ghi phiếu 4 ô): làm tròn n chữ số thập phân nếu cần, dấu phẩy; quá 4 ký tự → lỗi."""
    if n is not None:
        x = lam_tron(x, n)
    x = _gon(x)
    if isinstance(x, Fraction):
        x = float(x)
    t = str(x) if isinstance(x, int) else ("%.6f" % x).rstrip("0").rstrip(".")
    t = t.replace(".", ",")
    if len(t) > 4:
        raise ValueError(f"đáp số «{t}» dài hơn 4 ô — cần làm tròn (tln(x, n)) hoặc đổi bộ số")
    return t


TV = {"Fraction": Fraction, "math": math, "random": random, "itertools": itertools, "functools": functools,
      "so": so, "ngoac": ngoac, "dau": dau, "hang_tu": hang_tu, "da_thuc": da_thuc, "can": can,
      "lam_tron": lam_tron, "tln": tln, "gcd": math.gcd, "sqrt": math.sqrt, "isqrt": math.isqrt}


# ───────────── so khớp ─────────────
def bang(a, b):
    if isinstance(a, (list, tuple)) or isinstance(b, (list, tuple)):
        return isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)) and len(a) == len(b) and all(bang(x, y) for x, y in zip(a, b))
    if isinstance(a, bool) or isinstance(b, bool):
        return bool(a) == bool(b) and type(a) == type(b)
    if _la_so(a) and _la_so(b):
        if isinstance(a, (int, Fraction)) and isinstance(b, (int, Fraction)):
            return Fraction(a) == Fraction(b)
        return abs(float(a) - float(b)) <= 1e-9 * max(1.0, abs(float(a)))
    return str(a).replace(" ", "") == str(b).replace(" ", "")


def json_hoa(x):
    if isinstance(x, (list, tuple)):
        return [json_hoa(y) for y in x]
    if isinstance(x, bool) or x is None:
        return x
    if isinstance(x, Fraction):
        return str(_gon(x))
    if isinstance(x, (int, float, str)):
        return x
    return str(x)


def kiem_viet(loai, v, d):
    """Kiểm cấu trúc kết quả viet(p). d = dap_an(p)."""
    if not isinstance(v, dict) or not str(v.get("de") or "").strip():
        raise KhuonXau("viet(p) phải trả dict có khoá 'de'")
    if not str(v.get("loigiai") or "").strip():
        raise KhuonXau("viet(p) thiếu 'loigiai'")
    if loai == "TN":
        pa = v.get("pa")
        if not isinstance(pa, (list, tuple)) or len(pa) != 4 or not all(str(x).strip() for x in pa):
            raise KhuonXau("TN: viet(p)['pa'] phải là 4 phương án (pa[0] là đáp án đúng)")
        if len({str(x).replace(" ", "") for x in pa}) < 4:
            raise KhuonXau("TN: có phương án trùng nhau")
        gt = v.get("gt")
        if gt is not None:
            if len(gt) != 4:
                raise KhuonXau("TN: 'gt' phải có 4 giá trị")
            if not bang(gt[0], d):
                raise KhuonXau(f"TN: giá trị phương án đúng {json_hoa(gt[0])} ≠ dap_an {json_hoa(d)}")
            for g in gt[1:]:
                if bang(g, d):
                    raise KhuonXau(f"TN: phương án nhiễu {json_hoa(g)} trùng đáp án đúng")
            if len({str(json_hoa(_gon(g))) for g in gt}) < 4:
                raise KhuonXau("TN: hai phương án có cùng giá trị")
    elif loai == "DS":
        y = v.get("y")
        if not isinstance(y, (list, tuple)) or len(y) != 4:
            raise KhuonXau("DS: viet(p)['y'] phải là 4 mệnh đề a, b, c, d")
        if not (isinstance(d, (list, tuple)) and len(d) == 4 and all(isinstance(x, bool) for x in d)):
            raise KhuonXau("DS: dap_an(p) phải trả 4 giá trị True/False")
    elif loai == "TLN":
        t = str(v.get("dap") or "").strip()
        if not t or len(t) > 4:
            raise KhuonXau(f"TLN: đáp số «{t}» rỗng hoặc dài hơn 4 ô")
        if _la_so(d):
            try:
                x = float(t.replace(",", "."))
            except ValueError:
                raise KhuonXau(f"TLN: đáp số «{t}» không phải số")
            if abs(x - float(d)) > 0.5 * 10 ** -(len(t.split(",")[1]) if "," in t else 0) + 1e-9:
                raise KhuonXau(f"TLN: đáp số ghi «{t}» không khớp dap_an {json_hoa(d)} (kể cả làm tròn)")


def chay(vao):
    loai = vao.get("loai") or "TL"
    code = vao["code"]
    kiem_ma(code)
    bi = {k: getattr(__builtins__, k) if not isinstance(__builtins__, dict) else __builtins__[k] for k in BUILTIN_CHO}
    bi["__import__"] = _nhap_an_toan
    g = {"__builtins__": bi, "__name__": "khuon", **TV}
    exec(compile(code, "<khuon>", "exec"), g)
    tham_so, dap_an, kiem, viet = g["tham_so"], g["dap_an"], g["kiem"], g["viet"]
    ra = {"ok": True, "loi": "", "mau": None, "bien_the": [], "thong_ke": {"thu": 0, "bo_so_xau": 0, "lech": 0, "trung": 0, "loi_viet": 0}}
    # 1) câu mẫu
    if isinstance(g.get("MAU"), dict):
        p = g["MAU"]
        d, k = dap_an(p), kiem(p)
        v = viet(p)
        ra["mau"] = {"dap_an": json_hoa(d), "kiem": json_hoa(k), "khop": bang(d, k), "de": v.get("de"),
                     "pa0": (v.get("pa") or [None])[0] if loai == "TN" else None, "dap": v.get("dap")}
        if not bang(d, k):
            raise KhuonXau(f"Với bộ số của câu mẫu MAU: dap_an = {json_hoa(d)} nhưng kiem = {json_hoa(k)}")
    else:
        raise KhuonXau("Khuôn thiếu MAU = {...} (bộ số của câu mẫu)")
    # 2) bốc biến thể
    r = random.Random(vao.get("seed"))
    so_can = int(vao.get("so") or 5)
    toi_da = int(vao.get("toi_da_thu") or max(60, so_can * 40))
    da_de = {str(ra["mau"]["de"]).replace(" ", "")}
    vi_du_loi = []
    while len(ra["bien_the"]) < so_can and ra["thong_ke"]["thu"] < toi_da:
        ra["thong_ke"]["thu"] += 1
        p = tham_so(r, nang_cao=bool(vao.get("nang_cao")))
        if p is None:
            ra["thong_ke"]["bo_so_xau"] += 1
            continue
        try:
            d, k = dap_an(p), kiem(p)
        except (ZeroDivisionError, ValueError, ArithmeticError):
            ra["thong_ke"]["bo_so_xau"] += 1
            continue
        if not bang(d, k):
            ra["thong_ke"]["lech"] += 1
            if len(vi_du_loi) < 3:
                vi_du_loi.append(f"bộ số {json_hoa({a: b for a, b in p.items()})}: dap_an = {json_hoa(d)}, kiem = {json_hoa(k)}")
            continue
        try:
            v = viet(p)
            kiem_viet(loai, v, d)
        except (ValueError, ZeroDivisionError) as e:
            ra["thong_ke"]["loi_viet"] += 1
            if len(vi_du_loi) < 3:
                vi_du_loi.append(f"viet() lỗi với bộ số {json_hoa(dict(p))}: {e}")
            continue
        key = str(v["de"]).replace(" ", "")
        if key in da_de:
            ra["thong_ke"]["trung"] += 1
            continue
        da_de.add(key)
        ra["bien_the"].append({"de": v["de"], "loigiai": v["loigiai"], "pa": v.get("pa"), "loi": v.get("loi"),
                               "y": v.get("y"), "dung": json_hoa(d) if loai == "DS" else None, "dap": v.get("dap"),
                               "dap_an": json_hoa(d), "tham_so": json_hoa(dict(p))})
    tk = ra["thong_ke"]
    if tk["lech"]:
        raise KhuonXau(f"dap_an và kiem LỆCH nhau ở {tk['lech']}/{tk['thu']} bộ số — công thức sai với một số trường hợp. Ví dụ: "
                       + " | ".join(vi_du_loi))
    if not ra["bien_the"]:
        raise KhuonXau(f"Không sinh được biến thể nào sau {tk['thu']} lần bốc (bộ số xấu {tk['bo_so_xau']}, trùng {tk['trung']}, viet lỗi {tk['loi_viet']})"
                       + (". " + " | ".join(vi_du_loi) if vi_du_loi else ""))
    if vi_du_loi:
        ra["canh_bao"] = vi_du_loi
    return ra


def main():
    try:
        import resource                                   # Mac/Linux: giới hạn CPU, bộ nhớ
        resource.setrlimit(resource.RLIMIT_CPU, (20, 25))
        try:
            resource.setrlimit(resource.RLIMIT_AS, (1 << 31, 1 << 31))
        except (ValueError, OSError):
            pass
    except ImportError:
        pass
    vao = json.loads(sys.stdin.read())
    try:
        ra = chay(vao)
    except KhuonXau as e:
        ra = {"ok": False, "loi": str(e)}
    except Exception as e:
        import traceback
        tb = traceback.extract_tb(e.__traceback__)
        dong = next((f"dòng {f.lineno} ({f.name}): {f.line}" for f in reversed(tb) if f.filename == "<khuon>"), "")
        ra = {"ok": False, "loi": f"{type(e).__name__}: {e}" + (f" — {dong}" if dong else "")}
    sys.stdout.write(json.dumps(ra, ensure_ascii=False))


if __name__ == "__main__":
    main()
