---
description: Gõ lại một đề thi / phiếu bài tập có sẵn trong NotebookLM thành câu LaTeX đúng chuẩn kho (giữ nguyên đề, gắn mã dạng)
---

# /nlm-go-de — Gõ lại đề có sẵn trong NotebookLM vào kho

Ví dụ: `/nlm-go-de notebook "NH Toán 11" nguồn "Đề GHK1 Toán 11 Trần Phú 2025"`.

1. Lấy id notebook (`notebooklm/so_tay_notebook.json`, hoặc tool `notebook_list`). Nếu thầy chưa nêu tên nguồn:
   gọi `notebook_get`/`source_list` (tên tool tuỳ bản MCP) để liệt kê nguồn, hỏi thầy chọn.

2. Hỏi NotebookLM bằng **MẪU 1 – Trích nguyên văn** trong `notebooklm/mau_hoi_notebooklm.md`, theo từng phần của đề
   (Phần I câu 1–6, 7–12; Phần II; Phần III) để câu trả lời không bị cắt. Lưu nguyên văn mỗi lần vào `ai-nhap/tho/`.
   Đề có đáp án/lời giải trong nguồn thì yêu cầu kèm; không có thì để trống — em tự giải ở bước 4.

3. Đối chiếu số câu trích được với đề (đủ, không thừa, đúng thứ tự). Thiếu → hỏi lại đúng đoạn thiếu.

4. **Bộ não xử lý:** giữ nguyên số liệu và cách hỏi của đề; tra mã dạng bằng `python3 scripts/tra_dang.py`
   (không có dạng phù hợp → `%[?]`); đánh giá mức N/H/V/C; tự giải và viết lời giải nếu nguồn không có,
   kiểm số bằng Python; câu có hình → vẽ TikZ nếu đơn giản, không thì `% CAN_VE_HINH`.
   Thêm `% nguon: <tên đề> – câu <n>`.

5. Ghi `ai-nhap/YYYY-MM-DD_<ten-de-khong-dau>.tex`, chạy `python3 scripts/kiem_tra_ai.py <file> --json`
   (cho phép `--cho-phep-chua-ma` với câu `%[?]`), sửa tới 0 LỖI.

6. Báo thầy tóm tắt + câu cần xem lại, rồi hỏi có chạy `/nhap-kho` không.
   Muốn trộn đề ngay từ file này: `python3 scripts/tron_de.py --tu-file <file> --so-ma-de 4 --bien-dich` (hỏi thầy trước).
