---
description: Kiểm tra chặt, xem trước, nhập file câu hỏi AI (tex/json) trong ai-nhap/ vào ngân hàng LaTeX rồi lưu GitHub
---

# /nhap-kho — Đưa file trong `ai-nhap/` vào Quản lý ngân hàng LaTeX

Không nêu file → lấy mọi `.tex/.txt/.json` nằm trực tiếp trong `ai-nhap/` (không tính `tho/`, `da-nhap/`).

1. `python3 scripts/kiem_tra_ai.py <các file>` — còn LỖI thì sửa trong file rồi chạy lại (tối đa 3 vòng; vẫn lỗi → báo thầy câu nào).
2. `python3 scripts/nhap_cau.py <các file> --thu` — đọc báo cáo: số câu mới, số trùng bị bỏ, file dạng sẽ ghi, cảnh báo ⚠, **câu lỗi biên dịch bị loại** (ghi vào `ai-nhap/_loi/`, không nhập, không lên GitHub).
3. Tóm tắt cho thầy và **hỏi xác nhận**. Câu `%[?]`/chưa mã sẽ vào `cau-hoi/_chua_phan_loai/` — nói rõ.
4. Thầy đồng ý → `python3 scripts/nhap_cau.py <các file>` (tự gắn mã câu, tự lập lại chỉ mục).
5. Dời file đã nhập: `mkdir -p ai-nhap/da-nhap && mv <file> ai-nhap/da-nhap/`.
6. Lưu git: `git add -A cau-hoi ai-nhap notebooklm && git commit -m "Nhập <n> câu <lớp – bài> (NotebookLM)"`.
   Không tự `git push`: đưa lệnh cho thầy chạy (tài khoản GitHub VuTienLuc).
7. Nhắc: mở ứng dụng "Ra đề theo ma trận" bấm **Cập nhật kho** nếu ứng dụng đang mở.
