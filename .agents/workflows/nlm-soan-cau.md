---
description: Soạn câu hỏi MỚI theo một bài học, bám tài liệu trong NotebookLM, xuất LaTeX/JSON đúng chuẩn kho rồi chuẩn bị nhập
---

# /nlm-soan-cau — Soạn câu mới theo bài (NotebookLM đọc nguồn, em là bộ não)

Đầu vào thầy gõ kèm lệnh, ví dụ: `/nlm-soan-cau Toán 10 Bài 9 Tích vectơ với một số — 8 TN, 4 ĐS, 6 TLN, ưu tiên thực tế, xuất tex`.
Thiếu thông tin nào thì dùng mặc định: 8 TN (3N 3H 2V) · 4 ĐS (mức H/V) · 6 TLN (2H 3V 1C) · xuất `.tex`.

1. **Xác định dạng.** Chạy `python3 scripts/tra_dang.py "<tên bài không dấu>"` (hoặc `--tien-to` nếu biết mã chương/bài).
   Liệt kê các dạng của bài + số câu đang có. Rải số câu ưu tiên dạng ÍT câu. Ghi kế hoạch ngắn: dạng × loại × mức.

2. **Chọn notebook.** Đọc `notebooklm/so_tay_notebook.json` lấy id notebook của lớp. Chưa có id → gọi tool
   `notebook_list` của MCP notebooklm, chọn notebook khớp lớp, ghi id vào sổ tay rồi tiếp tục.

3. **Hỏi NotebookLM theo từng dạng** (mỗi lần ≤ 10 câu) bằng tool `notebook_query`, dùng mẫu
   "MẪU 2 – Soạn câu bám nguồn" trong `notebooklm/mau_hoi_notebooklm.md` (điền tên bài, dạng, số câu từng loại × mức).
   - Lưu NGUYÊN VĂN câu trả lời vào `ai-nhap/tho/YYYY-MM-DD_<lop>_<bai>_<dang>.md` trước khi xử lý.
   - Câu trả lời không có JSON hợp lệ → hỏi lại một lần, nhấn mạnh "chỉ trả khối ```json".
   - Tool lỗi xác thực → dừng, nhắn thầy chạy `nlm login` trong Terminal. Hỏng hẳn → chế độ thủ công (HUONG_DAN_NOTEBOOKLM.md, mục 5).

4. **Bộ não xử lý từng câu nháp** (đây là việc của em, không giao lại cho NotebookLM):
   - Gắn mã dạng đúng `%[<lớp><môn><chương><mức><bài>-<dạng>]` từ bước 1; sửa mức nếu nháp đánh sai độ khó.
   - **Tự giải lại**; có số thì kiểm bằng `python3 -c "..."`. Sai → sửa đề/đáp án; không chắc → `% KIEM_TRA: …`.
   - TN: 1 đáp án đúng, 3 nhiễu theo lỗi sai thường gặp; trải đáp án đúng đều A–D trong cả lô.
   - ĐS: 4 ý độc lập, khó tăng dần a → d; lời giải 4 `\itemch`.
   - TLN: đáp số ≤ 4 ký tự, dấu phẩy thập phân.
   - Giữ dòng `% nguon: …` từ trường `nguon` của NotebookLM.
   - Viết lại LaTeX theo `.agents/rules/dinh-dang-ngan-hang.md` (hoặc giữ khuôn JSON nháp, thêm trường `"ma_dang": "0H5N3-1"` nếu thầy chọn JSON; không dùng trường tên `dang`).

5. **Ghi file** `ai-nhap/YYYY-MM-DD_<lop>_<bai-khong-dau>.tex` (hoặc `.json`). Nhiều dạng gộp một file.

6. **Kiểm tra – tự sửa vòng lặp:** `python3 scripts/kiem_tra_ai.py <file> --json` → sửa mọi câu có `loi` → chạy lại tới khi 0 LỖI.
   Câu báo "TRÙNG câu đã có trong kho" → thay bằng câu khác.

7. **Báo thầy** bảng tóm tắt: số câu theo loại × mức × dạng, các câu `% KIEM_TRA`, đường dẫn file.
   Hỏi: "Thầy cho nhập vào kho không?" → nếu đồng ý thì chạy `/nhap-kho <file>`.
