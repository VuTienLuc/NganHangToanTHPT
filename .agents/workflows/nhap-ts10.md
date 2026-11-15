---
description: Nhập đề TUYỂN SINH 10 từ PDF (đề chính thức, đề tham khảo quận…) vào kho lớp 9 + kho Tuyển sinh 10 — ít token nhất
---

# /nhap-ts10 — PDF đề tuyển sinh 10 → kho (tiết kiệm token)

Thầy nói: "nhập đề TS10 từ <file.pdf> đề 3, 4" (hoặc trang …). **Mỗi lượt 2 đề (14 bài).**

1. **Tách chữ bằng máy (0 token):** `python3 scripts/pdf_sang_chu.py "<file.pdf>" --trang <a-b> --ten <quan_x_de_y_z>`
   → `ai-nhap/tho/<ten>.txt`. Báo "không có lớp chữ" (PDF scan) → hỏi NotebookLM (`/nlm-go-de`) gõ thô 2 đề, lưu `ai-nhap/tho/`.
   KHÔNG tự đọc PDF dạng ảnh, KHÔNG mở cả cuốn PDF.
2. **Chuẩn hoá (1 lượt, chỉ định dạng lại — không giải lại):** đọc file thô, viết `ai-nhap/YYYY-MM-DD_09_<ten>.tex`, mỗi bài một khối:
   ```
   \begin{bt}%[<mã dạng lớp 9>]
   % nguon: Đề tham khảo Tuyển sinh 10 TP.HCM 2025-2026 – Quận 4 – Đề 1 – Bài 3
   <đề, các ý dùng \begin{enumerate}[a)] \item … \end{enumerate}>
   \loigiai{ <CHÉP lời giải/hướng dẫn chấm có trong PDF; PDF không có mới tự giải — số liệu kiểm bằng python3 -c> }
   \end{bt}
   ```
   - Dòng `% nguon:` BẮT BUỘC có chữ "Tuyển sinh 10" và "Bài N" (để tự đồng bộ sang kho TS10).
   - Mã dạng lớp 9 theo chủ đề (? = mức N/H/V/C):
     Bài 1 parabol `9D6?18-2` · Bài 2 Viète `9D6?20-2` · Bài 3 thống kê–xác suất `9D8?26-3` (`9D8?26-2`) ·
     Bài 4 thực tế lập PT/biểu thức `9D6?21-3` · Bài 5 hình khối `9H0?31-3` (`9H0?31-1`, `9H0?31-2`) ·
     Bài 6 lập hệ `9D1?3-4` · Bài 7 đường tròn `9H9?29-3`. Khác → `python3 scripts/tra_dang.py "<từ khoá>"`.
   - Hình: chỉ vẽ TikZ khi đề cần (biểu đồ Bài 3, vật thể Bài 5, hình Bài 7); Bài 1 không cần vẽ (P) trong đề.
   - Không thêm lời bình, không viết lại đề cho "hay hơn".
3. **Kiểm tra (0 token):** `python3 scripts/kiem_tra_ai.py <file>` → `python3 scripts/nhap_cau.py <file> --thu`; báo thầy số bài, bài lỗi.
4. **Thầy đồng ý → nhập:** `python3 scripts/nhap_cau.py <file>` — bài lỗi biên dịch tự loại (ai-nhap/_loi/);
   bài có nguồn tuyển sinh 10 **tự đồng bộ sang `cau-hoi-ts10/Bai1..7.tex`** (xếp theo nội dung, gán mã dạng TS10, biên dịch thử).
   Đọc mục "⚠ máy gán mã dạng chưa chắc" và sửa dòng `%[TS10 …]` nếu cần.
5. Dời file: `mv <file> ai-nhap/da-nhap/`. Git: `git add -A cau-hoi cau-hoi-ts10 ai-nhap && git commit -m "Nhập 14 bài Tuyển sinh 10 (<nguồn>)"`.
   Không tự `git push` — đưa lệnh cho thầy.

Đồng bộ lại bất cứ lúc nào: `python3 scripts/ts10_tu_kho9.py` (hoặc nút **⇄ Đồng bộ từ kho lớp 9** trong menu Tuyển sinh 10).
