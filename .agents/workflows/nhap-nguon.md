---
description: Nhập câu hỏi từ NGUỒN KHÁC (file .tex ngân hàng khác, Word, PDF, ảnh, thư mục đề) vào kho — chuyển chuẩn, kiểm tra, xem trước, chỉ nhập câu tốt
---

# /nhap-nguon — Nhập kho từ nguồn khác (đúng nhất)

Dùng khi thầy nói "nhập kho từ …", "đưa đề/file này vào ngân hàng", hoặc đưa file/thư mục không phải do `/nlm-*` tạo.
Nguồn: đường dẫn thầy đưa hoặc file đính kèm. Không rõ lớp/bài → tự xác định từ nội dung rồi báo thầy.

1. **Giữ nguyên gốc.** Chép nguồn vào `ai-nhap/tho/<ngày>_<tên nguồn>/`; không sửa, không xoá file gốc của thầy.
   Mỗi lần xử lý 1 bài hoặc 1 chương (nguồn lớn → chia nhiều đợt, mỗi đợt một file).
2. **Chuyển về định dạng kho** thành `ai-nhap/YYYY-MM-DD_<lop>_<bai>.tex`:
   ex/bt, `\choice` + đúng 1 `\True`, `\choiceTF`, `\shortans{số ≤4 kí tự}`, `\loigiai`, theo `mau_cau_moi.tex`.
   - Word/PDF/ảnh: đọc kỹ công thức; xong **đối chiếu 5 câu ngẫu nhiên với gốc** (đề, phương án, đáp án).
   - Có hình TikZ: giữ nguyên toạ độ, **không đổi dấu phẩy trong toạ độ**; không dùng lệnh/gói lạ (\daungoac, \trucso, gói cờ vua…) — vẽ lại bằng TikZ thường hoặc để câu ra ngoài.
   - Nguồn có đáp án → chép đúng; không có → tự giải (tính số bằng `python3 -c`), nghi ngờ ghi `% KIEM_TRA`.
3. **Mã dạng**: chỉ lấy từ danh mục (`python3 scripts/tra_dang.py "<từ khoá>"` hoặc `--tien-to 0H5?3`). Câu không chắc → liệt kê cho thầy chọn, không đoán.
4. `python3 scripts/kiem_tra_ai.py <file>` tới khi **0 câu LỖI** (tối đa 3 vòng).
5. `python3 scripts/nhap_cau.py <file> --thu` rồi **báo cáo cho thầy** (bảng ngắn):
   tổng số câu · số câu theo mã dạng và mức độ · câu trùng kho (bị bỏ) · câu thiếu lời giải · câu `% KIEM_TRA` · **câu lỗi biên dịch kèm lý do**.
6. **Chờ thầy đồng ý** → `python3 scripts/nhap_cau.py <file>`.
   Câu lỗi tự bị loại, ghi vào `ai-nhap/_loi/` — KHÔNG nhập kho, KHÔNG đưa lên GitHub. Không dùng `--khong-bien-dich`.
7. Nhập xong: `python3 scripts/lap_chi_muc.py`; xuất thử 1 đề nhỏ có câu mới, biên dịch được mới coi là xong.
8. Dời file: `mkdir -p ai-nhap/da-nhap && mv <file> ai-nhap/da-nhap/`.
9. Git: `git add -A cau-hoi ai-nhap du-lieu && git commit -m "Nhập <n> câu <lớp – bài> từ <nguồn>"`.
   KHÔNG tự `git push` — đưa lệnh cho thầy tự chạy (đẩy bằng tài khoản GitHub **VuTienLuc**).
10. Báo kết quả cuối: số câu đã nhập, số câu lỗi để ở `ai-nhap/_loi/` (tên file), câu cần thầy xem lại.
