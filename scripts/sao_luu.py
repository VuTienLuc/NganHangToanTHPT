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
    try:
        t["lan_truoc"] = json.load(open(P_NK, encoding="utf-8"))
    except Exception:
        t["lan_truoc"] = None
    return t


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


def tao(dich=None, de_ra="ket_qua", kem_kho=True, in_ra=print):
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
    nk = {"luc": datetime.datetime.now().isoformat(timespec="minutes"), "tep": p, "mb": mb, **dem}
    try:
        json.dump(nk, open(P_NK, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    except OSError:
        pass
    in_ra(f"✅ Đã tạo {ten} ({mb} MB) trong {dich}")
    return p


if __name__ == "__main__":
    import argparse
    a = argparse.ArgumentParser(description="Sao lưu những gì GitHub không giữ (khoá AI, bí mật, de-da-ra, kho git).")
    a.add_argument("--dich", help="thư mục lưu file zip (mặc định: Desktop)")
    a.add_argument("--de-ra", default="ket_qua", choices=["ket_qua", "tat_ca", "khong"])
    a.add_argument("--khong-kho", action="store_true")
    a.add_argument("--xem", action="store_true", help="chỉ xem tình trạng")
    g = a.parse_args()
    if g.xem:
        print(json.dumps(tinh_trang(), ensure_ascii=False, indent=1))
    else:
        tao(g.dich, g.de_ra, not g.khong_kho)
