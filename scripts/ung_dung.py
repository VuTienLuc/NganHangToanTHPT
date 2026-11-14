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
            if u.path == "/api/ping":
                return self.gui(200, {"ok": True})
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
                return self.gui(200, {"ok": ok, "nhat_ky": log, "ten": mt["ten"], "thu_muc": rel, "bien_dich": dang_bd, "xem": bo})
            if u.path == "/api/doi-cau":
                import xem_truoc
                t = xem_truoc.doi(d.get("ma"), d.get("tranh") or [])
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
            if u.path.startswith("/api/ts10/"):
                import ts10
                viec = u.path.rsplit("/", 1)[1]
                try:
                    if viec == "thong-ke":
                        return self.gui(200, {"ok": True, **ts10.thong_ke()})
                    if viec == "nhap":
                        return self.gui(200, {"ok": True, **ts10.nhap(d.get("van_ban") or "", bool(d.get("thu")))})
                    if viec == "prompt":
                        return self.gui(200, {"ok": True, "noi_dung": ts10.prompt(d["bai"], d.get("dang") or [], int(d.get("so_luong") or 5))})
                    if viec == "xem":
                        bo, thieu = ts10.chon_bo(d.get("cau_hinh") or {})
                        return self.gui(200, {"ok": True, "thieu": thieu,
                                              "bo": [{b: ts10.the_xem(x) for b, x in de.items()} for de in bo]})
                    if viec == "doi":
                        x = ts10.doi(d["bai"], d.get("kieu"), d.get("tranh") or [], d.get("ma"))
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

def cong_trong():
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
    sv = ThreadingHTTPServer(("127.0.0.1", cong), XuLy)
    url = f"http://127.0.0.1:{cong}/"
    print("Ứng dụng ra đề đang chạy tại", url)
    threading.Thread(target=canh_gac, daemon=True).start()
    if "--khong-mo" not in sys.argv:
        webbrowser.open(url)
    sv.serve_forever()
