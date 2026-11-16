# -*- coding: utf-8 -*-
"""
ỨNG DỤNG RA ĐỀ THEO MA TRẬN — chạy máy chủ nhỏ trên máy (127.0.0.1) và mở giao diện trong trình duyệt.
Mở bằng: nhấp đúp "Ra de theo ma tran.app" (hoặc file .command), hoặc:  python3 scripts/ung_dung.py
Không cần mạng, không cài thêm gì (chỉ dùng thư viện có sẵn của Python 3).
"""
import os, sys, json, re, csv, time, socket, shutil, threading, subprocess, webbrowser, collections
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nh_core import *

PY = sys.executable or "python3"
SCRIPTS = os.path.join(GOC, "scripts")
CAC_LOAI, CAC_MUC = ["TN", "DS", "TLN", "TL"], ["N", "H", "V", "C"]
lan_ping = [time.time()]
cong_viec = {"dang_chay": False, "nhat_ky": "", "xong": True}

def chay(args, timeout=600):
    r = subprocess.run([PY] + args, cwd=GOC, capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout or "") + (r.stderr or "")

def chi_muc_cu():
    p = os.path.join(GOC, "du-lieu", "chi_muc.jsonl")
    if not os.path.exists(p):
        return True
    t = os.path.getmtime(p)
    for f in glob.glob(os.path.join(GOC, "cau-hoi", "**", "*.tex"), recursive=True):
        if os.path.getmtime(f) > t:
            return True
    return False

def hop_le(c):
    l, d = c["loai"], c["dap_an"]
    return l == "TL" or (l == "TN" and d and len(d) == 1) or (l == "DS" and d and len(d) == 4) or (l == "TLN" and bool(d))

def du_lieu_cay():
    id_map = tai_id_map()
    kho = collections.defaultdict(lambda: {l: [0, 0, 0, 0] for l in CAC_LOAI})
    moi = collections.defaultdict(lambda: {l: [0, 0, 0, 0] for l in CAC_LOAI})
    ls = doc_lich_su()
    for c in map(json.loads, open(os.path.join(GOC, "du-lieu", "chi_muc.jsonl"), encoding="utf-8")):
        if c["dang_key"] and hop_le(c) and c["muc_chuan"] in CAC_MUC:
            i = CAC_MUC.index(c["muc_chuan"])
            kho[c["dang_key"]][c["loai"]][i] += 1
            if not ls.get(c["ma"]):
                moi[c["dang_key"]][c["loai"]][i] += 1
    ds = []
    for k, v in kho.items():
        m = re.match(r"(\d)([A-Z])(\d+)\?(\d+)-(\d+)", k)
        if not m:
            continue
        t = id_map.get(k, {})
        ds.append({"k": k, "lop": lop_tu_so(m.group(1)), "mon": m.group(2), "chuong": int(m.group(3)),
                   "bai": int(m.group(4)), "dang": int(m.group(5)),
                   "ten_chuong": t.get("chap_name") or f"Chương {m.group(3)} ({k[:3]})",
                   "ten_bai": t.get("lesson_name") or f"Bài {m.group(4)}",
                   "ten_dang": t.get("type_name") or f"Dạng {m.group(5)}", "kho": v, "moi": moi[k]})
    ds.sort(key=lambda d: (d["lop"], 0, 0, d["bai"], d["dang"]) if d["lop"] <= 9 else   # THCS: theo thứ tự bài SGK
                          (d["lop"], "DHC".find(d["mon"]), d["chuong"], d["bai"], d["dang"]))
    ch = cau_hinh()
    mac_dinh = {"so_gd": "SỞ GD&ĐT TP. HỒ CHÍ MINH", "truong": "TRƯỜNG THPT NGUYỄN HỮU CẢNH",
                "nam_hoc": "NĂM HỌC 2026 -- 2027", "thoi_gian": "90 phút", "giao_vien": "Vũ Tiến Lực"}
    mac_dinh.update({k: v for k, v in ch.get("thong_tin_de", {}).items() if not k.startswith("_")})
    ma_tran = sorted(os.path.splitext(f)[0] for f in os.listdir(os.path.join(GOC, "ma-tran")) if f.endswith(".json"))
    return {"dang": ds, "thong_tin": mac_dinh, "ma_tran": ma_tran, "pdflatex": bool(tim_pdflatex()),
            "tong_cau": sum(sum(sum(x) for x in d["kho"].values()) for d in ds)}

def doc_lich_su():
    p = os.path.join(GOC, "du-lieu", "lich_su_dung.json")
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return {}

def tom_tat_lich_su():
    ls = doc_lich_su()
    theo_de = collections.Counter(d for v in ls.values() for d in v)
    return {"so_cau": sum(1 for v in ls.values() if v),
            "de": [{"ten": d, "so_cau": n} for d, n in sorted(theo_de.items())]}

def doc_csv(p):
    phan = collections.OrderedDict((l, []) for l in CAC_LOAI)
    with open(p, encoding="utf-8-sig", newline="") as f:
        s = f.read(4096); f.seek(0)
        dl = csv.Sniffer().sniff(s, delimiters=",;\t") if s else csv.excel
        for r in csv.DictReader(f, dialect=dl):
            for l in CAC_LOAI:
                for m in CAC_MUC:
                    v = (r.get(f"{l}_{m}") or "").strip()
                    if v and v not in ("0", "-"):
                        phan[l].append({"dang": r["ma_dang"].strip(), "muc": m, "so": int(float(v))})
    return [{"loai": l, "yeu_cau": y} for l, y in phan.items() if y]

def doc_ma_tran(ten):
    p = os.path.join(GOC, "ma-tran", ten + ".json")
    mt = json.load(open(p, encoding="utf-8"))
    if "ma_tran_csv" in mt and not mt.get("phan"):
        q = mt["ma_tran_csv"]; q = q if os.path.isabs(q) else os.path.join(GOC, q)
        mt["phan"] = doc_csv(q)
    return mt

def ten_an_toan(s):
    s = ten_khong_dau(s or "De", 60) or "De"
    goc, i = s, 2
    while os.path.exists(os.path.join(GOC, "de-da-ra", s)):
        s = f"{goc}_{i}"; i += 1
    return s

def bien_dich_nen(rel):
    cong_viec.update(dang_chay=True, xong=False, nhat_ky="")
    def ghi_log(x):
        cong_viec["nhat_ky"] += x + "\n"
    try:
        bien_dich_thu_muc(os.path.join(GOC, rel), ghi_log)
    except Exception as e:
        ghi_log(f"Lỗi biên dịch: {e}")
    ghi_log("Xong.")
    cong_viec.update(dang_chay=False, xong=True)

def chay_bo_de(cfg, bd):
    import bo_de
    cong_viec.update(dang_chay=True, xong=False, nhat_ky="")
    def ghi_log(x):
        cong_viec["nhat_ky"] += x + "\n"
    try:
        bo_de.chay(cfg, ghi_log, bien_dich=bd)
    except Exception as e:
        ghi_log(f"Lỗi: {e}")
    ghi_log("Xong.")
    cong_viec.update(dang_chay=False, xong=True)

def bien_dich_ts10(out):
    import ts10
    cong_viec.update(dang_chay=True, xong=False, nhat_ky="")
    def ghi_log(x):
        cong_viec["nhat_ky"] += x + "\n"
    try:
        ghi_log("Biên dịch PDF…"); ts10.bien_dich(out, ghi_log)
    except Exception as e:
        ghi_log(f"Lỗi biên dịch: {e}")
    ghi_log("Xong.")
    cong_viec.update(dang_chay=False, xong=True)

def bai_giang_pdf(d, log):
    """Bài giảng PDF chữa đề: xuất đúng bộ câu đã đăng (không đảo) → biên dịch Beamer sửa bài → đưa vào mục lục lớp."""
    import thi_truc_tuyen as T
    bo = d.get("bo") or []
    if not bo:
        return
    log(f"Dựng bài giảng PDF (Beamer sửa bài) cho {len(bo)} bộ câu…")
    mt = dict(d.get("mt") or {})
    mt.update({"ten": ten_khong_dau((d.get("slug") or "bai_giang") + "_baigiang", 60), "so_ma_de": len(bo),
               "ma_de_bat_dau": int(d.get("bat_dau") or 101), "moi_ma_de_cau_khac_nhau": len(bo) > 1, "chon_san": bo,
               "xao_cau": False, "xao_phuong_an": False, "xao_y_dung_sai": False, "xuat_beamer": True, "xuat_leftnote": False,
               "xuat_word": False, "xuat_word_k12": False, "xuat_word_de": False, "de_cuong": False})
    mt.pop("tranh_ma", None)
    p = os.path.join(GOC, "du-lieu", "_ma_tran_tam.json")
    json.dump(mt, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    rc, ra = chay([os.path.join(SCRIPTS, "tron_de.py"), p])
    m = re.search(r"^THU_MUC:(.*)$", ra, re.M)
    if rc != 0 or not m:
        log("✗ Chưa xuất được đề cho bài giảng PDF:\n" + ra[-800:]); return
    thu = os.path.join(GOC, m.group(1).strip()); tex = os.path.join(thu, "tex")
    pdfl = tim_pdflatex()
    if not pdfl:
        log("✗ Máy chưa có pdflatex — bỏ qua bài giảng PDF."); return
    for i in range(len(bo)):
        so = int(d.get("bat_dau") or 101) + i
        f = f"BeamerTrang_{so}.tex"
        if not os.path.exists(os.path.join(tex, f)):
            log(f"   ✗ không thấy {f}"); continue
        for _ in range(2):
            subprocess.run([pdfl, "-interaction=nonstopmode", f], cwd=tex, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1800)
        pdf = os.path.join(tex, f[:-4] + ".pdf")
        if not os.path.exists(pdf):
            log(f"   ✗ biên dịch lỗi {f} (xem {os.path.relpath(tex, GOC)}/{f[:-4]}.log)"); continue
        nhieu = len(bo) > 1
        sl = T.them_bai_giang(f"{d.get('slug')}{'-' + str(so) if nhieu else ''}-pdf",
                              f"{d.get('ten')}{' – Mã ' + str(so) if nhieu else ''} – chữa đề (PDF)", int(d.get("lop") or 10), "pdf",
                              open(pdf, "rb").read(), ghi_de=True, nguon=os.path.relpath(pdf, GOC))
        log(f"   ✓ bài giảng PDF: bai-giang/{sl}/")


def dang_thi_nen(viec=None):
    """Đổi đề (nếu có) rồi đăng thư mục thi-truc-tuyen/site lên Cloudflare Pages."""
    import thi_truc_tuyen as T
    cong_viec.update(dang_chay=True, xong=False, nhat_ky="", thi_url="")
    def ghi_log(x):
        cong_viec["nhat_ky"] += x + "\n"
    try:
        if viec:
            viec(ghi_log)
        cong_viec["thi_url"] = T.dang(ghi_log)
        cong_viec["thi_ok"] = True
    except Exception as e:
        cong_viec["thi_ok"] = False
        ghi_log(f"✗ {e}")
    ghi_log("Xong.")
    cong_viec.update(dang_chay=False, xong=True)

class XuLy(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def gui(self, ma, du_lieu, loai="application/json; charset=utf-8"):
        b = du_lieu if isinstance(du_lieu, bytes) else json.dumps(du_lieu, ensure_ascii=False).encode("utf-8")
        self.send_response(ma); self.send_header("Content-Type", loai)
        self.send_header("Content-Length", str(len(b))); self.send_header("Cache-Control", "no-store")
        self.end_headers(); self.wfile.write(b)

    def doc_than(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        u = urlparse(self.path); q = parse_qs(u.query)
        lan_ping[0] = time.time()
        try:
            if u.path in ("/", "/index.html"):
                return self.gui(200, open(os.path.join(SCRIPTS, "ung_dung.html"), "rb").read(), "text/html; charset=utf-8")
            if u.path == "/api/du-lieu":
                return self.gui(200, du_lieu_cay())
            if u.path == "/api/ma-tran":
                return self.gui(200, doc_ma_tran(q["ten"][0]))
            if u.path == "/api/lich-su":
                return self.gui(200, tom_tat_lich_su())
            if u.path == "/api/trang-thai":
                return self.gui(200, cong_viec)
            if u.path == "/trinh-chieu-app":
                return self.gui(200, open(os.path.join(GOC, "khung", "TrinhChieu", "ung_dung_trinh_chieu.html"), "rb").read(),
                                "text/html; charset=utf-8")
            if u.path == "/api/ping":
                return self.gui(200, {"ok": True, "ban": MA_KHOI, "cu": ma_ma_nguon() != MA_KHOI})
            if u.path == "/tai":            # tải file đề đã xuất (chỉ trong de-da-ra)
                from urllib.parse import quote
                goc = os.path.realpath(os.path.join(GOC, "de-da-ra"))
                f = os.path.realpath(os.path.join(GOC, (q.get("p") or [""])[0]))
                if not f.startswith(goc + os.sep) or not os.path.isfile(f):
                    return self.gui(404, {"loi": "không có file"})
                b = open(f, "rb").read(); ten = os.path.basename(f)
                loai = {".html": "text/html; charset=utf-8", ".pdf": "application/pdf", ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}.get(os.path.splitext(f)[1].lower(), "application/octet-stream")
                self.send_response(200); self.send_header("Content-Type", loai); self.send_header("Content-Length", str(len(b)))
                self.send_header("Content-Disposition", ("inline" if f.endswith((".pdf", ".html")) and "xem" in q else "attachment") + "; filename*=UTF-8''" + quote(ten))
                self.end_headers(); self.wfile.write(b); return
            self.gui(404, {"loi": "không có"})
        except Exception as e:
            self.gui(500, {"loi": str(e)})

    def do_POST(self):
        u = urlparse(self.path); lan_ping[0] = time.time()
        try:
            d = self.doc_than()
            if u.path == "/api/xuat":
                mt = d["ma_tran"]; thu = d.get("thu", False)
                if not any(p["yeu_cau"] for p in mt.get("phan", [])):
                    return self.gui(200, {"ok": False, "nhat_ky": "Ma trận chưa có số câu nào."})
                if thu:
                    p = os.path.join(GOC, "du-lieu", "_ma_tran_tam.json")
                    mt = {**mt, "ten": "_xem_truoc"}
                else:
                    mt = {**mt, "ten": ten_khong_dau(mt.get("ten") or "De", 60) or "De"}
                    p = os.path.join(GOC, "ma-tran", mt["ten"] + ".json")
                    if mt.get("chon_san"):      # bộ câu đã xác nhận: lưu ma trận sạch, chạy bằng file tạm có danh sách câu
                        json.dump({k: v for k, v in mt.items() if k != "chon_san"}, open(p, "w", encoding="utf-8"),
                                  ensure_ascii=False, indent=2)
                        p = os.path.join(GOC, "du-lieu", "_ma_tran_tam.json")
                json.dump(mt, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
                rc, log = chay([os.path.join(SCRIPTS, "tron_de.py"), p] + (["--thu"] if thu else []))
                ok = rc == 0
                m = re.search(r"^THU_MUC:(.*)$", log, re.M)
                rel = m.group(1).strip() if m else ""
                log = re.sub(r"^THU_MUC:.*\n?", "", log, flags=re.M)
                dang_bd = False
                if ok and rel and not thu and d.get("bien_dich") and tim_pdflatex():
                    dang_bd = True
                    threading.Thread(target=bien_dich_nen, args=(rel,), daemon=True).start()
                bo = None
                if thu and ok:
                    try:
                        import xem_truoc
                        x = json.load(open(os.path.join(GOC, "du-lieu", "_xem_truoc.json"), encoding="utf-8"))
                        bo = {"khac_cau": x["khac_cau"], "bo": xem_truoc.bo_cau(x["bo"])}
                    except Exception as e:
                        log += f"\n(không dựng được bản xem trước: {e})"
                ma_dung = []
                if ok and rel and not thu:
                    try:
                        ma_dung = json.load(open(os.path.join(GOC, rel, "_ma_cau_dung.json"), encoding="utf-8"))
                    except Exception:
                        pass
                return self.gui(200, {"ok": ok, "nhat_ky": log, "ten": mt["ten"], "thu_muc": rel, "bien_dich": dang_bd, "xem": bo,
                                      "ma_dung": ma_dung})
            if u.path == "/api/tep-de":     # file PDF / Excel / Word ở gốc thư mục đề vừa xuất
                thu = os.path.realpath(os.path.join(GOC, d.get("thu_muc") or ""))
                if not thu.startswith(os.path.realpath(os.path.join(GOC, "de-da-ra")) + os.sep) or not os.path.isdir(thu):
                    return self.gui(200, {"ok": False, "ds": []})
                ds = sorted(f for f in os.listdir(thu) if os.path.splitext(f)[1].lower() in (".pdf", ".xlsx", ".docx"))
                return self.gui(200, {"ok": True, "ds": [{"ten": f, "p": os.path.relpath(os.path.join(thu, f), GOC)} for f in ds]})
            if u.path == "/api/de-ai/kiem":
                import de_ai
                return self.gui(200, de_ai.kiem(d.get("van_ban") or "", d.get("can")))
            if u.path == "/api/khoi-dong-lai":
                if cong_viec.get("dang_chay"):
                    return self.gui(200, {"ok": False, "loi": "Đang có việc chạy, đợi xong rồi khởi động lại."})
                self.gui(200, {"ok": True})
                threading.Thread(target=khoi_dong_lai, args=(self.server.server_address[1],), daemon=True).start()
                return
            if u.path.startswith("/api/thi/"):
                import thi_truc_tuyen as T
                viec = u.path.rsplit("/", 1)[1]
                if viec == "ds":
                    return self.gui(200, {"ok": True, "ds": T.danh_sach(), "cau_hinh": T.cau_hinh(), "goc": T.goc_url(),
                                          "co_node": T.co_node()})
                if viec == "cau-hinh":
                    c = T.luu_cau_hinh(d)
                    return self.gui(200, {"ok": True, "cau_hinh": c, "goc": T.goc_url(c)})
                if viec == "du-lieu":
                    import trinh_chieu
                    nk = []
                    try:
                        du = trinh_chieu.lap_du_lieu(d.get("ma") or [], (d.get("ten") or "Đề thi").strip(), in_ra=nk.append)
                    except Exception as e:
                        return self.gui(200, {"ok": False, "loi": str(e), "nhat_ky": "\n".join(nk)})
                    return self.gui(200, {"ok": True, "du_lieu": du, "nhat_ky": "\n".join(nk)})
                if viec == "tk-ds":
                    return self.gui(200, T.goi("tk/ds"))
                if viec == "tk-nhap":
                    return self.gui(200, T.nhap_hs(d.get("van_ban") or "", d.get("lop") or ""))
                if viec == "tk-dat-lai":
                    return self.gui(200, T.dat_lai_mk(d.get("ten") or ""))
                if viec == "tk-khoa":
                    return self.gui(200, T.goi("tk/khoa", {"ten": d.get("ten"), "khoa": bool(d.get("khoa"))}))
                if viec == "tk-xoa":
                    return self.gui(200, T.goi("tk/xoa", {"ten": d.get("ten")}))
                if viec == "gv-them":
                    return self.gui(200, T.them_gv(d.get("ten"), d.get("ho_ten"), d.get("mk")))
                if viec == "phieu":
                    return self.gui(200, {"ok": True, "html": T.phieu_tai_khoan(d.get("lop") or "")})
                if viec == "diem":
                    return self.gui(200, T.goi("diem", {"nhom": d.get("nhom")}))
                if viec == "luot-them":
                    return self.gui(200, T.goi("luot/them", {"tk": d.get("tk"), "nhom": d.get("nhom"), "so": int(d.get("so") or 1)}))
                if viec == "bai-xoa":
                    return self.gui(200, T.goi("bai/xoa", {"id": d.get("id")}))
                if viec == "de-sua":
                    ds = T.danh_sach()
                    for x in ds:
                        if x["slug"] == d.get("slug") and x.get("loai") != "bai_giang":
                            x["lop_giao"] = T.chuan_lop(d.get("lop_giao") or ""); x["so_luot"] = int(d.get("so_luot") or 0)
                            for y in ds:      # nhóm: áp cho mã con
                                if y.get("nhom") == x["slug"]:
                                    y["lop_giao"], y["so_luot"] = x["lop_giao"], x["so_luot"]
                    T.luu_ds(ds)
                    return self.gui(200, {"ok": T.dong_bo_de(lambda *_: None)})
                if viec == "bg-nguon":
                    return self.gui(200, {"ok": True, "ds": T.nguon_ung_dung()})
                if viec == "bg-json":
                    try:
                        return self.gui(200, {"ok": True, "du_lieu": json.loads(T.doc_nguon(d["duong_dan"]).decode("utf-8"))})
                    except Exception as e:
                        return self.gui(200, {"ok": False, "loi": str(e)})
                if cong_viec.get("dang_chay"):
                    return self.gui(200, {"ok": False, "loi": "Đang có việc chạy, đợi xong rồi bấm lại."})
                if viec == "bg-dang":
                    import base64
                    try:
                        if d.get("duong_dan"):
                            noi = T.doc_nguon(d["duong_dan"])
                        elif d.get("base64"):
                            noi = base64.b64decode(d["base64"])
                        else:
                            noi = (d.get("html") or "").encode("utf-8")
                        if not noi:
                            raise RuntimeError("Chưa có nội dung bài giảng.")
                        slug = T.them_bai_giang(d.get("slug"), (d.get("ten") or "Bài giảng").strip(), int(d.get("lop") or 10),
                                                d.get("kieu") or "html", noi, bool(d.get("ghi_de")), d.get("nguon") or "",
                                                d.get("chuong") or "", d.get("bai") or "", d.get("chuong_so") or 0)
                    except Exception as e:
                        return self.gui(200, {"ok": False, "loi": str(e)})
                    if d.get("dang_ngay", True):
                        threading.Thread(target=dang_thi_nen, daemon=True).start()
                    return self.gui(200, {"ok": True, "slug": slug, "url": f"{T.goc_url()}/bai-giang/{slug}/",
                                          "muc_luc": f"{T.goc_url()}/toan{int(d.get('lop') or 10)}/"})
                if viec == "bg-hs":
                    try:
                        T.dat_hs(d.get("slug"), bool(d.get("hs")))
                    except Exception as e:
                        return self.gui(200, {"ok": False, "loi": str(e)})
                    threading.Thread(target=dang_thi_nen, daemon=True).start()
                    return self.gui(200, {"ok": True})
                if viec == "phieu-web":      # phiếu học tập → HTML (+ đăng lên web: chỉ GV hoặc cho HS khối lớp)
                    import phieu_web
                    dong = []
                    try:
                        p, P = phieu_web.ghi(d.get("thu_muc") or "", dong.append)
                        ra = {"ok": True, "tep": os.path.relpath(p, GOC), "nhat_ky": "\n".join(dong)}
                        if d.get("dang") in ("gv", "hs"):
                            ten = (d.get("ten") or P.get("ten") or "Phiếu học tập").strip()
                            ten = ten if ten.lower().startswith("phiếu") else ("Phiếu tự luận – " if P.get("kieu") == "tu_luan" else "Phiếu học tập – ") + ten
                            lop = int(re.sub(r"\D", "", str(P.get("lop") or "")) or 10)
                            slug = T.them_bai_giang(d.get("slug") or ("phieu-" + T.lam_slug(P.get("ten") or ten) + ("-tl" if P.get("kieu") == "tu_luan" else "")),
                                                    ten, lop, "html", open(p, "rb").read(), True, "phiếu học tập",
                                                    P.get("chuong") or "", P.get("ten") or "", 0, hs=d["dang"] == "hs", loai_bg="phieu")
                            threading.Thread(target=dang_thi_nen, daemon=True).start()
                            ra.update(slug=slug, url=f"{T.goc_url()}/bai-giang/{slug}/")
                    except Exception as e:
                        return self.gui(200, {"ok": False, "loi": str(e), "nhat_ky": "\n".join(dong)})
                    return self.gui(200, ra)
                if viec == "bg-pdf":
                    threading.Thread(target=dang_thi_nen, args=(lambda log: bai_giang_pdf(d, log),), daemon=True).start()
                    return self.gui(200, {"ok": True})
                if viec == "bg-trang-thai":
                    sl, tt = d.get("slug"), d.get("tt")
                    threading.Thread(target=dang_thi_nen, args=(lambda log: (T.doi_bai_giang(sl, tt),
                                     log(f"Bài giảng {sl} → {tt}")),), daemon=True).start()
                    return self.gui(200, {"ok": True})
                if viec == "dang":
                    try:
                        slug = T.them_de(d.get("slug"), (d.get("ten") or "Đề thi").strip(), d["html"],
                                         bool(d.get("an_dap_an", True)), d.get("phut"), lop_giao=d.get("lop_giao") or "",
                                         so_luot=int(d.get("so_luot") if d.get("so_luot") is not None else 2))
                    except Exception as e:
                        return self.gui(200, {"ok": False, "loi": str(e)})
                    if d.get("dang_ngay", True):
                        threading.Thread(target=dang_thi_nen, daemon=True).start()
                    return self.gui(200, {"ok": True, "slug": slug, "url": T.goc_url() + "/" + slug + "/"})
                if viec == "nhom":
                    slug = T.them_nhom(d.get("slug"), (d.get("ten") or "Đề thi").strip(), d.get("con") or [],
                                       d.get("lop_giao") or "", int(d.get("so_luot") if d.get("so_luot") is not None else 2))
                    if d.get("dang_ngay", True):
                        threading.Thread(target=dang_thi_nen, daemon=True).start()
                    return self.gui(200, {"ok": True, "slug": slug, "url": T.goc_url() + "/" + slug + "/"})
                if viec == "trang-thai":
                    sl, tt = d.get("slug"), d.get("tt")
                    threading.Thread(target=dang_thi_nen, args=(lambda log: (T.doi_trang_thai(sl, tt),
                                     log(f"Đã đổi đề {sl} → {tt}")),), daemon=True).start()
                    return self.gui(200, {"ok": True})
                if viec == "dang-lai":
                    threading.Thread(target=dang_thi_nen, daemon=True).start()
                    return self.gui(200, {"ok": True})
            if u.path == "/api/trinh-chieu":
                import trinh_chieu
                nk = []
                try:
                    kq = trinh_chieu.tao(d.get("ma") or [], (d.get("ten") or "Đề trình chiếu").strip(), in_ra=nk.append)
                except Exception as e:
                    return self.gui(200, {"ok": False, "nhat_ky": "\n".join(nk + [f"Lỗi: {e}"])})
                if d.get("mo", True):
                    p = kq["html"]
                    try:
                        if sys.platform.startswith("win"):
                            os.startfile(p)
                        else:
                            subprocess.Popen(["open", p] if sys.platform == "darwin" else ["xdg-open", p])
                    except Exception:
                        nk.append("  (Không tự mở được trình duyệt — thầy mở file HTML trong thư mục trên.)")
                return self.gui(200, {"ok": True, "nhat_ky": "\n".join(nk), "html": os.path.relpath(kq["html"], GOC),
                                      "thu_muc": os.path.relpath(os.path.dirname(kq["html"]), GOC)})
            if u.path == "/api/doi-cau":
                import xem_truoc
                t = xem_truoc.doi(d.get("ma"), d.get("tranh") or [], da_dung=d.get("da_dung") or "uu_tien")
                return self.gui(200, {"ok": bool(t), "cau": t})
            if u.path == "/api/luu-ma-tran":
                mt = d["ma_tran"]; ten = ten_khong_dau(mt.get("ten") or "MaTran", 60)
                json.dump({**mt, "ten": ten}, open(os.path.join(GOC, "ma-tran", ten + ".json"), "w", encoding="utf-8"),
                          ensure_ascii=False, indent=2)
                return self.gui(200, {"ok": True, "ten": ten})
            if u.path == "/api/mo":
                p = os.path.realpath(os.path.join(GOC, d.get("duong_dan", "")))
                if not p.startswith(os.path.realpath(GOC)) or not os.path.exists(p):
                    return self.gui(400, {"ok": False})
                if sys.platform.startswith("win"):
                    os.startfile(p)
                else:
                    subprocess.Popen(["open", p] if sys.platform == "darwin" else ["xdg-open", p])
                return self.gui(200, {"ok": True})
            if u.path == "/api/tron-file":
                # TRỘN ĐỀ CÓ SẴN: lưu file đề vào de-da-ra/_nguon/, chạy tron_de với tu_file
                t = d.get("tep") or {}
                ten_goc = os.path.basename(t.get("ten") or "de.tex")
                thu_nguon = os.path.join(GOC, "de-da-ra", "_nguon"); os.makedirs(thu_nguon, exist_ok=True)
                p_nguon = os.path.join(thu_nguon, time.strftime("%Y%m%d-%H%M%S_") + ten_goc)
                open(p_nguon, "w", encoding="utf-8").write(t.get("noi_dung") or "")
                mt = {**(d.get("ma_tran") or {}), "tu_file": os.path.relpath(p_nguon, GOC), "phan": []}
                mt["ten"] = ten_khong_dau(os.path.splitext(ten_goc)[0], 60) or "De"
                p = os.path.join(GOC, "du-lieu", "_tron_file.json")
                json.dump(mt, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
                rc, log = chay([os.path.join(SCRIPTS, "tron_de.py"), p], timeout=1800)
                m = re.search(r"^THU_MUC:(.*)$", log, re.M)
                rel = m.group(1).strip() if m else ""
                log = re.sub(r"^THU_MUC:.*\n?", "", log, flags=re.M)
                dang_bd = False
                if rc == 0 and rel and d.get("bien_dich") and tim_pdflatex():
                    dang_bd = True
                    threading.Thread(target=bien_dich_nen, args=(rel,), daemon=True).start()
                return self.gui(200, {"ok": rc == 0, "nhat_ky": log, "thu_muc": rel, "bien_dich": dang_bd})
            if u.path == "/api/prompt":
                import tao_prompt
                return self.gui(200, {"ok": True, "noi_dung": tao_prompt.tao_prompt(d.get("pham_vi") or [])})
            if u.path == "/api/prompt-soan":
                import tao_prompt
                try:
                    nd = tao_prompt.tao_prompt_soan(d.get("dang") or [], d.get("so_cau") or {}, d.get("tai_lieu") or "",
                                                    d.get("cach") or "ket_hop", bool(d.get("thuc_te")), d.get("ghi_chu") or "")
                except ValueError as e:
                    return self.gui(200, {"ok": False, "loi": str(e)})
                return self.gui(200, {"ok": True, "noi_dung": nd})
            if u.path == "/api/cau-trung":
                import cau_trung
                return self.gui(200, {"ok": True, "nhom": cau_trung.tim(float(d.get("nguong") or 0.9))})
            if u.path == "/api/xoa-trung":
                import cau_trung
                dong = []
                so = cau_trung.xoa(d.get("ma") or [], dong.append)
                return self.gui(200, {"ok": True, "so": so, "nhat_ky": "\n".join(dong)})
            if u.path == "/api/cau-lac":
                import quan_ly_cau
                if d.get("tim"):
                    return self.gui(200, {"ok": True, "ds": quan_ly_cau.tim_cau(d["tim"])})
                return self.gui(200, {"ok": True, "ds": quan_ly_cau.tim_lac()})
            if u.path == "/api/sua-cau":
                import quan_ly_cau
                dong = []
                try:
                    if d.get("viec") == "chuyen":
                        so = quan_ly_cau.chuyen(d.get("ds") or [], dong.append)
                    elif d.get("viec") == "xoa":
                        so = quan_ly_cau.xoa(d.get("ma") or [], dong.append)
                    else:
                        so = quan_ly_cau.bo_qua(d.get("ma") or [])
                        dong.append(f"Đã đánh dấu {so} câu là đúng bài (lần sau không báo nữa).")
                except ValueError as e:
                    return self.gui(200, {"ok": False, "nhat_ky": str(e)})
                return self.gui(200, {"ok": True, "so": so, "nhat_ky": "\n".join(dong)})
            if u.path == "/api/bo-de":
                if cong_viec.get("dang_chay"):
                    return self.gui(200, {"ok": False, "loi": "Đang có việc chạy (biên dịch…), đợi xong rồi bấm lại."})
                bd = bool(d.get("bien_dich")) and bool(tim_pdflatex())
                threading.Thread(target=chay_bo_de, args=(d.get("cau_hinh") or {}, bd), daemon=True).start()
                return self.gui(200, {"ok": True, "bien_dich": bd})
            if u.path.startswith("/api/ts10/"):
                import ts10
                viec = u.path.rsplit("/", 1)[1]
                try:
                    if viec == "thong-ke":
                        return self.gui(200, {"ok": True, **ts10.thong_ke()})
                    if viec == "nhap":
                        return self.gui(200, {"ok": True, **ts10.nhap(d.get("van_ban") or "", bool(d.get("thu")))})
                    if viec == "dong-bo":
                        import ts10_tu_kho9
                        dong = []
                        kq = ts10_tu_kho9.chay(bool(d.get("thu")), in_ra=dong.append)
                        return self.gui(200, {"ok": True, **kq, "nhat_ky": "\n".join(dong)})
                    if viec == "prompt":
                        return self.gui(200, {"ok": True, "noi_dung": ts10.prompt(d["bai"], d.get("dang") or [], int(d.get("so_luong") or 5))})
                    if viec == "xem":
                        bo, thieu = ts10.chon_bo(d.get("cau_hinh") or {})
                        return self.gui(200, {"ok": True, "thieu": thieu,
                                              "bo": [{b: ts10.the_xem(x) for b, x in de.items()} for de in bo]})
                    if viec == "doi":
                        x = ts10.doi(d["bai"], d.get("kieu"), d.get("tranh") or [], d.get("ma"), d.get("da_dung") or "uu_tien")
                        return self.gui(200, {"ok": bool(x), "bai": ts10.the_xem(x) if x else None})
                    if viec == "tao":
                        dong = []
                        out = ts10.tao(d.get("cau_hinh") or {}, dong.append, d.get("chon_san"))
                        bd = bool(d.get("bien_dich")) and bool(tim_pdflatex())
                        if bd:
                            threading.Thread(target=bien_dich_ts10, args=(out,), daemon=True).start()
                        return self.gui(200, {"ok": True, "thu_muc": os.path.relpath(out, GOC), "bien_dich": bd,
                                              "nhat_ky": "\n".join(x for x in dong if not x.startswith("THU_MUC:"))})
                except Exception as e:
                    return self.gui(200, {"ok": False, "loi": str(e)})
            if u.path.startswith("/api/kho-kt/"):
                import kho_kien_thuc as K
                viec = u.path.rsplit("/", 1)[1]
                try:
                    if viec == "ds":
                        return self.gui(200, {"ok": True, "bai": K.danh_sach(d.get("lop") or 12)})
                    if viec == "doc":
                        return self.gui(200, {"ok": True, "noi_dung": K.doc(d["bai"])})
                    if viec == "luu":
                        return self.gui(200, {"ok": True, "so_pp": K.luu(d["bai"], d.get("noi_dung") or "")})
                    if viec == "nhap":
                        return self.gui(200, {"ok": True, "ket_qua": K.nhap(d.get("van_ban") or "", d.get("bai"))})
                    if viec == "prompt":
                        return self.gui(200, {"ok": True, "noi_dung": K.prompt(d.get("bai") or [])})
                except Exception as e:
                    return self.gui(200, {"ok": False, "loi": str(e)})
            if u.path == "/api/kien-thuc":
                import phieu_bai_hoc
                return self.gui(200, {"ok": True, "noi_dung": phieu_bai_hoc.doc_kien_thuc(d.get("pham_vi") or [])})
            if u.path == "/api/phieu-thieu":
                import phieu_bai_hoc
                cfg = d.get("cau_hinh") or {}
                try:
                    thieu = phieu_bai_hoc.tao(cfg, lambda x: None, chi_tinh=True)
                except Exception as e:
                    return self.gui(200, {"ok": False, "loi": str(e)})
                return self.gui(200, {"ok": True, "thieu": thieu,
                                      "bo_sung": phieu_bai_hoc.goi_y_bo_sung(cfg.get("dang") or [], phieu_bai_hoc.tai_id_map())})
            if u.path == "/api/phieu":
                import phieu_bai_hoc
                dong = []
                cfg = d.get("cau_hinh") or {}
                def bo_sung():
                    try:
                        return phieu_bai_hoc.goi_y_bo_sung(cfg.get("dang") or [], phieu_bai_hoc.tai_id_map())
                    except Exception:
                        return None
                try:
                    out_goc = phieu_bai_hoc.tao(cfg, dong.append)
                except Exception as e:
                    return self.gui(200, {"ok": False, "nhat_ky": f"Chưa tạo được phiếu: {e}", "bo_sung": bo_sung()})
                rel = os.path.relpath(out_goc, GOC)
                dang_bd = False
                if d.get("bien_dich") and tim_pdflatex():
                    dang_bd = True
                    threading.Thread(target=bien_dich_nen, args=(rel,), daemon=True).start()
                log = "\n".join(x for x in dong if not x.startswith("THU_MUC:"))
                return self.gui(200, {"ok": True, "nhat_ky": log, "thu_muc": rel, "bien_dich": dang_bd, "bo_sung": bo_sung()})
            if u.path == "/api/danh-muc-dang":
                import tao_prompt
                return self.gui(200, {"ok": True, "dang": tao_prompt.danh_sach_dang()})
            if u.path == "/api/nhap":
                import nhap_cau, tempfile
                thu_muc = tempfile.mkdtemp(prefix="nhap_")
                duong = []
                for t in d.get("tep", []):
                    ten = os.path.basename(t["ten"]) or "cau_moi.tex"
                    p = os.path.join(thu_muc, ten)
                    open(p, "w", encoding="utf-8").write(t["noi_dung"])
                    duong.append(p)
                dong = []
                so = nhap_cau.nhap(duong, thu=d.get("thu", True), in_ra=dong.append, ma_dang=(d.get("ma_dang") or None))
                shutil.rmtree(thu_muc, ignore_errors=True)
                return self.gui(200, {"ok": True, "so_cau": so, "nhat_ky": "\n".join(dong)})
            if u.path == "/api/lich-su":
                p = os.path.join(GOC, "du-lieu", "lich_su_dung.json")
                ls = doc_lich_su()
                if d.get("xoa_het"):
                    ls = {}
                elif d.get("bo_de"):
                    ls = {k: [x for x in v if x != d["bo_de"]] for k, v in ls.items()}
                    ls = {k: v for k, v in ls.items() if v}
                json.dump(ls, open(p, "w", encoding="utf-8"), ensure_ascii=False)
                return self.gui(200, {"ok": True, **tom_tat_lich_su()})
            if u.path == "/api/lap-chi-muc":
                rc, log = chay([os.path.join(SCRIPTS, "lap_chi_muc.py")])
                return self.gui(200, {"ok": rc == 0, "nhat_ky": log})
            if u.path == "/api/thoat":
                self.gui(200, {"ok": True})
                threading.Thread(target=lambda: (time.sleep(0.3), os._exit(0)), daemon=True).start()
                return
            self.gui(404, {"loi": "không có"})
        except Exception as e:
            self.gui(500, {"ok": False, "nhat_ky": f"Lỗi: {e}"})

def canh_gac():
    """Tự tắt khi không còn cửa sổ nào mở giao diện (không ping quá 3 phút)."""
    while True:
        time.sleep(30)
        if time.time() - lan_ping[0] > 180 and not cong_viec["dang_chay"]:
            os._exit(0)

def ma_ma_nguon():
    """Dấu vân tay mã chương trình (giờ sửa các file .py) — đổi sau git pull → nhắc khởi động lại."""
    return str(int(sum(os.path.getmtime(os.path.join(SCRIPTS, f)) for f in os.listdir(SCRIPTS) if f.endswith(".py"))))


MA_KHOI = ma_ma_nguon()


def khoi_dong_lai(cong):
    time.sleep(0.6)
    try:
        SV[0].server_close()
    except Exception:
        pass
    os.execv(sys.executable, [sys.executable, os.path.abspath(__file__), "--khong-mo", "--cong", str(cong)])


SV = [None]


def cong_trong():
    if "--cong" in sys.argv:                       # khởi động lại: giữ cổng cũ để trang đang mở chạy tiếp
        c = int(sys.argv[sys.argv.index("--cong") + 1])
        for _ in range(25):
            with socket.socket() as s:
                try:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); s.bind(("127.0.0.1", c)); return c
                except OSError:
                    time.sleep(0.2)
    for c in range(8765, 8800):
        with socket.socket() as s:
            try:
                s.bind(("127.0.0.1", c)); return c
            except OSError:
                pass
    return 0

if __name__ == "__main__":
    if chi_muc_cu():
        print("Đang lập chỉ mục ngân hàng…")
        chay([os.path.join(SCRIPTS, "lap_chi_muc.py")])
    cong = cong_trong()
    sv = SV[0] = ThreadingHTTPServer(("127.0.0.1", cong), XuLy)
    url = f"http://127.0.0.1:{cong}/"
    print("Ứng dụng ra đề đang chạy tại", url)
    threading.Thread(target=canh_gac, daemon=True).start()
    if "--khong-mo" not in sys.argv:
        webbrowser.open(url)
    sv.serve_forever()
