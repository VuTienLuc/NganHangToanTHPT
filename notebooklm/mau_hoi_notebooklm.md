# Mẫu câu hỏi gửi NotebookLM

Antigravity điền phần `<…>` rồi gửi bằng tool `notebook_query`. Thầy cũng có thể chép tay vào ô chat NotebookLM (chế độ thủ công).
Cả hai mẫu yêu cầu cùng một khuôn JSON — khuôn này `scripts/nhap_cau.py` đọc được trực tiếp, Antigravity chỉ cần thêm `"ma_dang"`.

```
"loai":     "TN" | "DS" | "TLN" | "TL"
"muc":      "N" | "H" | "V" | "C"
"dang":     tên dạng toán (chữ)
"de":       đề bài, công thức trong $...$
"phuong_an": [4 chuỗi]   (TN: 4 phương án; DS: 4 mệnh đề a–d; TLN/TL: [])
"dap_an":   TN "B" · DS "ĐSĐS" · TLN "2,5" · TL ""
"loi_giai": lời giải ngắn gọn, đủ ý, công thức trong $...$
"nguon":    tên tài liệu – trang / ví dụ / bài tập
```

---

## MẪU 1 – Trích nguyên văn (gõ lại đề có sẵn)

```
Chỉ dựa vào nguồn "<TÊN NGUỒN>". Trích NGUYÊN VĂN <các câu cần lấy, vd: Phần I câu 1 đến câu 6>.
Không tóm tắt, không sửa số liệu, không thêm câu ngoài nguồn. Nếu nguồn có đáp án/lời giải thì chép kèm, không có thì để "".
Viết mọi công thức toán bằng LaTeX trong $...$ (phân số \frac, căn \sqrt, vectơ \overrightarrow{AB}, độ ^\circ).
Câu có hình: ghi vào "de" dòng [HÌNH: mô tả hình].
Trả lời DUY NHẤT một khối ```json chứa mảng đối tượng với các trường:
loai (TN|DS|TLN|TL), muc (N|H|V|C – em ước lượng), dang, de, phuong_an (mảng 4 chuỗi, không ghi "A."), dap_an, loi_giai, nguon.
Không viết gì ngoài khối json.
```

## MẪU 2 – Soạn câu bám nguồn (câu mới theo bài)

```
Dựa vào các nguồn về "<TÊN BÀI, vd: Toán 10 KNTT – Bài 9. Tích của một vectơ với một số>" (SGK, SBT, đề cũ trong sổ này).
Soạn <N> câu hỏi MỚI cho dạng "<TÊN DẠNG>": <vd: 3 TN mức N, 2 TN mức H, 1 DS mức V, 2 TLN mức V>.
Yêu cầu:
- Đúng phạm vi bài, không dùng kiến thức lớp trên; bám ví dụ – bài tập trong nguồn nhưng đổi số liệu/ngữ cảnh.
- <tuỳ chọn: ưu tiên toán thực tế gần gũi học sinh TP.HCM>.
- TN: đúng 1 đáp án, 3 phương án nhiễu theo lỗi sai thường gặp; lời giải không ghi "Chọn A".
- DS: 4 mệnh đề độc lập, khó tăng dần a→d; lời giải từng ý mở đầu "Đúng." hoặc "Sai.".
- TLN: đáp số là số, tối đa 4 ký tự kể cả dấu phẩy, dùng dấu phẩy thập phân.
- Mỗi câu ghi "nguon" là ví dụ/bài tập trong nguồn đã dựa vào.
- Công thức LaTeX trong $...$.
Trả lời DUY NHẤT một khối ```json chứa mảng đối tượng với các trường:
loai, muc, dang, de, phuong_an, dap_an, loi_giai, nguon. Không viết gì ngoài khối json.
```

## MẪU 3 – Hỏi kiến thức để kiểm chứng (khi em nghi ngờ một câu)

```
Theo nguồn, <phát biểu/công thức/định nghĩa cần kiểm>? Trả lời ngắn, trích câu trong nguồn và ghi trang.
```
