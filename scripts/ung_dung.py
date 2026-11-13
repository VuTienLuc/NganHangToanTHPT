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

def tim_pdflatex():
    p = shutil.which("pdflatex")
    for c in (p, "/Library/TeX/texbin/pdflatex", "/usr/local/texlive/2025/bin/universal-darwin/pdflatex",
              "/usr/local/texlive/2026/bin/universal-darwin/pdflatex", "/opt/homebrew/bin/pdflatex"):
        if c and os.path.exists(c):
            return c
    return None

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
    for c in map(json.loads, open(os.path.join(GOC, "du-lieu", "chi_muc.jsonl"), encoding="utf-8")):
        if c["dang_key"] and hop_le(c) and c["muc_chuan"] in CAC_MUC:
            kho[c["dang_key"]][c["loai"]][CAC_MUC.index(c["muc_chuan"])] += 1
    ds = []
    for k, v in kho.items():
        m = re.match(r"(\d)([A-Z])(\d+)\?(\d+)-(\d+)", k)
        if not m:
            continue
        t = id_map.get(k, {})
        ds.append({"k": k, "lop": 10 + int(m.group(1)), "mon": m.group(2), "chuong": int(m.group(3)),
                   "bai": int(m.group(4)), "dang": int(m.group(5)),
                   "ten_chuong": t.get("chap_name") or f"Chương {m.group(3)} ({k[:3]})",
                   "ten_bai": t.get("lesson_name") or f"Bài {m.group(4)}",
                   "ten_dang": t.get("type_name") or f"Dạng {m.group(5)}", "kho": v})
    ds.sort(key=lambda d: (d["lop"], "DHC".find(d["mon"]), d["chuong"], d["bai"], d["dang"]))
    ch = cau_hinh()
    mac_dinh = {"so_gd": "SỞ GD&ĐT TP. HỒ CHÍ MINH", "truong": "TRƯỜNG THPT NGUYỄN HỮU CẢNH",
                "nam_hoc": "NĂM HỌC 2026 -- 2027", "thoi_gian": "90 phút"}
    mac_dinh.update({k: v for k, v in ch.get("thong_tin_de", {}).items() if not k.startswith("_")})
    ma_tran = sorted(os.path.splitext(f)[0] for f in os.listdir(os.path.join(GOC, "ma-tran")) if f.endswith(".json"))
    return {"dang": ds, "thong_tin": mac_dinh, "ma_tran": ma_tran, "pdflatex": bool(tim_pdflatex()),
            "tong_cau": sum(sum(sum(x) for x in d["kho"].values()) for d in ds)}

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

def bien_dich_nen(ten, chi_gop):
    pdfl = tim_pdflatex()
    out = os.path.join(GOC, "de-da-ra", ten)
    tep = sorted(f for f in os.listdir(out) if f.endswith(".tex") and f.startswith(ten)
                 and (not chi_gop or "_TatCa_" in f))
    cong_viec.update(dang_chay=True, xong=False, nhat_ky=f"Biên dịch {len(tep)} file trong de-da-ra/{ten}…\n")
    for f in tep:
        ok = True
        for _ in range(2):
            r = subprocess.run([pdfl, "-interaction=nonstopmode", f], cwd=out, capture_output=True, text=True,
                               errors="replace", timeout=600)
        pdf = os.path.join(out, f[:-4] + ".pdf")
        ok = os.path.exists(pdf) and os.path.getmtime(pdf) > time.time() - 900
        cong_viec["nhat_ky"] += f"  {'✓' if ok else '✗'} {f[:-4]}.pdf\n"
    cong_viec.update(dang_chay=False, xong=True)
    cong_viec["nhat_ky"] += "Xong."

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
                    mt = {**mt, "ten": ten_an_toan(mt.get("ten"))}
                    p = os.path.join(GOC, "ma-tran", mt["ten"] + ".json")
                json.dump(mt, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
                rc, log = chay([os.path.join(SCRIPTS, "tron_de.py"), p] + (["--thu"] if thu else []))
                ok = rc == 0
                if ok and not thu and d.get("bien_dich") and tim_pdflatex():
                    threading.Thread(target=bien_dich_nen, args=(mt["ten"], d.get("chi_gop", True)), daemon=True).start()
                return self.gui(200, {"ok": ok, "nhat_ky": log, "ten": mt["ten"],
                                      "thu_muc": os.path.join(GOC, "de-da-ra", mt["ten"])})
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
                so = nhap_cau.nhap(duong, thu=d.get("thu", True), in_ra=dong.append)
                shutil.rmtree(thu_muc, ignore_errors=True)
                return self.gui(200, {"ok": True, "so_cau": so, "nhat_ky": "\n".join(dong)})
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
