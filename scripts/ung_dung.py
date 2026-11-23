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

def nhap_tuong_tu_va_tao_phieu(t, cfg, so, vi_du_mau, bien_dich, nguon="Câu tương tự theo mẫu – AI soạn, nhập từ ứng dụng (Phiếu bài học)"):
    """Câu tương tự theo mẫu (LaTeX, có dòng % mau:) → ai-nhap → nhập kho (biên dịch thử từng câu) → tạo phiếu riêng theo mẫu."""
    import nhap_cau
    ten_tep_ai = time.strftime("%Y-%m-%d_%H%M%S") + "_tuong-tu-theo-mau.tex"
    p = os.path.join(GOC, "ai-nhap", ten_tep_ai)
    open(p, "w", encoding="utf-8").write("% " + nguon + "\n" + t + "\n")
    dong = []
    try:
        so_cau = nhap_cau.nhap([p], thu=False, in_ra=dong.append)
    except Exception as e:
        return {"ok": False, "nhat_ky": f"Chưa nhập được: {e}\n" + "\n".join(dong)}
    os.makedirs(os.path.join(GOC, "ai-nhap", "da-nhap"), exist_ok=True)
    try:
        shutil.move(p, os.path.join(GOC, "ai-nhap", "da-nhap", ten_tep_ai))
    except OSError:
        pass
    cfg.update(theo_mau=True, so_tuong_tu=int(so or cfg.get("so_tuong_tu") or 3), so_van_dung=0, vi_du_mau=vi_du_mau or cfg.get("vi_du_mau") or {})
    dong.append(f"→ Đã nhập {so_cau} câu vào ngân hàng.\n")
    try:
        if cfg.get("kieu_cau") == "luyen_ngay":
            import luyen_moi_ngay
            out_goc = luyen_moi_ngay.tao(cfg, dong.append)
        else:
            import phieu_bai_hoc
            cfg["kieu_cau"] = "tu_luan"
            out_goc = phieu_bai_hoc.tao(cfg, dong.append)
    except Exception as e:
        return {"ok": False, "so_cau": so_cau, "nhat_ky": "\n".join(dong) + f"\nChưa tạo được phiếu: {e}"}
    rel = os.path.relpath(out_goc, GOC)
    dang_bd = bool(bien_dich and tim_pdflatex())
    if dang_bd:
        threading.Thread(target=bien_dich_nen, args=(rel,), daemon=True).start()
    return {"ok": True, "so_cau": so_cau, "thu_muc": rel, "bien_dich": dang_bd,
            "nhat_ky": "\n".join(x for x in dong if not x.startswith("THU_MUC:") and not x.startswith("   +"))}


def tu_sinh_nen(d):
    """Chạy nền cho /api/tu-sinh: nhật kí từng bước vào cong_viec, kết quả cuối ở cong_viec["ket_qua"]."""
    import random as _rd, sinh_tuong_tu as ST
    def ghi(x):
        cong_viec["nhat_ky"] += x + "\n"
    ra = {"ok": False}
    try:
        cfg = dict(d.get("cau_hinh") or {})
        so = max(1, min(8, int(d.get("so") or 3))); kieu = d.get("kieu") or "giong"; cach = d.get("cach") or "python"
        rng = _rd.Random(cfg.get("seed") or time.time())
        khoi, vdm = [], {}
        if cach in ("python", "python_ai"):
            ghi("🐍 Python (đổi số liệu, tính lại lời giải):")
            t_py, vd_py, nk_py = ST.sinh_python(cfg, so, kieu, rng)
            for x in nk_py:
                ghi(x)
            if t_py:
                khoi.append(t_py)
            vdm.update(vd_py)
        if cach == "khuon":                       # 🧬 khuôn câu: AI viết khuôn 1 lần / mẫu, Python sinh & kiểm chứng
            import luyen_moi_ngay, khuon_cau as KC
            kq, cac_dang, _ = luyen_moi_ngay.chon(dict(cfg, so_tuong_tu=0, so_van_dung=0, theo_mau=False), rng)
            ds_ma = [kq[k]["vd"]["ma"] for k in cac_dang if k in kq]
            n_nc = so if kieu == "nang_cao" else (1 if kieu == "giong_nc" and so > 1 else 0)
            ghi(f"🧬 Khuôn câu cho {len(ds_ma)} mẫu ({so - n_nc} giống mẫu + {n_nc} nâng cao mỗi mẫu; mọi câu đều được tính lại đáp án):")
            kb, vd_k, tk = KC.sinh(ds_ma, so - n_nc, n_nc, ghi, seed=rng.randrange(1 << 30))
            khoi += kb; vdm.update(vd_k)
            ghi(f"   → {tk['cau']} câu từ {tk['mau']} khuôn ({tk['khuon_moi']} khuôn mới, {tk['khuon_cu']} khuôn dùng lại)"
                + (f"; {len(tk['bo'])} mẫu chưa làm khuôn được: {', '.join(tk['bo'])}" if tk["bo"] else ""))
        if cach in ("ai", "python_ai"):
            import luyen_moi_ngay
            kq, cac_dang, _ = luyen_moi_ngay.chon(dict(cfg, so_tuong_tu=0, so_van_dung=0, theo_mau=False), rng)
            con_lai = [k for k in cac_dang if k not in vdm]
            if con_lai:
                id_map = tai_id_map()
                mau = [{"ma": kq[k]["vd"]["ma"], "dang_key": k, "muc": kq[k]["vd"].get("muc_chuan") or "H",
                        "ten_dang": (id_map.get(k, {}).get("type_name") or "").strip(), "ten_bai": (id_map.get(k, {}).get("lesson_name") or "").strip(),
                        "de": kq[k]["vd"]["_tl"]["de"], "lg": kq[k]["vd"]["_tl"]["lg"]} for k in con_lai]
                ghi(f"🤖 AI soạn {len(mau)} mẫu (mỗi lượt một mẫu; bị ngắt / thiếu → tự hỏi tiếp; khoá hết lượt → đổi khoá):")
                try:
                    hd, xoay = None, None
                    if d.get("hoi_dong"):
                        import hoi_dong_ai as HD
                        hd = HD.HoiDong(ghi=ghi); hd.gioi_thieu(); xoay = hd.xoay("soan")
                    kb, vd_ai = ST.sinh_ai(mau, so, kieu, lop_tu_so(con_lai[0][0]), ghi, xoay=xoay, hoi_dong=hd)
                    khoi += kb; vdm.update(vd_ai)
                except ST.HetKhoa as e:
                    if cach == "ai" and not khoi:
                        raise
                    ghi(f"  ⚠ {e} — giữ các câu đã sinh.")
        if not khoi:
            raise RuntimeError("Chưa sinh được câu nào. Thầy thử cách khác hoặc 📝 Prompt AI (chép – dán).")
        ghi("\n📥 Nhập ngân hàng và tạo phiếu…")
        ra = nhap_tuong_tu_va_tao_phieu("\n\n".join(khoi), cfg, so, vdm, False,
                                        "Ngân hàng tự sinh (" + {"python": "Python", "ai": "AI", "python_ai": "Python + AI", "khuon": "Khuôn câu"}.get(cach, cach)
                                        + (" · Hội đồng AI" if d.get("hoi_dong") and cach != "python" else "") + ")")
        ghi(ra.get("nhat_ky", ""))
        if ra.get("ok") and d.get("bien_dich") and tim_pdflatex():
            ghi("Biên dịch PDF…")
            bien_dich_thu_muc(os.path.join(GOC, ra["thu_muc"]), ghi)
    except Exception as e:
        ghi(f"Lỗi: {e}")
        ra = {"ok": False}
    ra["nhat_ky"] = cong_viec["nhat_ky"]
    cong_viec.update(dang_chay=False, xong=True, ket_qua=ra)


def ai_loi_sai_nen(d):
    """🤖 AI tạo lời giải có lỗi (vai Tổng biên tập — cẩn thận nhất) cho phiếu Tìm lỗi sai → kho lỗi sai."""
    def ghi(x):
        cong_viec["nhat_ky"] += x + "\n"
    ra = {"ok": False}
    try:
        import phieu_hoat_dong as H, hoi_dong_ai as HD
        vai = HD.phan_vai()
        if not vai:
            raise RuntimeError("Chưa có khoá API AI — bấm ⚙ Khoá AI… hoặc dùng 📝 Prompt AI (chép – dán).")
        nha = vai.get("bien_tap")
        p, n = H.prompt_loi(d.get("dang") or [], int(d.get("so") or 4))
        ghi(f"🤖 {HD.ST.TEN_NHA.get(nha, nha)} viết {n} lời giải có lỗi từ câu gốc trong ngân hàng…")
        t, _, _ = HD.xoay_cho("bien_tap", nha, ghi=ghi).goi(p)
        so, bo = H.nhap_loi(t)
        for x in bo:
            ghi("  ⚠ bỏ " + x)
        ghi(f"✓ Đã thêm {so} bài vào kho lỗi sai.")
        ra = {"ok": True, "so": so}
    except Exception as e:
        ghi(f"Lỗi: {e}")
    ra["nhat_ky"] = cong_viec["nhat_ky"]
    cong_viec.update(dang_chay=False, xong=True, ket_qua=ra)


def khuon_nen(d):
    """🧬 Song sinh: các câu chỉ định → khuôn (dùng lại / AI viết) → N câu giống + M nâng cao, đã kiểm chứng → nhập kho."""
    def ghi(x):
        cong_viec["nhat_ky"] += x + "\n"
    ra = {"ok": False}
    try:
        import khuon_cau as KC, nhap_cau
        ds_ma = [m for m in (d.get("ma") or []) if re.fullmatch(r"[0-9a-f]{8}", m or "")]
        so = max(0, min(30, int(d.get("so") or 5))); so_nc = max(0, min(15, int(d.get("so_nc") or 0)))
        if not ds_ma or not (so or so_nc):
            raise RuntimeError("Chưa chọn câu mẫu hoặc số câu.")
        ghi(f"🧬 Khuôn câu: {len(ds_ma)} mẫu × ({so} giống + {so_nc} nâng cao)")
        kb, vdm, tk = KC.sinh(ds_ma, so, so_nc, ghi, viet_lai=bool(d.get("viet_lai")))
        if not kb:
            raise RuntimeError("Chưa sinh được câu nào." + (f" Mẫu chưa làm khuôn được: {', '.join(tk['bo'])}" if tk["bo"] else ""))
        ten = time.strftime("%Y-%m-%d_%H%M%S") + "_khuon_cau.tex"
        p = os.path.join(GOC, "ai-nhap", ten)
        open(p, "w", encoding="utf-8").write("% Khuôn câu — câu song sinh có kiểm chứng\n\n" + "\n\n".join(kb) + "\n")
        ghi(f"\n📥 Biên dịch thử & nhập {len(kb)} câu vào ngân hàng…")
        so_cau = nhap_cau.nhap([p], thu=False, in_ra=ghi)
        os.makedirs(os.path.join(GOC, "ai-nhap", "da-nhap"), exist_ok=True)
        try:
            shutil.move(p, os.path.join(GOC, "ai-nhap", "da-nhap", ten))
        except OSError:
            pass
        ghi(f"\n✓ Đã nhập {so_cau}/{len(kb)} câu song sinh (câu lỗi nếu có ở ai-nhap/_loi/).")
        ra = {"ok": True, "so_cau": so_cau, "tong_sinh": len(kb), "khuon_moi": tk["khuon_moi"], "bo": tk["bo"]}
    except Exception as e:
        ghi(f"Lỗi: {e}")
    ra["nhat_ky"] = cong_viec["nhat_ky"]
    cong_viec.update(dang_chay=False, xong=True, ket_qua=ra)


def _tach_khoi_hk(t, mt_env, loai="TN"):
    """Tách các khối \\begin{ex|bt}…\\end{ex|bt} hoàn chỉnh từ phản hồi AI.
    Với TLN: hỗ trợ AI viết \\loigiai trước \\shortans (để giải xong mới chốt đáp số, tránh đoán mò sai),
    sau đó tự chuyển \\shortans về đúng vị trí trước \\loigiai và hậu kiểm cơ bản."""
    t = re.sub(r"```(?:latex|tex)?", "", t or "")
    pat = re.compile(r"\\begin\{(ex|bt)\}.*?\\end\{\1\}", re.S)
    ra = []
    for m in pat.finditer(t):
        k = m.group(0).strip()
        if "\\loigiai" not in k:
            continue
        if loai == "TLN":
            ms = re.search(r"\\shortans(?:\[[^\]]*\])?\{([^{}]+)\}", k)
            if not ms:
                continue
            ds_raw = ms.group(1).strip().replace("$", "").replace("{,}", ",").replace(" ", "").replace(".", ",")
            if not ds_raw or len(ds_raw) > 4:
                continue
            # Nếu AI viết \shortans sau \loigiai (do prompt yêu cầu giải trước), đưa về đúng vị trí trước \loigiai
            pos_lg = k.find("\\loigiai")
            if ms.start() > pos_lg:
                k = k[:ms.start()] + k[ms.end():]
                pos_lg = k.find("\\loigiai")
                k = k[:pos_lg] + f"\\shortans{{{ds_raw}}}\n\t" + k[pos_lg:]
            else:
                k = k[:ms.start()] + f"\\shortans{{{ds_raw}}}" + k[ms.end():]
            # Hậu kiểm: đáp số (dạng số không dấu cách) phải xuất hiện trong lời giải (tránh AI đoán mò lệch lời giải)
            lg_txt = k[k.find("\\loigiai"):].replace("{,}", ",").replace("\\,", "").replace(" ", "")
            so_kiem = ds_raw.lstrip("-")
            if so_kiem and (so_kiem not in lg_txt and so_kiem.replace(",", ".") not in lg_txt):
                continue
        than = k[k.find("\\loigiai"):]
        if than.count("{") != than.count("}"):
            continue
        k = re.sub(r"^\\begin\{(ex|bt)\}", rf"\\begin{{{mt_env}}}", k, count=1)
        k = re.sub(r"\\end\{(ex|bt)\}$", rf"\\end{{{mt_env}}}", k, count=1)
        k, _ = chuan_vecto(k)
        ra.append(k)
    return ra


MO_TA_MUC_HK = {
    "NB": (
        "NHẬN BIẾT (mức 1): 1 bước trực tiếp, nhận diện khái niệm, công thức, tính chất cơ bản hoặc đọc trực tiếp từ đề bài."
    ),
    "TH": (
        "THÔNG HIỂU (mức 2): 2–3 bước biến đổi quen thuộc, kết hợp 2 kiến thức cơ bản trong bài; không quá dễ kiểu 1 phép tính nhưng chưa quá lắt léo."
    ),
    "VD": (
        "VẬN DỤNG (mức 3 — câu phân hoá 8–9 điểm):\n"
        "  • BẮT BUỘC cần TỐI THIỂU 3–4 bước suy luận/tính toán liên kết nhau (ví dụ: đặt ẩn/tọa độ → lập phương trình hoặc điều kiện hình học → giải tìm đại lượng trung gian → tính kết quả cuối cùng).\n"
        "  • Ưu tiên: bài toán THỰC TẾ cần mô hình hoá (tọa độ, vectơ, quỹ đạo, tối ưu chi phí/diện tích/lực/vận tốc), HOẶC bài toán tham số, tìm điểm thoả mãn điều kiện hình học–đại số, kết hợp nhiều kiến thức.\n"
        "  • CẤM TUYỆT ĐỐI câu 1–2 bước kiểu chỉ thay số vào công thức (như chỉ tính trực tiếp tích vô hướng hai vectơ cho sẵn, chỉ tính độ dài đoạn thẳng AB, chỉ giải một phương trình bậc nhất đơn giản). Nếu câu nháp quá dễ phải tự nâng cấp ngay trước khi xuất."
    ),
    "VDC": (
        "VẬN DỤNG CAO (mức 4 — câu phân hoá 9,5–10 điểm):\n"
        "  • BẮT BUỘC là bài toán sâu, nhiều bước (≥ 4–5 bước): cực trị hình học/đại số, bài toán tối ưu thực tế phức tạp, biện luận đa điều kiện hoặc kết hợp nhiều chủ đề.\n"
        "  • CẤM TUYỆT ĐỐI câu dễ hoặc câu thông hiểu."
    ),
}


def _prompt_hk_ai(lop, it, thieu, ds_ma, da_de, ten_chuong="", ten_bai=""):
    loai = it.get("loai") or "TN"
    muc_code = it.get("muc") or "TH"
    muc_ten = {"NB": "Nhận biết", "TH": "Thông hiểu", "VD": "Vận dụng", "VDC": "Vận dụng cao"}.get(muc_code, "Thông hiểu")
    mt_env = "ex" if loai in ("TN", "DS") else "bt"
    if loai == "TN":
        quy_tac = (
            f"- Môi trường `\\begin{{ex}}%[MÃ_DẠNG]` … `\\end{{ex}}`, dùng `\\choice{{PA1}}{{PA2}}{{PA3}}{{PA4}}`.\n"
            "- Đúng MỘT phương án đúng đánh dấu `\\True` ở đầu ngoặc nhọn (vd `{\\True $3$}`). Không ghi A., B., C., D.\n"
            "- Trong `\\loigiai{...}` KHÔNG ghi 'Chọn A' hay 'Đáp án B'."
        )
    elif loai == "DS":
        quy_tac = (
            f"- Môi trường `\\begin{{ex}}%[MÃ_DẠNG]` … `\\end{{ex}}`, dùng `\\choiceTF{{y1}}{{y2}}{{y3}}{{y4}}`.\n"
            "- Ý đúng đánh dấu `\\True` ở đầu ngoặc nhọn; độ khó tăng dần từ ý 1 đến ý 4 (ý 4 khó nhất, mang tính phân hoá).\n"
            "- Trong `\\loigiai{...}` dùng `\\begin{itemchoice}` đủ 4 `\\itemch`, mỗi ý mở đầu 'Đúng.' hoặc 'Sai.'; không nhắc 'ý a', 'b)'."
        )
    elif loai == "TLN":
        quy_tac = (
            f"- Môi trường `\\begin{{bt}}%[MÃ_DẠNG]` … `\\end{{bt}}`.\n"
            "- BẮT BUỘC viết `\\loigiai{...}` TRƯỚC để giải trọn vẹn từng bước và tính ra đáp số chính xác, SAU ĐÓ mới viết `\\shortans{đáp số}` ngay trước `\\end{bt}` (để đáp số khớp 100% với lời giải, tuyệt đối không đoán mò).\n"
            "- Đáp số trong `\\shortans{...}` là số tối đa 4 ký tự (kể cả dấu - và dấu phẩy thập phân, vd `2,5`, `-12`, `47,1`). Nếu kết quả lẻ, ĐỀ BÀI phải nêu rõ quy tắc làm tròn (vd: làm tròn đến hàng phần mười) và đáp số làm tròn đúng quy tắc đó."
        )
    else:
        quy_tac = (
            f"- Môi trường `\\begin{{bt}}%[MÃ_DẠNG]` … `\\end{{bt}}` (KHÔNG có `\\shortans`), lời giải `\\loigiai{{...}}` đủ từng bước rõ ràng."
        )
    goi_ma = "\n".join(f"  - {ma}: {ten}" for ma, ten in ds_ma)
    da_dang = ""
    if thieu > 1:
        goc_kho = [
            "Bài toán THỰC TẾ / LIÊN MÔN (vật lí, kỹ thuật, xây dựng, kinh tế, chuyển động, đo đạc, tối ưu chi phí/diện tích/quỹ đạo — mô hình hoá sang Toán).",
            "Bài toán THAM SỐ / TÌM ĐIỂM / BIỆN LUẬN thoả mãn điều kiện hình học–đại số (vuông góc, thẳng hàng, cách đều, góc, đối xứng, ràng buộc miền).",
            "Bài toán CỰC TRỊ / TỐI ƯU (giá trị lớn nhất – nhỏ nhất, bất đẳng thức, tâm tỉ cự, hình học tối ưu, tam thức bậc hai).",
            "Bài toán TỔNG HỢP / TƯ DUY NGƯỢC (cho kết quả ngược tìm dữ kiện, kết hợp 2–3 định lí/tính chất khác nhau trong bài).",
            "Bài toán ĐỌC / KHAI THÁC ĐỒ THỊ, BẢNG SỐ LIỆU hoặc HÌNH HỌC PHỐI HỢP nhiều bước.",
        ]
        if muc_code in ("VD", "VDC"):
            phan_bo = "\n".join(
                f"  - Câu {i + 1}: {goc_kho[i % len(goc_kho)]}"
                + (f" (ưu tiên mã dạng `{ds_ma[i % len(ds_ma)][0]}`)" if len(ds_ma) > 1 else "")
                for i in range(thieu)
            )
            da_dang = (
                "\nYÊU CẦU ĐA DẠNG CÂU HỎI KHÓ (BẮT BUỘC — SÁNG TẠO KHÁC NHAU, KHÔNG RẬP KHUÔN MẪU):\n"
                "- CẤM TUYỆT ĐỐI sinh nhiều câu cùng một khuôn/ý tưởng rồi chỉ thay số liệu! Không nhất thiết giống câu mẫu có sẵn.\n"
                "- Hãy xoay quanh đúng Lớp, Tên bài, Chủ đề và các Dạng toán bên dưới, mỗi câu khai thác một hướng tư duy, bối cảnh và phương pháp giải KHÁC NHAU:\n"
                + phan_bo + "\n"
            )
        else:
            da_dang = (
                "\nYÊU CẦU ĐA DẠNG (BẮT BUỘC — KHÔNG RẬP KHUÔN MẪU):\n"
                "- Hãy sáng tạo ĐA DẠNG các câu hỏi mới xoay quanh đúng Lớp, Tên bài, Chủ đề và các Dạng toán bên dưới — KHÔNG nhất thiết giống mẫu, KHÔNG sinh các câu na ná nhau chỉ thay số liệu.\n"
                + (f"- Phân bổ đều qua các mã dạng khác nhau trong danh sách CÁC DẠNG TOÁN THUỘC BÀI.\n" if len(ds_ma) > 1 else "")
            )
    thang_muc = (
        "QUY ƯỚC 4 MỨC ĐỘ NHẬN THỨC (BẮT BUỘC PHÂN BIỆT RÕ):\n"
        "- NB = Nhận biết (mức 1): nhận diện khái niệm, định lí, công thức cơ bản hoặc tính trực tiếp 1 bước.\n"
        "- TH = Thông hiểu (mức 2): hiểu bản chất, biến đổi 2–3 bước quen thuộc, kết hợp 2 kiến thức cơ bản trong bài.\n"
        "- VD = Vận dụng (mức 3 — câu 8–9 điểm): bài toán ≥ 3–4 bước suy luận liên kết (mô hình hoá thực tế, tham số, tìm điểm, kết hợp nhiều tính chất).\n"
        "- VDC = Vận dụng cao (mức 4 — câu 9,5–10 điểm): bài toán phân hoá sâu ≥ 4–5 bước (cực trị, tối ưu phức tạp, biện luận đa điều kiện).\n"
    )
    p = (
        f"Bạn là giáo viên Toán THPT/THCS giỏi luyện thi học sinh giỏi và đề thi chuẩn GDPT 2018 (sách Kết nối tri thức). "
        f"Hãy soạn ĐÚNG {thieu} câu hỏi Toán Lớp {lop}, mức độ **{muc_code} ({muc_ten})**.\n\n"
        + thang_muc + "\n"
        f"YÊU CẦU CỤ THỂ CHO MỨC ĐANG SOẠN — {muc_code} ({muc_ten}):\n{MO_TA_MUC_HK.get(muc_code, MO_TA_MUC_HK['TH'])}\n"
        + da_dang + "\n"
        f"PHẠM VI KIẾN THỨC (SOẠN CÂU XOAY QUANH ĐÚNG BÀI & CHỦ ĐỀ NÀY, ĐA DẠNG CÁC DẠNG TOÁN KHÁC NHAU):\n"
        f"- Lớp: Toán Lớp {lop} (SGK Kết nối tri thức)\n"
        + (f"- Chương: {ten_chuong}\n" if ten_chuong else "")
        + (f"- Tên bài: {ten_bai}\n" if ten_bai else "")
        + f"- Chủ đề trọng tâm: {it.get('chu_de') or ''}\n"
        + (f"- Ngữ cảnh thực tế gợi ý: {it.get('ngu_canh')}\n" if it.get("ngu_canh") else "")
        + (f"- Tham khảo thêm của giáo viên (chỉ tham khảo phạm vi & tầm độ khó, tự do sáng tạo đa dạng câu hỏi khác nhau, KHÔNG nhất thiết giống khuôn mẫu):\n{it.get('mau')}\n" if it.get("mau") else "")
        + f"\nCÁC DẠNG TOÁN & MÃ DẠNG HỢP LỆ THUỘC BÀI NÀY (chọn đúng 1 mã ghi ngay sau `\\begin{{{mt_env}}}`):\n{goi_ma}\n\n"
        f"QUY TẮC ĐỊNH DẠNG LATEX NGÂN HÀNG (BẮT BUỘC):\n{quy_tac}\n"
        "- Công thức toán đặt trong `$...$` hoặc `$$...$$` (KHÔNG dùng `\\(` `\\[`; vectơ dùng `\\overrightarrow{AB}`, KHÔNG dùng `\\vec`; cung tròn dùng `\\overset{\\frown}{AB}`, KHÔNG dùng `\\wideparen`).\n"
        "- Số thập phân trong công thức viết `15{,}25`. Không dùng Markdown (`**`, `#`) trong khối LaTeX.\n"
        "- BẮT BUỘC tự giải lại kiểm tra từng phép tính, đáp số khớp 100% với lời giải trước khi xuất.\n"
        "- CHỈ trả về các khối LaTeX `\\begin{" + mt_env + "}...\\end{" + mt_env + "}`, không viết lời dẫn thừa.\n"
    )
    if da_de:
        p += "\nKHÔNG LẶP LẠI các đề bài đã có sau (soạn câu MỚI khác hẳn kiểu bài và số liệu):\n" + "\n".join("- " + d[:150] for d in list(da_de)[:12])
    return p


def hk_sinh_ai_nen(d):
    """Chạy nền cho /api/hk-sinh-ai: dùng chung khoá AI (ai_khoa.json) sinh câu thiếu/ít ở Ôn thi HK và nhập thẳng vào ngân hàng."""
    import sinh_tuong_tu as ST, nhap_cau
    def ghi(x):
        cong_viec["nhat_ky"] += x + "\n"
    ra = {"ok": False}
    try:
        lop = int(d.get("lop") or 12)
        muc_tieu = [x for x in (d.get("muc_tieu") or []) if int(x.get("so_sinh") or 0) > 0]
        if not muc_tieu:
            raise RuntimeError("Chưa chọn dòng nào để AI sinh câu.")
        id_map = tai_id_map()
        hd = None
        if d.get("hoi_dong"):                             # Hội đồng AI: vai Soạn dùng hãng được phân, rồi giải – phản biện – biên tập
            import hoi_dong_ai as HD
            hd = HD.HoiDong(ghi=ghi)
            hd.gioi_thieu()
            xoay = hd.xoay("soan")
        else:
            xoay = ST.XoayKhoa(ghi=ghi)
        nhan = d.get("nhan") or f"Ôn thi HK Lớp {lop}"
        muc_map = {"NB": "N", "TH": "H", "VD": "V", "VDC": "C"}
        muc_ten_map = {"NB": "Nhận biết", "TH": "Thông hiểu", "VD": "Vận dụng", "VDC": "Vận dụng cao"}
        tat_ca = []
        ghi(f"🤖 AI sinh câu cho {nhan} ({len(muc_tieu)} mục · tổng {sum(int(x.get('so_sinh') or 1) for x in muc_tieu)} câu)…")
        for idx, it in enumerate(muc_tieu, 1):
            lop_i = int(it.get("lop") or lop)
            loai = it.get("loai") or "TN"
            muc_code = it.get("muc") or "TH"
            muc_ma = muc_map.get(muc_code, "H")
            so_can = max(1, min(15, int(it.get("so_sinh") or 3)))
            mt_env = "ex" if loai in ("TN", "DS") else "bt"
            bai = (it.get("bai") or "").strip()
            ds_ma, ten_chuong, ten_bai = [], "", ""
            if bai:
                if "-" in bai and bai in id_map:
                    v = id_map[bai]
                    ten_chuong = (v.get("chap_name") or "").strip()
                    ten_bai = (v.get("lesson_name") or "").strip()
                    ds_ma.append((bai.replace("?", muc_ma), (v.get("type_name") or bai).strip()))
                elif re.fullmatch(r"\d[DHC][0-9A-Z]\?\d+-\d+", bai) and it.get("ten_dang"):   # dạng có trong mục lục SGK nhưng chưa có trong id_map
                    ten_chuong, ten_bai = it.get("ten_chuong") or "", it.get("ten_bai") or ""
                    ds_ma.append((bai.replace("?", muc_ma), it["ten_dang"]))
                else:
                    for k, v in id_map.items():
                        if k == bai or k.startswith(bai + "-"):
                            if not ten_chuong:
                                ten_chuong = (v.get("chap_name") or "").strip()
                            if not ten_bai:
                                ten_bai = (v.get("lesson_name") or "").strip()
                            ds_ma.append((k.replace("?", muc_ma), (v.get("type_name") or k).strip()))
            if not ds_ma:                                 # không đoán mã (vd 0D1?1-1 = Mệnh đề) → câu sẽ lạc chương; bỏ qua mục này
                ghi(f"  [{idx}/{len(muc_tieu)}] ⚠ Bỏ qua «{it.get('chu_de') or '(chưa đặt tên)'}»: chưa có mã bài/dạng hợp lệ"
                    f"{' (' + bai + ')' if bai else ''} — thầy chọn mã bài cho dòng này rồi sinh lại.")
                continue
            ma_mac_dinh = ds_ma[0][0]
            ghi(f"  [{idx}/{len(muc_tieu)}] {loai} · {muc_code} ({muc_ten_map.get(muc_code, muc_code)}) · {ten_bai or it.get('chu_de') or bai} → cần {so_can} câu đa dạng ({len(ds_ma)} dạng)")
            co, da_de = [], set()
            for lan in range(4):
                thieu = so_can - len(co)
                if thieu <= 0:
                    break
                p = _prompt_hk_ai(lop_i, it, thieu, ds_ma[:10], da_de, ten_chuong=ten_chuong, ten_bai=ten_bai)
                try:
                    t, cat, k = xoay.goi(p)
                except ST.HetKhoa as e:
                    if not tat_ca and not co:
                        raise
                    ghi(f"  ⚠ {e} — giữ các câu đã sinh được.")
                    break
                except Exception as e:                    # lỗi lạ của một lượt (mạng, JSON…) → thử lượt sau
                    ghi(f"  ⚠ {str(e)[:120]}")
                    continue
                moi = 0
                for kb in _tach_khoi_hk(t, mt_env, loai=loai):
                    dong0 = kb.split("\n", 1)[0]
                    if "%[" not in dong0:
                        kb = re.sub(r"^(\\begin\{(?:ex|bt)\})", rf"\1%[{ma_mac_dinh}]", kb, count=1)
                    if "% nguon:" not in kb:
                        kb = re.sub(r"^(\\begin\{(?:ex|bt)\}[^\n]*\n)", r"\1% nguon: AI tự sinh (Ôn thi HK)\n", kb, count=1)
                    de = re.sub(r"\s+", " ", re.sub(r"^\\begin\{(?:ex|bt)\}[^\n]*\n", "", kb).split("\\loigiai")[0]).strip()
                    if not de or de in da_de or len(co) >= so_can:
                        continue
                    da_de.add(de); co.append(kb); moi += 1
                ghi(f"    lượt {lan + 1} ({ST.TEN_NHA.get(k['nha'], k['nha'])} {ST.che(k['khoa'])}): +{moi} câu đạt kiểm tra"
                    + (" · bị ngắt → hỏi tiếp" if cat else "") + f" · có {len(co)}/{so_can}")
            if hd and co:
                co = hd.duyet(co, ngu_canh=f"Toán lớp {lop_i}, {ten_chuong} — {ten_bai}; chủ đề: {it.get('chu_de') or ''}; loại {loai}", muc=muc_code)
            tat_ca += co
        if hd:
            tk = hd.thong_ke
            ghi(f"\n🧑‍⚖️ Hội đồng: {tk['vao']} câu soạn → {tk['dat']} đạt ngay · {tk['sua']} đã sửa · {tk['loai']} bị loại")
        if not tat_ca:
            raise RuntimeError("AI chưa sinh được câu hợp lệ nào. Thầy kiểm tra lại ⚙ Khoá AI…")
        os.makedirs(os.path.join(GOC, "ai-nhap"), exist_ok=True)
        ten_tep = time.strftime("%Y-%m-%d_%H%M%S") + (f"_hoi_dong_ai_lop{lop}.tex" if hd else f"_hk_ai_lop{lop}.tex")
        duong_dan = os.path.join(GOC, "ai-nhap", ten_tep)
        open(duong_dan, "w", encoding="utf-8").write(f"% AI tự sinh cho {nhan}\n\n" + "\n\n".join(tat_ca) + "\n")
        ghi(f"\n📥 Biên dịch thử & nhập {len(tat_ca)} câu vào ngân hàng…")
        so_cau = nhap_cau.nhap([duong_dan], thu=False, in_ra=ghi)
        os.makedirs(os.path.join(GOC, "ai-nhap", "da-nhap"), exist_ok=True)
        try:
            shutil.move(duong_dan, os.path.join(GOC, "ai-nhap", "da-nhap", ten_tep))
        except OSError:
            pass
        ghi(f"\n✓ Hoàn tất: đã nhập {so_cau}/{len(tat_ca)} câu hợp lệ vào ngân hàng (câu lỗi nếu có đã tách vào ai-nhap/_loi/).")
        ra = {"ok": True, "so_cau": so_cau, "tong_sinh": len(tat_ca)}
    except Exception as e:
        ghi(f"Lỗi: {e}")
        ra = {"ok": False}
    ra["nhat_ky"] = cong_viec["nhat_ky"]
    cong_viec.update(dang_chay=False, xong=True, ket_qua=ra)


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
    # Lớp 4, 5 (tư duy theo SGK KNTT), 8, 9 (SGK KNTT): hiện đủ mục lục kể cả dạng chưa có câu (= 0)
    for ten_f in ("toan4_tuduy", "toan5_tuduy", "toan8_kntt", "toan9_kntt"):
        try:
            src = json.load(open(os.path.join(GOC, "du-lieu", f"{ten_f}.json"), encoding="utf-8"))
        except Exception:
            continue
        for ch_ in src.get("chuong", []):
            for b in ch_.get("bai", []):
                for j in range(1, len(b.get("dang", [])) + 1):
                    kho[f"{ch_['ma']}?{b['so']}-{j}"]          # defaultdict: tạo ô rỗng nếu chưa có
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


def de_in_song_song(x, log):
    """🖨 Bộ đề PDF in trên lớp — ĐÚNG các câu vừa đăng (link thi / bài giảng), cùng thứ tự, cùng phương án,
    mã đề trùng mã trên mạng; lưu vào thư mục đề mặc định (de-da-ra/Lớp N/…) kèm lời giải, đáp án Excel."""
    bo = [b for b in (x.get("bo") or []) if any(b.get(l) for l in ("TN", "DS", "TLN", "TL"))]
    if not bo:
        return
    mt = dict(x.get("mt") or {})
    ten = (x.get("ten") or mt.get("ten_ky_thi") or "Đề kiểm tra").strip()
    mt.update({"ten": ten_khong_dau(f"{x.get('slug') or ten}_in_tren_lop", 60) or "De_in_tren_lop", "ten_ky_thi": ten,
               "so_ma_de": len(bo), "ma_de_bat_dau": int(x.get("bat_dau") or 101), "moi_ma_de_cau_khac_nhau": len(bo) > 1,
               "chon_san": bo, "sap_xep": "giu_nguyen", "xao_cau": False, "xao_phuong_an": False, "xao_y_dung_sai": False,
               "loi_giai_rieng": True, "de_cuong": False, "xuat_beamer": False, "xuat_leftnote": False,
               "xuat_word": False, "xuat_word_k12": False, "xuat_word_de": False})
    for k in ("tranh_ma", "thu_muc_ra"):
        mt.pop(k, None)
    if not mt.get("phan"):                     # bộ câu đến từ nơi khác (bài giảng): dựng ma trận tối thiểu theo số câu
        mt["phan"] = [{"loai": l, "yeu_cau": [{"dang": "", "muc": "", "so": len(bo[0].get(l) or [])}]} for l in ("TN", "DS", "TLN", "TL") if bo[0].get(l)]
    log(f"\n🖨 Bộ đề PDF in trên lớp (đúng {sum(len(v) for v in bo[0].values())} câu đã đăng, {len(bo)} mã đề)…")
    p = os.path.join(GOC, "du-lieu", "_ma_tran_tam.json")
    json.dump(mt, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    rc, ra = chay([os.path.join(SCRIPTS, "tron_de.py"), p])
    m = re.search(r"^THU_MUC:(.*)$", ra, re.M)
    if rc != 0 or not m:
        log("   ✗ Chưa tạo được bộ đề in:\n" + ra[-600:]); return
    thu = os.path.join(GOC, m.group(1).strip())
    if tim_pdflatex():
        bien_dich_thu_muc(thu, lambda s: log("   " + s) if ("✗" in s or "✓" in s) else None)
    else:
        log("   (máy chưa có pdflatex — mở thư mục tex/ bằng TeXstudio để in)")
    log(f"   ✓ Bộ đề in trên lớp: {os.path.relpath(thu, GOC)}")
    cong_viec["de_in"] = os.path.relpath(thu, GOC)


def dang_thi_nen(viec=None, sau=None):
    """Đổi đề (nếu có) rồi đăng thư mục thi-truc-tuyen/site lên Cloudflare Pages; `sau` chạy tiếp (vd tạo bộ đề in)."""
    import thi_truc_tuyen as T
    cong_viec.update(dang_chay=True, xong=False, nhat_ky="", thi_url="", de_in="")
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
    if sau:
        try:
            sau(ghi_log)
        except Exception as e:
            ghi_log(f"   ✗ bộ đề in: {e}")
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
            if u.path == "/tong_hop.js":
                return self.gui(200, open(os.path.join(SCRIPTS, "tong_hop.js"), "rb").read(), "text/javascript; charset=utf-8")
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
            if u.path == "/api/thu-muc-de":  # cây thư mục đề + sắp xếp thư mục cũ theo lớp / chương / kỳ
                import sap_xep_de as SX
                v = d.get("viec") or "xem"
                if v in ("ds", "ghim", "ghi", "cat"):          # giao diện Thư mục đề theo lớp
                    import thu_muc_de as TM
                    try:
                        moi = None
                        if v == "ghim":
                            TM.ghim(d.get("p"), bool(d.get("bat", True)))
                        elif v == "ghi":
                            TM.ghi_chu(d.get("p"), d.get("noi"))
                        elif v == "cat":
                            moi = TM.cat(d.get("p"))
                    except ValueError as e:
                        return self.gui(200, {"ok": False, "loi": str(e)})
                    import glob as _g
                    return self.gui(200, {"ok": True, **TM.danh_sach(), "moi": moi, "so_cu": len(SX.ke_hoach()),
                                          "co_hoan_tac": bool(_g.glob(os.path.join(SX.NHAT_KY, "*.json")))})
                dong = []
                if v == "lam":
                    SX.lam(dong.append)
                elif v == "hoan_tac":
                    SX.hoan_tac(dong.append)
                import glob as _g
                return self.gui(200, {"ok": True, "cay": SX.cay(), "ke_hoach": SX.ke_hoach(), "nhat_ky": "\n".join(dong),
                                      "co_hoan_tac": bool(_g.glob(os.path.join(SX.NHAT_KY, "*.json")))})
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
                    ds = T.danh_sach()
                    for x in ds:
                        try:
                            x["pl"] = T.phan_loai(x, ds)
                        except Exception:
                            x["pl"] = {"lop": 0, "chuong": "", "chuong_so": 0, "bai": "", "bai_so": 0}
                    return self.gui(200, {"ok": True, "ds": ds, "cau_hinh": T.cau_hinh(), "goc": T.goc_url(),
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
                if viec in ("theo-doi", "theo-doi-dat", "de-giao", "de-giao-ds", "bang-diem", "lo-hong"):
                    return self.gui(200, T.goi(viec, d))
                if viec == "loi-nhan":
                    return self.gui(200, T.goi("loi-nhan", {"ds": d.get("ds") or []}))
                if viec == "tong-hop":
                    return self.gui(200, T.goi("tong-hop", {"lop": d.get("lop") or ""}))
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
                        de_in = d.get("de_in")
                        threading.Thread(target=dang_thi_nen, kwargs={"sau": (lambda log: de_in_song_song(de_in, log)) if de_in else None},
                                         daemon=True).start()
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
                            if P.get("kieu") == "luyen_ngay":
                                ten = ten if ten.lower().startswith("luyện") else "Luyện mỗi ngày – " + ten
                            else:
                                ten = ten if ten.lower().startswith("phiếu") else ("Phiếu tự luận – " if P.get("kieu") == "tu_luan" else "Phiếu học tập – ") + ten
                            lop = int(re.sub(r"\D", "", str(P.get("lop") or "")) or 10)
                            slug = T.them_bai_giang(d.get("slug") or (("luyen-ngay-" if P.get("kieu") == "luyen_ngay" else "phieu-") + T.lam_slug(P.get("ten") or ten)
                                                                       + ("-tl" if P.get("kieu") == "tu_luan" else "")),
                                                    ten, lop, "html", open(p, "rb").read(), True, "phiếu học tập",
                                                    P.get("chuong") or "", P.get("ten") or "", 0, hs=d["dang"] == "hs", loai_bg="phieu")
                            T.dat_thu_muc(slug, os.path.relpath(os.path.dirname(p), GOC))
                            threading.Thread(target=dang_thi_nen, daemon=True).start()
                            ra.update(slug=slug, url=f"{T.goc_url()}/bai-giang/{slug}/")
                    except Exception as e:
                        return self.gui(200, {"ok": False, "loi": str(e), "nhat_ky": "\n".join(dong)})
                    return self.gui(200, ra)
                if viec == "phieu-lam-lai":   # phiếu đã đăng → dựng lại HTML bằng mẫu mới nhất (trình chiếu, nền sáng/tối…)
                    import phieu_web
                    x = next((y for y in T.danh_sach() if y["slug"] == d.get("slug") and y.get("loai") == "bai_giang"), None)
                    if not x:
                        return self.gui(200, {"ok": False, "loi": "Không thấy bài này."})
                    tm = T.tim_thu_muc_phieu(x)
                    if not tm:
                        return self.gui(200, {"ok": False, "loi": "Không tìm thấy thư mục phiếu gốc trong de-da-ra. Thầy mở Phiếu bài học → 🌐 Phiếu HTML lên web… và chọn lại thư mục phiếu."})
                    dong = []
                    try:
                        p, P = phieu_web.ghi(tm, dong.append)
                        T.them_bai_giang(x["slug"], x["ten"], x.get("lop") or 10, "html", open(p, "rb").read(), True, x.get("nguon") or "phiếu học tập",
                                         x.get("chuong") or "", x.get("bai") or "", x.get("chuong_so") or 0, hs=bool(x.get("hs")), loai_bg="phieu")
                        T.dat_thu_muc(x["slug"], os.path.relpath(tm, GOC))
                    except Exception as e:
                        return self.gui(200, {"ok": False, "loi": str(e), "nhat_ky": "\n".join(dong)})
                    threading.Thread(target=dang_thi_nen, daemon=True).start()
                    return self.gui(200, {"ok": True, "nhat_ky": "\n".join(dong)})
                if viec == "bg-pdf":
                    de_in = d.get("de_in")
                    threading.Thread(target=dang_thi_nen, args=(lambda log: bai_giang_pdf(d, log),),
                                     kwargs={"sau": (lambda log: de_in_song_song(de_in, log)) if de_in else None}, daemon=True).start()
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
                                         so_luot=int(d.get("so_luot") if d.get("so_luot") is not None else 2),
                                         goi_y_ai=bool(d.get("goi_y_ai")))
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
                if viec == "goi-y":            # bật / tắt 💡 Gợi ý AI cho đề đã đăng
                    sl, bat = d.get("slug"), bool(d.get("bat"))
                    threading.Thread(target=dang_thi_nen, args=(lambda log: (T.dat_goi_y(sl, bat),
                                     log(f"Gợi ý AI đề {sl}: {'bật' if bat else 'tắt'}")),), daemon=True).start()
                    return self.gui(200, {"ok": True})
                if viec == "dang-lai":
                    de_in = d.get("de_in")
                    threading.Thread(target=dang_thi_nen, kwargs={"sau": (lambda log: de_in_song_song(de_in, log)) if de_in else None},
                                     daemon=True).start()
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
                t = xem_truoc.doi(d.get("ma"), d.get("tranh") or [], da_dung=d.get("da_dung") or "uu_tien", tu_luan=bool(d.get("tu_luan")))
                return self.gui(200, {"ok": bool(t), "cau": t})
            if u.path == "/api/ds-cau-nhom":
                import xem_truoc
                r = xem_truoc.ds_theo_nhom(
                    loai=d.get("loai") or "", lop=d.get("lop") or "", chuong=d.get("chuong") or "",
                    bai=d.get("bai") or "", dang=d.get("dang") or "", muc=d.get("muc") or "",
                    tim=d.get("tim") or "", chi_chua_dung=bool(d.get("chi_chua_dung")),
                    tranh=d.get("tranh") or [], offset=d.get("offset") or 0, limit=d.get("limit") or 30,
                    tu_luan=bool(d.get("tu_luan")),
                )
                return self.gui(200, r)
            if u.path == "/api/luu-ma-tran":
                mt = d["ma_tran"]; ten = ten_khong_dau(mt.get("ten") or "MaTran", 60)
                json.dump({**mt, "ten": ten}, open(os.path.join(GOC, "ma-tran", ten + ".json"), "w", encoding="utf-8"),
                          ensure_ascii=False, indent=2)
                return self.gui(200, {"ok": True, "ten": ten})
            if u.path == "/api/sao-luu":          # sao lưu những gì GitHub không giữ + tình trạng an toàn dữ liệu
                import sao_luu as SL
                if d.get("viec") == "tao":
                    dong = []
                    try:
                        p = SL.tao(d.get("dich"), d.get("de_ra") or "ket_qua", d.get("kem_kho", True), dong.append)
                    except (ValueError, OSError) as e:
                        return self.gui(200, {"ok": False, "loi": str(e)})
                    return self.gui(200, {"ok": True, "tep": p, "nhat_ky": "\n".join(dong), **SL.tinh_trang()})
                if d.get("viec") == "dong-bo":
                    f = "Dong bo (Windows).bat" if sys.platform.startswith("win") else "Dong bo (Mac).command"
                    p = os.path.join(GOC, f)
                    if not os.path.exists(p):
                        return self.gui(200, {"ok": False, "loi": "Không thấy file " + f})
                    if sys.platform.startswith("win"):
                        os.startfile(p)
                    else:
                        subprocess.Popen(["open", "-a", "Terminal", p] if sys.platform == "darwin" else ["xdg-open", p])
                    return self.gui(200, {"ok": True})
                if d.get("viec") == "mo-dich":
                    p = os.path.expanduser(d.get("dich") or "")
                    if os.path.isdir(p):
                        if sys.platform.startswith("win"):
                            os.startfile(p)
                        else:
                            subprocess.Popen(["open", p] if sys.platform == "darwin" else ["xdg-open", p])
                    return self.gui(200, {"ok": True})
                return self.gui(200, {"ok": True, **SL.tinh_trang()})
            if u.path == "/api/mo":
                p = os.path.realpath(os.path.join(GOC, d.get("duong_dan", "")))
                if not p.startswith(os.path.realpath(GOC)) or not os.path.exists(p):
                    return self.gui(400, {"ok": False})
                if sys.platform.startswith("win"):
                    os.startfile(p)
                else:
                    subprocess.Popen(["open", p] if sys.platform == "darwin" else ["xdg-open", p])
                return self.gui(200, {"ok": True})
            if u.path.startswith("/api/ngoai/"):        # ĐỀ TỪ NGUỒN NGOÀI: prompt → dán kết quả AI → xem trước, chèn hình → trộn
                import de_ngoai as DN
                v = u.path.rsplit("/", 1)[1]
                try:
                    if v == "prompt":
                        return self.gui(200, {"ok": True, "noi_dung": DN.prompt(d.get("kieu"), d.get("cfg") or {})})
                    if v == "doc":
                        ks = DN.doc(d.get("van_ban") or "", d.get("ten") or "de_ai.tex") if d.get("van_ban") is not None else \
                            [DN.chuan(k) for k in (d.get("khoi") or [])]
                        if not ks:
                            return self.gui(200, {"ok": False, "loi": "Không thấy câu nào: kết quả AI cần các khối \\begin{ex}…\\end{ex} / \\begin{bt}…\\end{bt} hoặc JSON trac_nghiem / dung_sai / tra_loi_ngan."})
                        return self.gui(200, {"ok": True, **DN.kiem_tat_ca(ks)})
                    if v == "xem":
                        return self.gui(200, DN.xem_truoc(d.get("khoi") or [], bat_dau=int(d.get("bat_dau") or 0)))
                    if v == "chen-hinh":
                        k = DN.chen_hinh(d.get("tex") or "", d.get("tikz") or "", d.get("vi_tri") or "giua", bool(d.get("thay")))
                        return self.gui(200, {"ok": True, "tex": k, **DN.thong_tin(k)})
                    if v == "bo-cho-hinh":
                        k = DN.bo_cho_hinh(d.get("tex") or "")
                        return self.gui(200, {"ok": True, "tex": k, **DN.thong_tin(k)})
                    if v == "sua":
                        ks = DN.doc(d.get("tex") or "")
                        if len(ks) != 1:
                            return self.gui(200, {"ok": False, "loi": "Mã câu phải là đúng MỘT khối \\begin{ex}…\\end{ex} hoặc \\begin{bt}…\\end{bt}."})
                        return self.gui(200, {"ok": True, "tex": ks[0], **DN.thong_tin(ks[0])})
                    if v == "prompt-hinh":
                        return self.gui(200, {"ok": True, "noi_dung": DN.prompt_ve_hinh(d.get("tex") or "")})
                    if v == "ghep":
                        return self.gui(200, {"ok": True, "noi_dung": DN.ghep(d.get("khoi") or [], d.get("nguon") or "")})
                except ValueError as e:
                    return self.gui(200, {"ok": False, "loi": str(e)})
                return self.gui(404, {"ok": False})
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
            if u.path.startswith("/api/hd/"):          # 🎲 phiếu hoạt động: Mật mã · Tìm lỗi sai · Ôn tập ngắt quãng
                import phieu_hoat_dong as H
                viec = u.path.rsplit("/", 1)[1]
                try:
                    if viec == "thong-tin":
                        dang = d.get("dang") or []
                        g = H.goi_y_on(set(d.get("dang_nay") or []), d.get("lop")) if d.get("goi_y") else {}
                        return self.gui(200, {"ok": True, "loi": H.dem_loi(dang), "goi_y": g, "thong_diep": H.THONG_DIEP_MAU})
                    if viec == "prompt":
                        if d.get("kieu") == "tim_loi":
                            p, n = H.prompt_loi(d.get("dang") or [], int(d.get("so") or 4))
                            return self.gui(200, {"ok": True, "prompt": p, "so": n})
                        return self.gui(200, {"ok": True, "prompt": H.prompt_cau(d.get("dang") or [], int(d.get("so") or 4), d.get("kieu") or "mat_ma")})
                    if viec == "nhap-loi":
                        so, bo = H.nhap_loi(d.get("van") or "")
                        return self.gui(200, {"ok": True, "so": so, "bo": bo})
                    if viec == "ai-loi":
                        if cong_viec.get("dang_chay"):
                            return self.gui(200, {"ok": False, "loi": "Đang có việc khác chạy, đợi xong rồi bấm lại."})
                        cong_viec.update(dang_chay=True, xong=False, nhat_ky="", ket_qua=None)
                        threading.Thread(target=ai_loi_sai_nen, args=(dict(d),), daemon=True).start()
                        return self.gui(200, {"ok": True})
                    if viec == "tao":
                        dong = []
                        ham = {"mat_ma": H.mat_ma, "tim_loi": H.tim_loi_sai, "on_tap": H.on_tap,
                                "thu_thach": H.thu_thach, "manh_ghep": H.manh_ghep}[d.get("kieu")]
                        out_goc = ham(d.get("cau_hinh") or {}, dong.append)
                        rel = os.path.relpath(out_goc, GOC)
                        dang_bd = bool(d.get("bien_dich")) and bool(tim_pdflatex())
                        if dang_bd:
                            threading.Thread(target=bien_dich_nen, args=(rel,), daemon=True).start()
                        return self.gui(200, {"ok": True, "nhat_ky": "\n".join(dong), "thu_muc": rel, "bien_dich": dang_bd})
                except Exception as e:
                    return self.gui(200, {"ok": False, "loi": str(e)})
                return self.gui(404, {"loi": "không có"})
            if u.path == "/api/so-tay-dm":           # 📐 sổ tay công thức: cây chương → bài → dạng của một lớp
                import so_tay_cong_thuc
                return self.gui(200, {"ok": True, "cay": so_tay_cong_thuc.danh_muc(int(d.get("lop") or 10)),
                                      "kho": [{"ma": k, "ten": v["ten"]} for k, v in so_tay_cong_thuc.KHO.items()]})
            if u.path == "/api/so-tay":
                import so_tay_cong_thuc
                dong = []
                try:
                    out_goc = so_tay_cong_thuc.tao(d.get("cau_hinh") or {}, dong.append)
                except Exception as e:
                    return self.gui(200, {"ok": False, "nhat_ky": f"Chưa tạo được: {e}"})
                rel = os.path.relpath(out_goc, GOC)
                dang_bd = bool(d.get("bien_dich")) and bool(tim_pdflatex())
                if dang_bd:
                    threading.Thread(target=bien_dich_nen, args=(rel,), daemon=True).start()
                return self.gui(200, {"ok": True, "nhat_ky": "\n".join(x for x in dong if not x.startswith("THU_MUC:")), "thu_muc": rel, "bien_dich": dang_bd})
            if u.path == "/api/phieu-xem-truoc":     # phiếu bài học: chọn thử bộ câu để thầy xem, đổi câu ưng ý rồi mới tạo
                import phieu_bai_hoc
                cfg = d.get("cau_hinh") or {}
                if cfg.get("kieu_cau") == "luyen_ngay":
                    return self.gui(200, {"ok": False, "loi": "Luyện mỗi ngày chưa hỗ trợ xem trước — thầy chọn Trắc nghiệm hoặc Tự luận."})
                try:
                    r = phieu_bai_hoc.chon_xem_truoc(cfg)
                except Exception as e:
                    return self.gui(200, {"ok": False, "loi": str(e)})
                if not any(r["bo"][0].values()):
                    return self.gui(200, {"ok": False, "loi": "Không tìm thấy câu nào trong phạm vi đã chọn.", "thieu": r["thieu"]})
                return self.gui(200, {"ok": True, **r})
            if u.path == "/api/phieu-thieu":
                import phieu_bai_hoc
                cfg = d.get("cau_hinh") or {}
                if cfg.get("kieu_cau") == "luyen_ngay":      # luyện mỗi ngày: kiểm kho như phiếu tự luận (ví dụ mẫu + tự luyện mỗi dạng)
                    cfg = dict(cfg, kieu_cau="tu_luan")
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
                    if cfg.get("kieu_cau") == "luyen_ngay":
                        import luyen_moi_ngay
                        out_goc = luyen_moi_ngay.tao(cfg, dong.append)
                    else:
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
            if u.path == "/api/prompt-tuong-tu":      # phiếu tự luận: prompt AI soạn câu tương tự BÁM SÁT từng ví dụ mẫu
                import random, luyen_moi_ngay, tao_prompt
                cfg = dict(d.get("cau_hinh") or {}, so_tuong_tu=0, so_van_dung=0, theo_mau=False)
                try:
                    kq, cac_dang, _ = luyen_moi_ngay.chon(cfg, random.Random(cfg.get("seed") or time.time()))
                    if not kq:
                        return self.gui(200, {"ok": False, "loi": "Phạm vi đã chọn chưa có câu tự luận (có lời giải) nào để làm ví dụ mẫu."})
                    id_map = tai_id_map()
                    mau = [{"ma": kq[k]["vd"]["ma"], "dang_key": k, "muc": kq[k]["vd"].get("muc_chuan") or "H",
                            "ten_dang": (id_map.get(k, {}).get("type_name") or "").strip(), "ten_bai": (id_map.get(k, {}).get("lesson_name") or "").strip(),
                            "de": kq[k]["vd"]["_tl"]["de"], "lg": kq[k]["vd"]["_tl"]["lg"]} for k in cac_dang]
                    lop = lop_tu_so(cac_dang[0][0])
                    p = tao_prompt.prompt_tuong_tu(mau, d.get("so") or 3, d.get("kieu") or "giong", lop, d.get("ghi_chu") or "")
                except Exception as e:
                    return self.gui(200, {"ok": False, "loi": str(e)})
                return self.gui(200, {"ok": True, "noi_dung": p, "vi_du_mau": {m["dang_key"]: m["ma"] for m in mau}, "so_mau": len(mau)})
            if u.path == "/api/tuong-tu-nhap":        # dán kết quả AI → nhập kho → tạo phiếu riêng: ví dụ mẫu + đúng các câu tương tự theo mẫu
                import nhap_cau
                t = (d.get("van") or "").strip()
                m = re.search(r"```(?:latex|tex)?\s*\n([\s\S]*?)```", t)
                t = m.group(1) if m else t
                if "\\begin{bt}" not in t and "\\begin{ex}" not in t:
                    return self.gui(200, {"ok": False, "nhat_ky": "Chưa thấy câu nào (\\begin{bt} … \\end{bt}) trong nội dung dán vào."})
                if not re.search(r"%\s*mau:\s*[0-9a-f]{8}", t):
                    return self.gui(200, {"ok": False, "nhat_ky": "Các câu chưa có dòng '% mau: <mã câu mẫu>' — AI cần giữ dòng này (xem lại prompt)."})
                return self.gui(200, nhap_tuong_tu_va_tao_phieu(t, dict(d.get("cau_hinh") or {}), d.get("so"), d.get("vi_du_mau"),
                                                                d.get("bien_dich")))
            if u.path == "/api/khoa-ai":              # nhiều khoá API (Gemini / DeepSeek / Claude / OpenAI) — tự nhận dạng, lưu ai_khoa.json trên máy
                import sinh_tuong_tu as ST
                if d.get("luu"):
                    ST.luu_khoa(d.get("van") or "", them=bool(d.get("them")))
                ra = {"ok": True, "ds": [{"nha": ST.TEN_NHA.get(k["nha"], k["nha"]), "khoa": ST.che(k["khoa"]), "mo_hinh": k.get("mo_hinh") or ""}
                                         for k in ST.doc_khoa()["ds"]]}
                ra["co_khoa"] = bool(ra["ds"])
                import hoi_dong_ai as HD                     # phân vai Hội đồng AI
                if isinstance(d.get("vai"), dict):
                    HD.luu_vai(d["vai"])
                ra["vai"] = HD.mo_ta_vai(HD.phan_vai())
                ra["vai_chon"] = ST.doc_khoa().get("vai") or {}
                ra["co_nha"] = [{"nha": n, "ten": ST.TEN_NHA.get(n, n)} for n in HD.cac_nha()]
                if d.get("thu"):
                    ra["thu"] = [{"nha": a, "khoa": b, "ok": c, "ghi": e} for a, b, c, e in ST.kiem_tra_khoa()]
                return self.gui(200, ra)
            if u.path == "/api/tu-sinh":              # NGÂN HÀNG TỰ SINH (chạy nền): rút mẫu → Python / AI sinh câu tương tự → nhập kho → in phiếu theo mẫu
                if cong_viec.get("dang_chay"):
                    return self.gui(200, {"ok": False, "nhat_ky": "Đang có việc khác chạy (biên dịch / đăng web…) — thầy đợi xong rồi bấm lại."})
                cong_viec.update(dang_chay=True, xong=False, nhat_ky="", ket_qua=None)
                threading.Thread(target=tu_sinh_nen, args=(dict(d),), daemon=True).start()
                return self.gui(200, {"ok": True, "nen": True})
            if u.path == "/api/khuon":                # 🧬 câu song sinh từ khuôn (chạy nền)
                if cong_viec.get("dang_chay"):
                    return self.gui(200, {"ok": False, "nhat_ky": "Đang có việc khác chạy — thầy đợi xong rồi bấm lại."})
                cong_viec.update(dang_chay=True, xong=False, nhat_ky="", ket_qua=None)
                threading.Thread(target=khuon_nen, args=(dict(d),), daemon=True).start()
                return self.gui(200, {"ok": True, "nen": True})
            if u.path == "/api/khuon-xem":            # xem khuôn đã lưu của một câu
                import khuon_cau as KC
                return self.gui(200, {"ok": True, "code": KC.doc_khuon(d.get("ma") or "") or ""})
            if u.path in ("/api/hk-sinh-ai", "/api/ai-hoi-dong"):   # AI sinh câu (Ôn thi HK / Hội đồng AI mọi mục) → phản biện chéo → biên dịch thử → nhập kho
                if u.path == "/api/ai-hoi-dong":
                    d["hoi_dong"] = True
                    d.setdefault("nhan", "Hội đồng AI")
                if cong_viec.get("dang_chay"):
                    return self.gui(200, {"ok": False, "nhat_ky": "Đang có việc khác chạy (biên dịch / đăng web…) — thầy đợi xong rồi bấm lại."})
                cong_viec.update(dang_chay=True, xong=False, nhat_ky="", ket_qua=None)
                threading.Thread(target=hk_sinh_ai_nen, args=(dict(d),), daemon=True).start()
                return self.gui(200, {"ok": True, "nen": True})
            if u.path == "/api/chon-theo-dang":      # phiếu vá lỗ hổng / phiếu cuối giờ: rút câu ngân hàng theo dạng hoặc theo bài
                import random
                from xem_truoc import kho, hop_le
                dang = set(d.get("dang") or []); bai = set(d.get("bai") or [])
                loai = set(d.get("loai") or ["TN", "DS", "TLN"]); moi = max(1, min(6, int(d.get("moi") or 2))); tong = int(d.get("tong") or 0)
                thu_tu = {"N": 0, "H": 1, "V": 2, "C": 3}
                theo = {}
                for c in kho().values():
                    k = c.get("dang_key") or ""
                    if not k or c.get("loai") not in loai or not hop_le(c):
                        continue
                    if k in dang or k.split("-")[0] in bai:
                        theo.setdefault(k, []).append(c)
                chon, thieu = [], []
                for k in sorted(theo) if bai else [x for x in d.get("dang") or [] if x in theo]:
                    ds = theo[k]; random.shuffle(ds)
                    ds.sort(key=lambda c: (thu_tu.get(c.get("muc_chuan") or c.get("muc") or "H", 1), c.get("so_lan_dung") or 0))
                    # dễ → khó: lấy rải theo mức (câu dễ nhất, rồi câu khó hơn)
                    buoc = max(1, len(ds) // moi) if len(ds) > moi else 1
                    chon += [ds[min(i * buoc, len(ds) - 1)] for i in range(min(moi, len(ds)))]
                thieu = [x for x in (d.get("dang") or []) if x not in theo]
                if tong and len(chon) > tong:            # phiếu cuối giờ: N câu rải đều các dạng, dễ → khó
                    chon.sort(key=lambda c: thu_tu.get(c.get("muc_chuan") or c.get("muc") or "H", 1))
                    b = len(chon) / tong; chon = [chon[int(i * b)] for i in range(tong)]
                chon.sort(key=lambda c: ({"TN": 0, "DS": 1, "TLN": 2}.get(c["loai"], 3), thu_tu.get(c.get("muc_chuan") or c.get("muc") or "H", 1)))
                return self.gui(200, {"ok": bool(chon), "ma": [c["ma"] for c in chon], "thieu": thieu,
                                      "loi": "" if chon else "Ngân hàng chưa có câu hợp lệ cho các dạng/bài đã chọn."})
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
                cu_dir = os.path.join(GOC, "du-lieu", "_cu")
                if d.get("hoan_tac"):            # trả lại bản lịch sử trước lần reset
                    f = os.path.join(cu_dir, os.path.basename(d["hoan_tac"]))
                    if not os.path.isfile(f):
                        return self.gui(200, {"ok": False, "loi": "Không còn bản sao lưu để hoàn tác."})
                    shutil.copy(f, p)
                    return self.gui(200, {"ok": True, **tom_tat_lich_su()})
                ls = doc_lich_su()
                os.makedirs(cu_dir, exist_ok=True)
                sao = f"lich_su_dung_{time.strftime('%Y%m%d-%H%M%S')}.json"
                json.dump(ls, open(os.path.join(cu_dir, sao), "w", encoding="utf-8"), ensure_ascii=False)
                truoc = len(ls)
                if d.get("xoa_het"):
                    ls = {}
                elif d.get("bo_de"):
                    ls = {k: [x for x in v if x != d["bo_de"]] for k, v in ls.items()}
                    ls = {k: v for k, v in ls.items() if v}
                elif d.get("bo_ma") is not None:  # cho lấy lại các câu này (reset câu đã rút của bộ đề)
                    bo = set(d["bo_ma"])
                    ls = {k: v for k, v in ls.items() if k not in bo}
                elif d.get("bo_lop"):            # reset mọi câu đã dùng của một lớp
                    ma_lop = {"10": "0", "11": "1", "12": "2"}.get(str(d["bo_lop"]), str(d["bo_lop"]))
                    lop_cua = {}
                    for dong in open(os.path.join(GOC, "du-lieu", "chi_muc.jsonl"), encoding="utf-8"):
                        c = json.loads(dong); lop_cua[c["ma"]] = (c.get("dang_key") or "")[:1]
                    ls = {k: v for k, v in ls.items() if lop_cua.get(k) != ma_lop}
                json.dump(ls, open(p, "w", encoding="utf-8"), ensure_ascii=False)
                return self.gui(200, {"ok": True, "da_xoa": truoc - len(ls), "sao_luu": sao, **tom_tat_lich_su()})
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
