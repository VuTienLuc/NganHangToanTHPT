# -*- coding: utf-8 -*-
"""SAO LƯU & CHUYỂN MÁY — gói những gì GitHub KHÔNG giữ thành một file .zip để phòng hư máy / cài máy mới.

GitHub đã giữ: mã ứng dụng, ngân hàng câu hỏi (cau-hoi/), kiến thức, ma trận, lịch sử dùng câu… (khi thầy bấm Đồng bộ).
GitHub KHÔNG giữ (cố ý, vì bí mật hoặc quá nặng):
  • ai_khoa.json                      — khoá API AI (Gemini, ChatGPT, DeepSeek, Claude)
  • thi-truc-tuyen/bi_mat.json, mat_khau_dau.json — mã quản trị thi trực tuyến, mật khẩu in phiếu
  • de-da-ra/                         — mọi đề, phiếu, PDF, Word, Excel đã xuất (+ ghim, ghi chú Thư mục đề)
File sao lưu SaoLuu_NganHang_<ngày giờ>.zip gồm:
  bi_mat/…            (đúng cấu trúc mà "Cai dat tren Windows.bat" / "Cai dat tren Mac.command" tự chép vào)
  de-da-ra/…          (tuỳ chọn: chỉ file kết quả, hoặc cả thư mục tex/ để biên dịch lại)
  kho.bundle          (toàn bộ kho git kèm lịch sử — khôi phục được cả khi không vào được GitHub)
  KHOI_PHUC.txt       (hướng dẫn)
Đặt file .zip cạnh file cài đặt trên máy mới → nhấp đúp file cài đặt là xong.

TỰ SAO LƯU HẰNG TUẦN LÊN GOOGLE DRIVE (theo cây /luu-drive: Drive của tôi › claude › Sao lưu ngân hàng):
  cần ứng dụng "Google Drive cho máy tính" (thư mục Drive hiện trong Finder / Explorer). Mỗi 7 ngày:
  • SaoLuu_NganHang_<ngày>.zip  — khoá AI, bí mật thi trực tuyến, kho.bundle (giữ N bản mới nhất, bản cũ hơn vào Thùng rác Drive)
  • de-da-ra/                  — bản sao thư mục đề (chỉ chép file mới / đã đổi; mở được trên điện thoại)
  Chạy khi ứng dụng mở (kiểm tra mỗi 3 giờ) và — nếu bật — bằng lịch của máy (launchd trên Mac, Task Scheduler trên Windows)
  ngay cả khi không mở ứng dụng:  python3 scripts/sao_luu.py --tu-dong
"""
import os, re, sys, json, time, zipfile, subprocess, datetime, shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nh_core import GOC  # noqa: E402

BI_MAT = [("ai_khoa.json", "ai_khoa.json"),
          (os.path.join("thi-truc-tuyen", "bi_mat.json"), "bi_mat.json"),
          (os.path.join("thi-truc-tuyen", "mat_khau_dau.json"), "mat_khau_dau.json")]
P_NK = os.path.join(GOC, "du-lieu", "_sao_luu.json")
BO_DUOI = (".aux", ".log", ".out", ".toc", ".nav", ".snm", ".synctex.gz", ".fls", ".fdb_latexmk", ".xdv", ".gz")


def _git(*a, timeout=60):
    try:
        r = subprocess.run(["git", "-C", GOC, *a], capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip()
    except Exception as e:
        return 1, str(e)


def thu_muc_mac_dinh():
    nha = os.path.expanduser("~")
    for c in ("Desktop", "Màn hình nền", "OneDrive/Desktop"):
        if os.path.isdir(os.path.join(nha, c)):
            return os.path.join(nha, c)
    return nha


def _co_de_ra(che_do):
    """Duyệt de-da-ra → [(đường dẫn thật, tên trong zip)]."""
    goc = os.path.join(GOC, "de-da-ra")
    ra = []
    if che_do == "khong" or not os.path.isdir(goc):
        return ra
    for r, ds, fs in os.walk(goc):
        rel = os.path.relpath(r, GOC)
        ds[:] = [d for d in ds if not d.startswith(".") and d not in ("_k12", "__pycache__")
                 and not (che_do == "ket_qua" and d in ("tex", "_cu", "_kiem_tra_nhap_kho", "_nguon"))]
        for f in fs:
            if f.startswith((".", "~$")) or f.endswith(BO_DUOI) or f.endswith(".icloud"):
                continue
            ra.append((os.path.join(r, f), os.path.join(rel, f)))
    return ra


def tinh_trang():
    """Tình trạng an toàn dữ liệu để hiện trong ứng dụng."""
    t = {"goc": GOC, "dich": thu_muc_mac_dinh()}
    ma, out = _git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    t["co_github"] = ma == 0
    ma, out = _git("rev-list", "--count", "@{u}..HEAD")
    t["chua_day"] = int(out) if ma == 0 and out.isdigit() else None
    ma, out = _git("status", "--porcelain", "--untracked-files=normal", "--", "cau-hoi", "cau-hoi-ts10", "du-lieu", "ma-tran", "ai-nhap", "khung", "cau_hinh.json")
    dong = [l for l in out.splitlines() if l.strip()] if ma == 0 else []
    t["chua_luu"] = len(dong)
    t["chua_luu_vd"] = [l[3:] for l in dong[:6]]
    ma, out = _git("log", "-1", "--format=%cI|%s")
    t["lan_luu_cuoi"] = out.split("|", 1)[0] if ma == 0 and out else ""
    t["bi_mat"] = [{"ten": ten, "co": os.path.exists(os.path.join(GOC, p))} for p, ten in BI_MAT]
    n = kb = 0
    for p, _ in _co_de_ra("ket_qua"):
        n += 1; kb += os.path.getsize(p) // 1024
    t["de_ra"] = {"so_tep": n, "mb": round(kb / 1024, 1)}
    nk = _doc_nk()
    t["lan_truoc"] = nk.get("lan_truoc")
    td = dict(nk.get("tu_dong") or {})
    td.setdefault("bat", False); td.setdefault("giu", 4); td.setdefault("kem_kho", True)
    td["drive"] = tim_drive()
    td["dich_goi_y"] = os.path.join(td["drive"][0], "claude", "Sao lưu ngân hàng") if td["drive"] else ""
    td["den_han"] = _den_han(td)
    td["co_lich"] = co_lich()
    t["tu_dong"] = td
    return t


def _doc_nk():
    try:
        d = json.load(open(P_NK, encoding="utf-8"))
    except Exception:
        return {}
    return {"lan_truoc": d} if "luc" in d else d          # bản cũ chỉ ghi lần sao lưu tay


def _ghi_nk(d):
    try:
        tam = P_NK + ".tam"
        json.dump(d, open(tam, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        os.replace(tam, P_NK)
    except OSError:
        pass


# ------------------------------------------------------------------ TỰ ĐỘNG HẰNG TUẦN LÊN GOOGLE DRIVE
CHU_KY_NGAY = 7


def tim_drive():
    """Thư mục 'Drive của tôi' của Google Drive cho máy tính (Mac / Windows), nếu có."""
    ra, ten = [], ("My Drive", "Drive của tôi", "Mi unidad")
    nha = os.path.expanduser("~")
    goc = []
    cs = os.path.join(nha, "Library", "CloudStorage")
    if os.path.isdir(cs):
        goc += [os.path.join(cs, d) for d in sorted(os.listdir(cs)) if d.startswith("GoogleDrive")]
    goc += [os.path.join(nha, "Google Drive"), os.path.join(nha, "GoogleDrive")]
    if sys.platform.startswith("win"):
        goc += [f"{c}:\\" for c in "GHIJKLMNOPQRSTUVWXYZ"]
    for g in goc:
        try:
            for t in ten:
                p = os.path.join(g, t)
                if os.path.isdir(p):
                    ra.append(p)
        except OSError:
            pass
    return ra


def _den_han(td):
    if not td.get("lan_cuoi"):
        return True
    try:
        return (datetime.datetime.now() - datetime.datetime.fromisoformat(td["lan_cuoi"])).days >= CHU_KY_NGAY
    except Exception:
        return True


def dat_tu_dong(bat=None, dich=None, giu=None, kem_kho=None):
    nk = _doc_nk()
    td = dict(nk.get("tu_dong") or {})
    if bat is not None:
        td["bat"] = bool(bat)
    if dich is not None:
        td["dich"] = os.path.expanduser(dich.strip())
    if giu is not None:
        td["giu"] = max(0, int(giu))
    if kem_kho is not None:
        td["kem_kho"] = bool(kem_kho)
    nk["tu_dong"] = td
    _ghi_nk(nk)
    return td


def _guong_de_ra(dich, in_ra):
    """Chép de-da-ra sang dich/de-da-ra: chỉ file mới / đổi kích thước / mới hơn. Không xoá gì ở đích."""
    moi = 0
    for a, rel in _co_de_ra("ket_qua"):
        b = os.path.join(dich, rel)
        try:
            sa = os.stat(a)
            if os.path.exists(b):
                sb = os.stat(b)
                if sb.st_size == sa.st_size and int(sb.st_mtime) >= int(sa.st_mtime):
                    continue
            os.makedirs(os.path.dirname(b), exist_ok=True)
            shutil.copy2(a, b)
            moi += 1
        except OSError as e:
            in_ra(f"  ⚠ bỏ qua {rel}: {e}")
    return moi


def tu_dong(bat_buoc=False, in_ra=print):
    """Sao lưu hằng tuần lên Google Drive. bat_buoc=True: chạy ngay dù chưa đến hạn / chưa bật."""
    nk = _doc_nk()
    td = dict(nk.get("tu_dong") or {})
    if not bat_buoc and (not td.get("bat") or not _den_han(td)):
        return None
    dich = td.get("dich") or ""
    if not dich:
        d = tim_drive()
        if not d:
            td["loi"] = "Chưa thấy Google Drive cho máy tính trên máy này."
            nk["tu_dong"] = td; _ghi_nk(nk)
            raise ValueError(td["loi"] + " Cài tại https://www.google.com/drive/download/ , đăng nhập rồi bật lại.")
        dich = os.path.join(d[0], "claude", "Sao lưu ngân hàng")
    goc_drive = os.path.dirname(os.path.dirname(dich))
    if not os.path.isdir(goc_drive):
        td["loi"] = "Không thấy thư mục Google Drive: " + goc_drive
        nk["tu_dong"] = td; _ghi_nk(nk)
        raise ValueError(td["loi"] + " (Google Drive cho máy tính đã mở và đăng nhập chưa?)")
    os.makedirs(dich, exist_ok=True)
    try:
        p = tao(dich, de_ra="khong", kem_kho=td.get("kem_kho", True), in_ra=in_ra, ghi_lai=False)
        moi = _guong_de_ra(dich, in_ra)
        in_ra(f"🗂 Thư mục đề trên Drive: chép {moi} file mới / đã đổi")
        bo = []
        giu = int(td.get("giu", 4) or 0)
        if giu > 0:
            cu = sorted(f for f in os.listdir(dich) if re.match(r"SaoLuu_NganHang_\d{4}-\d{2}-\d{2}_\d{4}\.zip$", f))
            for f in cu[:-giu]:
                try:
                    os.remove(os.path.join(dich, f)); bo.append(f)    # Drive đưa vào Thùng rác (khôi phục được 30 ngày)
                except OSError:
                    pass
            if bo:
                in_ra(f"♻ Chỉ giữ {giu} bản zip mới nhất — {len(bo)} bản cũ vào Thùng rác Google Drive")
        td.update({"lan_cuoi": datetime.datetime.now().isoformat(timespec="minutes"), "loi": "", "dich_that": dich,
                   "ket_qua": {"tep": os.path.basename(p), "mb": round(os.path.getsize(p) / 1048576, 1), "de_ra_moi": moi, "bo": len(bo)}})
    except Exception as e:
        td["loi"] = str(e)[:300]
        nk = _doc_nk(); nk["tu_dong"] = td; _ghi_nk(nk)
        raise
    nk = _doc_nk(); nk["tu_dong"] = td; _ghi_nk(nk)
    return td


# ------------------------------------------------------------------ LỊCH CỦA MÁY (chạy cả khi không mở ứng dụng)
NHAN = "vn.nganhangtoan.saoluu"
P_PLIST = os.path.expanduser(f"~/Library/LaunchAgents/{NHAN}.plist")
TEN_TASK = "NganHangToan SaoLuu"


def co_lich():
    if sys.platform == "darwin":
        return os.path.exists(P_PLIST)
    if sys.platform.startswith("win"):
        try:
            return subprocess.run(["schtasks", "/Query", "/TN", TEN_TASK], capture_output=True).returncode == 0
        except Exception:
            return False
    return False


def dat_lich(bat=True):
    """Bật/tắt lịch máy chạy `sao_luu.py --tu-dong` mỗi ngày 12:30 (chỉ thật sự sao lưu khi đủ 7 ngày)."""
    py, sc = sys.executable, os.path.abspath(__file__)
    if sys.platform == "darwin":
        subprocess.run(["launchctl", "unload", P_PLIST], capture_output=True)
        if not bat:
            if os.path.exists(P_PLIST):
                os.remove(P_PLIST)
            return "Đã tắt lịch tự sao lưu của máy."
        os.makedirs(os.path.dirname(P_PLIST), exist_ok=True)
        open(P_PLIST, "w", encoding="utf-8").write(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>{NHAN}</string>
  <key>ProgramArguments</key><array><string>{py}</string><string>{sc}</string><string>--tu-dong</string></array>
  <key>WorkingDirectory</key><string>{GOC}</string>
  <key>StartCalendarInterval</key><dict><key>Hour</key><integer>12</integer><key>Minute</key><integer>30</integer></dict>
  <key>EnvironmentVariables</key><dict><key>PATH</key><string>/Library/TeX/texbin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string></dict>
  <key>StandardOutPath</key><string>/tmp/nganhang_saoluu.log</string><key>StandardErrorPath</key><string>/tmp/nganhang_saoluu.log</string>
</dict></plist>
""")
        r = subprocess.run(["launchctl", "load", P_PLIST], capture_output=True, text=True)
        return "Đã bật lịch: máy kiểm tra mỗi ngày 12:30 (máy ngủ thì chạy khi thức dậy)." + (" ⚠ " + r.stderr.strip() if r.returncode else "")
    if sys.platform.startswith("win"):
        if not bat:
            subprocess.run(["schtasks", "/Delete", "/TN", TEN_TASK, "/F"], capture_output=True)
            return "Đã tắt lịch tự sao lưu của máy."
        pyw = py.replace("python.exe", "pythonw.exe") if py.lower().endswith("python.exe") else py
        r = subprocess.run(["schtasks", "/Create", "/F", "/SC", "DAILY", "/ST", "12:30", "/TN", TEN_TASK,
                            "/TR", f'"{pyw}" "{sc}" --tu-dong'], capture_output=True, text=True)
        return ("Đã bật lịch: máy kiểm tra mỗi ngày 12:30." if r.returncode == 0 else "⚠ Chưa đặt được lịch: " + (r.stderr or r.stdout).strip())
    return "Máy này không hỗ trợ đặt lịch tự động."


HUONG_DAN = """KHÔI PHỤC NGÂN HÀNG CÂU HỎI TOÁN TRÊN MÁY MỚI
=============================================
Bản sao lưu tạo lúc: {luc}  ·  từ máy: {may}

CÁCH NHANH NHẤT
1. Tải file cài đặt từ GitHub (VuTienLuc/NganHangToanTHPT) hoặc chép từ máy cũ:
     • Máy Mac     : "Cai dat tren Mac.command"
     • Máy Windows : "Cai dat tren Windows.bat"
2. Đặt FILE ZIP NÀY (giữ nguyên, không cần giải nén) vào CÙNG THƯ MỤC với file cài đặt.
3. Nhấp đúp file cài đặt. Máy tự: cài phần mềm cần thiết → tải kho từ GitHub (không vào được GitHub thì
   lấy từ kho.bundle trong zip) → chép khoá AI, bí mật thi trực tuyến → chép lại thư mục đề đã xuất.

TRONG FILE ZIP
  bi_mat/ai_khoa.json, bi_mat.json, mat_khau_dau.json  — khoá AI, bí mật thi trực tuyến (GIỮ KÍN, đừng gửi ai)
  de-da-ra/      — đề, phiếu, PDF, Word, Excel đã xuất
  kho.bundle     — toàn bộ ngân hàng + ứng dụng kèm lịch sử (git clone kho.bundle NganHangCaNhan)

LÀM TAY (nếu cần)
  git clone https://github.com/VuTienLuc/NganHangToanTHPT.git NganHangCaNhan
  chép bi_mat/ai_khoa.json            → NganHangCaNhan/ai_khoa.json
  chép bi_mat/bi_mat.json, mat_khau_dau.json → NganHangCaNhan/thi-truc-tuyen/
  chép de-da-ra/                      → NganHangCaNhan/de-da-ra/
"""


def tao(dich=None, de_ra="ket_qua", kem_kho=True, in_ra=print, ghi_lai=True):
    """Tạo file zip sao lưu. de_ra: ket_qua | tat_ca | khong. → đường dẫn file zip."""
    dich = os.path.expanduser(dich or thu_muc_mac_dinh())
    if not os.path.isdir(dich):
        raise ValueError("Không có thư mục: " + dich)
    if os.path.realpath(dich).startswith(os.path.realpath(os.path.join(GOC, "de-da-ra"))):
        raise ValueError("Đừng lưu bản sao lưu vào trong de-da-ra.")
    ten = "SaoLuu_NganHang_" + time.strftime("%Y-%m-%d_%H%M") + ".zip"
    p = os.path.join(dich, ten)
    tam = p + ".dang_tao"
    dem = {"bi_mat": 0, "de_ra": 0, "kho": False}
    with zipfile.ZipFile(tam, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for rel, ten_z in BI_MAT:
            a = os.path.join(GOC, rel)
            if os.path.exists(a):
                z.write(a, "bi_mat/" + ten_z); dem["bi_mat"] += 1
        in_ra(f"🔑 Bí mật: {dem['bi_mat']}/3 file")
        ds = _co_de_ra(de_ra)
        for i, (a, ten_z) in enumerate(ds, 1):
            try:
                if a.lower().endswith((".pdf", ".png", ".jpg", ".zip", ".xlsx", ".docx")):
                    z.write(a, ten_z.replace(os.sep, "/"), compress_type=zipfile.ZIP_STORED)
                else:
                    z.write(a, ten_z.replace(os.sep, "/"))
                dem["de_ra"] += 1
            except OSError as e:                     # file iCloud chưa tải về máy…
                in_ra(f"  ⚠ bỏ qua {ten_z}: {e}")
            if i % 200 == 0:
                in_ra(f"  … {i}/{len(ds)} file đề")
        if de_ra != "khong":
            in_ra(f"🗂 Thư mục đề: {dem['de_ra']} file")
        if kem_kho:
            b = os.path.join(dich, ".kho_tam.bundle")
            ma, out = _git("bundle", "create", b, "--all", timeout=600)
            if ma == 0 and os.path.exists(b):
                z.write(b, "kho.bundle", compress_type=zipfile.ZIP_STORED); dem["kho"] = True
                os.remove(b)
                in_ra("📚 Kho git (ngân hàng + ứng dụng + lịch sử): đã gói kho.bundle")
            else:
                in_ra("  ⚠ Không gói được kho git (" + out[-120:] + ") — vẫn khôi phục được từ GitHub.")
        import platform
        z.writestr("KHOI_PHUC.txt", HUONG_DAN.format(luc=time.strftime("%d/%m/%Y %H:%M"), may=platform.node() or "?"))
    os.replace(tam, p)
    mb = round(os.path.getsize(p) / 1048576, 1)
    if ghi_lai:
        d = _doc_nk()
        d["lan_truoc"] = {"luc": datetime.datetime.now().isoformat(timespec="minutes"), "tep": p, "mb": mb, **dem}
        _ghi_nk(d)
    in_ra(f"✅ Đã tạo {ten} ({mb} MB) trong {dich}")
    return p


if __name__ == "__main__":
    import argparse
    a = argparse.ArgumentParser(description="Sao lưu những gì GitHub không giữ (khoá AI, bí mật, de-da-ra, kho git).")
    a.add_argument("--dich", help="thư mục lưu file zip (mặc định: Desktop)")
    a.add_argument("--de-ra", default="ket_qua", choices=["ket_qua", "tat_ca", "khong"])
    a.add_argument("--khong-kho", action="store_true")
    a.add_argument("--xem", action="store_true", help="chỉ xem tình trạng")
    a.add_argument("--tu-dong", action="store_true", help="sao lưu lên Google Drive nếu đã bật và đủ 7 ngày (dùng cho lịch của máy)")
    a.add_argument("--ngay", action="store_true", help="kèm --tu-dong: chạy ngay, không chờ đủ 7 ngày")
    g = a.parse_args()
    if g.tu_dong:
        try:
            r = tu_dong(bat_buoc=g.ngay)
            print(time.strftime("%Y-%m-%d %H:%M"), "chưa đến hạn / chưa bật" if r is None else "xong")
        except Exception as e:
            print(time.strftime("%Y-%m-%d %H:%M"), "LỖI:", e)
            sys.exit(1)
    elif g.xem:
        print(json.dumps(tinh_trang(), ensure_ascii=False, indent=1))
    else:
        tao(g.dich, g.de_ra, not g.khong_kho)
