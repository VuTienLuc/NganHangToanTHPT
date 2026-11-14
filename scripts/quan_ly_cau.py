# -*- coding: utf-8 -*-
"""
QUẢN LÝ CÂU LẠC BÀI: tìm câu có nội dung không khớp bài/dạng đang gắn, rồi CHUYỂN sang đúng dạng hoặc XOÁ.

Cách dò: mỗi bài học có một "hồ sơ từ khoá" (TF-IDF trung bình của mọi câu trong bài). Câu nào giống hồ sơ của một
bài khác rõ rệt hơn bài của chính nó thì bị đánh dấu "nghi lạc bài", kèm gợi ý bài/dạng đúng (dạng giống nhất trong
bài gợi ý). Thầy xem rồi: Chuyển (đổi mã %[..] và dời câu sang file dạng mới) / Xoá / Đúng rồi (bỏ qua lần sau).

  python3 scripts/quan_ly_cau.py                    # thống kê câu nghi lạc bài
  python3 scripts/quan_ly_cau.py --tim "cấp số cộng"  # tìm câu theo nội dung
Câu bị chuyển/xoá đều được lưu bản sao trong du-lieu/da_xoa/.
"""
import os, sys, re, json, math, time, collections, tempfile, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nh_core import GOC, MA_DANG, tai_id_map
from cau_trung import _bo, gon, xoa as _xoa

P_BO_QUA = os.path.join(GOC, "du-lieu", "da_kiem_tra_lac.json")
P_CACHE = os.path.join(GOC, "du-lieu", "_cau_lac_cache.json")
TU_DUNG = set("và của là cho có các một được với trong không đến từ thì này đó sau như theo bằng hai ba bao nhiêu nào "
              "giá trị khi tại câu đây đúng sai mệnh đề tính tìm biết gọi xét hãy".split())

def bo_dau(s):
    s = unicodedata.normalize("NFD", (s or "").lower().replace("đ", "d"))
    return "".join(c for c in s if unicodedata.category(c) != "Mn")

def tu_khoa(k):
    t = re.sub(r"(?<!\\)%[^\n]*", "", k)
    t, _ = _bo(t, "loigiai")
    w = [x for x in re.findall(r"\\[a-z]+|[a-zà-ỹđ]+", t.lower()) if x not in TU_DUNG and len(x) > 1]
    return collections.Counter(w + [a + "_" + b for a, b in zip(w, w[1:])])

def doc():
    ds = []
    for l in open(os.path.join(GOC, "du-lieu", "chi_muc.jsonl"), encoding="utf-8"):
        ds.append(json.loads(l))
    return ds

def tim_lac(nguong=0.12, dung_cache=True):
    p_cm = os.path.join(GOC, "du-lieu", "chi_muc.jsonl")
    dau_vet = f"{os.path.getmtime(p_cm)}|{nguong}"
    if dung_cache and os.path.exists(P_CACHE):
        try:
            c = json.load(open(P_CACHE, encoding="utf-8"))
            if c.get("dau_vet") == dau_vet:
                return loc_bo_qua(c["ds"])
        except Exception:
            pass
    id_map = tai_id_map()
    ds = [d for d in doc() if d.get("dang_key")]
    for d in ds:
        d["_bai"] = d["dang_key"].split("-")[0]
        d["_tk"] = tu_khoa(d["noi_dung"])
    N = len(ds)
    df = collections.Counter()
    for d in ds:
        df.update(d["_tk"].keys())
    idf = {w: math.log(N / (1 + c)) for w, c in df.items() if c >= 2}
    def vec(c):
        v = {w: (1 + math.log(n)) * idf[w] for w, n in c.items() if w in idf}
        s = math.sqrt(sum(x * x for x in v.values())) or 1
        return {w: x / s for w, x in v.items()}
    tam_bai, tam_dang = collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)
    for d in ds:
        d["_v"] = vec(d["_tk"])
        tam_bai[d["_bai"]].update(d["_v"]); tam_dang[d["dang_key"]].update(d["_v"])
    def chuan_hoa(tam):
        ra = {}
        for k, c in tam.items():
            s = math.sqrt(sum(x * x for x in c.values())) or 1
            ra[k] = {w: x / s for w, x in c.items()}
        return ra
    tam_bai, tam_dang = chuan_hoa(tam_bai), chuan_hoa(tam_dang)
    chi_so = collections.defaultdict(list)
    for k, c in tam_bai.items():
        for w, x in c.items():
            chi_so[w].append((k, x))
    dang_theo_bai = collections.defaultdict(list)
    for k in tam_dang:
        dang_theo_bai[k.split("-")[0]].append(k)
    ra = []
    for d in ds:
        sc = collections.Counter()
        for w, x in d["_v"].items():
            for k, y in chi_so.get(w, ()):
                sc[k] += x * y
        if not sc:
            continue
        cua_minh = sc.get(d["_bai"], 0)
        top = [(k, v) for k, v in sc.most_common(3) if k != d["_bai"]]
        if not top:
            continue
        bai_tot, diem = top[0]
        if diem <= cua_minh + nguong or diem < 0.25:
            continue
        goi_y = []
        for bk, bd in top[:2]:
            if bd <= cua_minh:
                continue
            xep = sorted(((sum(x * tam_dang[k].get(w, 0) for w, x in d["_v"].items()), k) for k in dang_theo_bai[bk]), reverse=True)
            for dd, k in xep[:3 if bk == bai_tot else 1]:
                t = id_map.get(k, {})
                goi_y.append({"k": k, "ten_bai": (t.get("lesson_name") or "").strip(), "ten_dang": (t.get("type_name") or "").strip(),
                              "diem": round(dd, 2)})
        g = gon(d)
        g.update(ten_bai=d.get("ten_bai") or "", ten_dang=d.get("ten_dang") or "", tin_cay=round(diem - cua_minh, 2),
                 goi_y=goi_y, muc=d.get("muc") or "")
        ra.append(g)
    ra.sort(key=lambda x: -x["tin_cay"])
    try:
        json.dump({"dau_vet": dau_vet, "ds": ra}, open(P_CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    except OSError:
        pass
    return loc_bo_qua(ra)

def doc_bo_qua():
    try:
        return set(json.load(open(P_BO_QUA, encoding="utf-8")))
    except Exception:
        return set()

def loc_bo_qua(ds):
    bq = doc_bo_qua()
    return [x for x in ds if x["ma"] not in bq]

def bo_qua(cac_ma):
    bq = doc_bo_qua() | set(cac_ma)
    json.dump(sorted(bq), open(P_BO_QUA, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    return len(cac_ma)

def tim_cau(tu, toi_da=200):
    """Tìm câu theo nội dung / mã dạng / mã câu (không phân biệt dấu)."""
    cac_tu = bo_dau(tu).split()
    if not cac_tu:
        return []
    ra = []
    for d in doc():
        nd = bo_dau(re.sub(r"\s+", " ", d["noi_dung"])) + " " + bo_dau(d.get("file") or "")
        if " ".join(cac_tu) in nd:
            g = gon(d)
            g.update(ten_bai=d.get("ten_bai") or "", ten_dang=d.get("ten_dang") or "", tin_cay=0, goi_y=[], muc=d.get("muc") or "")
            ra.append(g)
            if len(ra) >= toi_da:
                break
    return ra

def doi_ma(khoi, ma_moi, muc_cu):
    """Thay mã dạng %[..] trong khối; ma_moi dạng 2D1?1-2 hoặc 2D1N1-2 ('?' = giữ mức cũ)."""
    ma_moi = ma_moi.strip().upper().replace("%", "").strip("[]")
    if "?" in ma_moi:
        ma_moi = ma_moi.replace("?", muc_cu or "N")
    if MA_DANG.search(khoi):
        return MA_DANG.sub(f"%[{ma_moi}]", khoi, count=1)
    return re.sub(r"(\\begin\{(ex|bt)\})", r"\1" + f"%[{ma_moi}]", khoi, count=1)

def chuyen(cac_yeu_cau, in_ra=print):
    """cac_yeu_cau: [{"ma": mã câu, "ma_dang": mã dạng mới}] → gỡ khỏi file cũ, ghi vào file dạng mới."""
    yc = {x["ma"]: x["ma_dang"] for x in cac_yeu_cau if x.get("ma") and x.get("ma_dang")}
    if not yc:
        return 0
    if any(not re.match(r"^\d[A-Z]\d+[A-Z?]\d+-\d+$", v.strip().upper().strip("%[]")) for v in yc.values()):
        raise ValueError("Mã dạng phải có dạng 2D1?1-2 hoặc 2D1N1-2.")
    khoi = {}
    for d in doc():
        if d["ma"] in yc:
            m = MA_DANG.search(d["noi_dung"])
            muc = m.group(4) if m else None
            khoi[d["ma"]] = doi_ma(d["noi_dung"], yc[d["ma"]], muc)
    _xoa(list(khoi), in_ra, nhan="chuyen_dang", lap_lai=True)
    import nhap_cau
    with tempfile.TemporaryDirectory() as tm:
        p = os.path.join(tm, "chuyen_dang.tex")
        open(p, "w", encoding="utf-8").write("\n\n".join(khoi.values()) + "\n")
        nhap_cau.nhap([p], thu=False, in_ra=lambda x: None)
    in_ra(f"Đã chuyển {len(khoi)} câu sang dạng mới.")
    return len(khoi)

def xoa(cac_ma, in_ra=print):
    return _xoa(cac_ma, in_ra, nhan="xoa_cau")

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--tim":
        for g in tim_cau(" ".join(sys.argv[2:]))[:30]:
            print(g["ma"], g["id"], g["file"], g["xem"][:100])
    else:
        t0 = time.time()
        kq = tim_lac(dung_cache=False)
        print(f"{len(kq)} câu nghi lạc bài ({time.time() - t0:.0f}s). 10 câu rõ nhất:")
        for g in kq[:10]:
            gy = g["goi_y"][0] if g["goi_y"] else {}
            print(f"  {g['id']} ({g['ten_bai']}) → {gy.get('k')} {gy.get('ten_dang')} | {g['xem'][:70]}")
