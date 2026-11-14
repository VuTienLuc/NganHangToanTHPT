# -*- coding: utf-8 -*-
"""XEM TRƯỚC BỘ CÂU ĐƯỢC CHỌN (ra đề theo ma trận): hiển thị câu, đổi ngẫu nhiên từng câu, xác nhận."""
import os, re, json, html, random
from nh_core import GOC
from k12word import tach_cau

_KHO = None


def kho():
    global _KHO
    p = os.path.join(GOC, "du-lieu", "chi_muc.jsonl")
    mt = os.path.getmtime(p)
    if not _KHO or _KHO[0] != mt:
        _KHO = (mt, {c["ma"]: c for c in map(json.loads, open(p, encoding="utf-8")) if c.get("ma")})
    return _KHO[1]


def lich_su():
    p = os.path.join(GOC, "du-lieu", "lich_su_dung.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


def hop_le(c):
    da = c.get("dap_an") or ""
    return {"TN": len(da) == 1, "DS": len(da) == 4, "TLN": bool(da)}.get(c["loai"], True)


def _cat_moi_truong(t, env, thay):
    while True:
        a = t.find("\\begin{" + env + "}")
        if a < 0:
            return t
        b = t.find("\\end{" + env + "}", a)
        if b < 0:
            return t
        t = t[:a] + thay + t[b + len(env) + 6:]


def sang_html(t):
    """LaTeX câu hỏi → HTML gọn để xem trước (công thức $…$ để MathJax vẽ)."""
    t = re.sub(r"(?<!\\)%[^\n]*", "", t or "")
    for env, thay in (("tikzpicture", " ⟦hình vẽ⟧ "), ("tabular", " ⟦bảng⟧ "), ("tkzTab", " ⟦bảng biến thiên⟧ "),
                      ("tikzcd", " ⟦sơ đồ⟧ ")):
        t = _cat_moi_truong(t, env, thay)
    t = re.sub(r"\\immini(?:\[[^\]]*\])?", "", t)
    t = html.escape(t, quote=False)
    t = re.sub(r"\\begin\{(enumerate|itemize|enumEX|listEX|itemchoice)\}(\[[^\]]*\])?(\{\d+\})?", "<br>", t)
    t = re.sub(r"\\end\{(enumerate|itemize|enumEX|listEX|itemchoice)\}", "<br>", t)
    t = re.sub(r"\\item(ch)?\b", "<br>• ", t)
    for lenh, the in (("textbf", "b"), ("textit", "i"), ("emph", "i"), ("underline", "u")):
        t = re.sub(r"\\" + lenh + r"\{([^{}]*)\}", rf"<{the}>\1</{the}>", t)
    t = re.sub(r"\\\\(\[[^\]]*\])?", "<br>", t)
    t = t.replace("\\centering", "").replace("\\noindent", "")
    t = re.sub(r"\n{2,}", "<br>", t)
    return t.strip()


def the_cau(ma, ls=None):
    c = kho().get(ma)
    if not c:
        return {"ma": ma, "mat": True}
    ls = ls if ls is not None else lich_su()
    try:
        p = tach_cau(c)
    except Exception:
        p = {"de": c.get("noi_dung") or "", "pa": None}
    return {"ma": ma, "loai": c["loai"], "muc": c.get("muc_chuan") or "", "dang_key": c.get("dang_key") or "",
            "ten_dang": c.get("ten_dang") or "", "ten_bai": c.get("ten_bai") or "",
            "de": sang_html(p.get("de")), "pa": [sang_html(x) for x in (p.get("pa") or [])],
            "dap_an": c.get("dap_an") or "", "da_dung": len(ls.get(ma, [])), "co_hinh": bool(c.get("co_hinh"))}


def bo_cau(bo):
    """bo: [{loai: [mã…]}…] → cùng cấu trúc nhưng là thẻ câu."""
    ls = lich_su()
    return [{l: [the_cau(m, ls) for m in ds] for l, ds in b.items()} for b in bo]


def doi(ma, tranh, rng=None):
    """Câu thay thế cho `ma`: cùng loại + cùng dạng + cùng mức → cùng dạng → cùng bài. Ưu tiên câu chưa dùng."""
    rng = rng or random.Random()
    K = kho(); c = K.get(ma)
    if not c:
        return None
    tranh = set(tranh or []) | {ma}
    ls = lich_su()
    cung = [x for x in K.values() if x["loai"] == c["loai"] and x["ma"] not in tranh and hop_le(x)]
    bai = (c.get("dang_key") or "").split("-")[0]
    for loc, ghi in ((lambda x: x.get("dang_key") == c.get("dang_key") and x.get("muc_chuan") == c.get("muc_chuan"), ""),
                     (lambda x: x.get("dang_key") == c.get("dang_key"), "khác mức"),
                     (lambda x: bai and (x.get("dang_key") or "").startswith(bai + "-") and x.get("muc_chuan") == c.get("muc_chuan"),
                      "dạng khác cùng bài")):
        ung = [x for x in cung if loc(x)]
        if ung:
            moi = [x for x in ung if not ls.get(x["ma"])]
            x = rng.choice(moi or ung)
            t = the_cau(x["ma"], ls)
            t["ghi_chu"] = ghi
            t["con"] = len(ung) - 1
            return t
    return None
