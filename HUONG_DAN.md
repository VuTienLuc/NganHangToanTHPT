# Ngân hàng câu hỏi cá nhân — Hướng dẫn

Thư mục này **không đụng** đến dữ liệu gốc của phần mềm NganHangTHPT (vẫn dùng được như cũ trên Windows).
Mọi thứ chạy bằng Python 3 trên Mac (Terminal), mở thư mục `NganHangCaNhan` rồi gõ lệnh.

## Cấu trúc

| Thư mục / file | Nội dung |
|---|---|
| `cau-hoi/lop10, lop11, lop12/<chương>/<dạng>.tex` | **Kho chính** — mỗi dạng toán một file, đã gỡ mã hoá. Thầy sửa/thêm câu trực tiếp ở đây |
| `cau-hoi/_chua_phan_loai/` | 198 câu chưa có mã `%[..]` — gắn mã rồi chuyển vào đúng file dạng |
| `ma-tran/*.json` | Ma trận đề (mẫu: `vi_du_GHK1_lop12.json`) |
| `khung/DeThi/` | Khung LaTeX in đề (Khaibao, ex_test.sty…); `mau_de.tex` là phần đầu file đề |
| `de-da-ra/<tên đề>/` | Đề đã trộn: mỗi mã đề 1 file đề + 1 file lời giải, `dap_an.csv` |
| `du-lieu/` | Chỉ mục (`nganhang.sqlite`, `chi_muc.jsonl`), thống kê, báo cáo, lịch sử dùng câu |
| `cau_hinh.json` | Quy đổi mức độ B/Y/T/K/G → N/H/V/C (em đoán, thầy sửa nếu khác) |
| `_cu/` | Bản cũ/tạm, xoá được |

## Mỗi câu hỏi

```latex
\begin{ex}%[2D1N1-2]%[ma:e42229d3]
   ...
\end{ex}
```
- `%[2D1N1-2]`: lớp 12 (2), Đại số (D), chương 1, mức N, bài 1, dạng 2.
- `%[ma:e42229d3]`: mã riêng của câu (để theo dõi câu đã dùng). Câu mới chưa có mã sẽ được tự gắn.

## Ba lệnh

```bash
python3 scripts/lap_chi_muc.py                       # sau mỗi lần thêm/sửa câu
python3 scripts/tron_de.py ma-tran/de_cua_thay.json --thu   # xem trước câu được chọn
python3 scripts/tron_de.py ma-tran/de_cua_thay.json         # tạo đề thật
```
(`scripts/tach_cau.py` chỉ chạy lại khi muốn chuyển đổi lại từ dữ liệu phần mềm — sẽ cất bản hiện tại vào `_cu/`.)

## Viết ma trận

```json
{"ten": "GHK1_12A1", "tieu_de": "ĐỀ KIỂM TRA GIỮA HỌC KỲ I — TOÁN 12",
 "so_ma_de": 4, "ma_de_bat_dau": 101, "xao_cau": true, "xao_phuong_an": true,
 "moi_ma_de_cau_khac_nhau": false, "tranh_cau_da_dung": true,
 "phan": [
   {"loai": "TN",  "yeu_cau": [{"dang": "2D1?1", "muc": "N", "so": 3}]},
   {"loai": "DS",  "yeu_cau": [{"dang": "2D1", "so": 2}]},
   {"loai": "TLN", "yeu_cau": [{"dang": "2D1?3-6", "muc": ["V","C"], "so": 2}]}
 ]}
```
- `loai`: TN (4 phương án) · DS (Đúng/Sai) · TLN (trả lời ngắn) · TL (tự luận)
- `dang`: `2D1` = cả chương · `2D1?2` = bài 2 · `2D1?2-3` = đúng dạng 3 (`?` thay cho chữ mức)
- `muc`: N/H/V/C hoặc danh sách; bỏ trống = mọi mức
- Xáo phương án tự **bỏ qua** câu có lời giải ghi "Chọn A…" hay phương án kiểu "Cả A và B".
- Câu đã dùng ghi vào `du-lieu/lich_su_dung.json`; lần sau ưu tiên câu chưa dùng.

## Biên dịch đề
Mở file trong `de-da-ra/<tên>/` bằng TeXstudio, biên dịch **pdfLaTeX** như các đề cũ của phần mềm
(cần gói `vietnam` — có sẵn trong MacTeX đầy đủ). Hoặc thêm `--bien-dich` khi trộn.
Chữ ở đầu/chân trang sửa trong `khung/DeThi/Khaibao/HeaderAndFooter.tex`.

## Tra cứu nhanh
`du-lieu/thong_ke_theo_dang.csv` (mở bằng Excel/Numbers): số câu theo dạng × loại × mức.
`du-lieu/nganhang.sqlite`: mở bằng "DB Browser for SQLite" để lọc câu.
