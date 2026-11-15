# -*- coding: utf-8 -*-
"""Tách CHỮ từ PDF đề (miễn phí, không tốn token AI) → ai-nhap/tho/<tên>.txt

Dùng:  python3 scripts/pdf_sang_chu.py "<file.pdf>" [--trang 5-8] [--ten quan_9_de_1_2]
- PDF có lớp chữ: dùng pdftotext (poppler) hoặc pypdf; công thức thường bị vỡ — AI chỉ cần đọc lại để gõ LaTeX.
- PDF SCAN (ảnh, không có chữ): script báo "không có lớp chữ" → đưa PDF vào NotebookLM / Gemini để gõ thô.
"""
import os, re, sys, shutil, argparse, subprocess
from nh_core import GOC


def tach(pdf, dau=None, cuoi=None):
    if shutil.which("pdftotext"):
        lenh = ["pdftotext", "-layout", "-enc", "UTF-8"] + (["-f", str(dau)] if dau else []) + (["-l", str(cuoi)] if cuoi else []) + [pdf, "-"]
        return subprocess.run(lenh, capture_output=True, text=True, errors="ignore").stdout
    try:
        from pypdf import PdfReader
    except ImportError:
        sys.exit("Máy chưa có pdftotext/pypdf. Cài một trong hai:  brew install poppler   hoặc   pip3 install pypdf")
    r = PdfReader(pdf)
    ds = r.pages[(dau or 1) - 1:(cuoi or len(r.pages))]
    return "\n\f".join(p.extract_text() or "" for p in ds)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--trang", help="vd 5-8")
    ap.add_argument("--ten")
    a = ap.parse_args()
    dau = cuoi = None
    if a.trang:
        x = a.trang.split("-"); dau = int(x[0]); cuoi = int(x[-1])
    t = tach(a.pdf, dau, cuoi)
    so_chu = len(re.sub(r"\s", "", t))
    if so_chu < 200:
        sys.exit(f"PDF gần như KHÔNG có lớp chữ ({so_chu} ký tự) — là bản scan. Đưa PDF vào NotebookLM/Gemini để gõ thô (xem .agents/workflows/nhap-ts10.md).")
    ten = a.ten or os.path.splitext(os.path.basename(a.pdf))[0]
    ten = re.sub(r"[^\w\-]+", "_", ten)
    d = os.path.join(GOC, "ai-nhap", "tho"); os.makedirs(d, exist_ok=True)
    p = os.path.join(d, ten + (f"_tr{dau}-{cuoi}" if dau else "") + ".txt")
    open(p, "w", encoding="utf-8").write(t)
    print(f"Đã tách {so_chu:,} ký tự → {os.path.relpath(p, GOC)}")
