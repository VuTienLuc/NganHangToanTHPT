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

## Các lệnh

```bash
python3 scripts/lap_chi_muc.py                                   # sau mỗi lần thêm/sửa câu
python3 scripts/tao_mau_ma_tran.py GHK1_12 --pham-vi 2D1,2D2,2H2   # sinh bảng ma trận để điền
python3 scripts/tron_de.py ma-tran/GHK1_12.csv --thu              # xem trước câu được chọn
python3 scripts/tron_de.py ma-tran/GHK1_12.csv --so-ma-de 4       # xuất đề
```
(`scripts/tach_cau.py` chỉ chạy lại khi muốn chuyển đổi lại từ dữ liệu phần mềm — sẽ cất bản hiện tại vào `_cu/`.)

## Xuất đề thi theo ma trận (3 phần: Trắc nghiệm – Đúng/Sai – Trả lời ngắn)

**1. Sinh bảng ma trận.** `tao_mau_ma_tran.py <tên> --pham-vi <chương,…>` tạo `ma-tran/<tên>.csv`:
mỗi dòng một dạng toán, cột `kho_TN(N/H/V/C)` cho biết kho đang có bao nhiêu câu mỗi mức.
Mở bằng Excel/Numbers, điền số câu cần lấy vào các cột `TN_N … TN_C`, `DS_N … DS_C`, `TLN_N … TLN_C`
(và `TL_…` nếu có tự luận), để trống = 0, lưu lại dạng CSV.
Excel cài tiếng Việt (dấu phân cách `;`) thì thêm `--cham-phay` khi sinh bảng.

**2. Thông tin đầu đề** (Sở, trường, năm học, thời gian) đặt một lần trong `cau_hinh.json → thong_tin_de`.
Tên kỳ thi, môn/lớp, số mã đề… ghi trong một file JSON đi kèm (mẫu `ma-tran/VD_GHK1_12.json`):

```json
{"ten": "GHK1_12A", "ten_ky_thi": "ĐỀ KIỂM TRA GIỮA HỌC KỲ I", "mon": "TOÁN -- Lớp 12",
 "so_ma_de": 4, "ma_de_bat_dau": 101, "sap_xep": "do_kho", "ma_tran_csv": "ma-tran/GHK1_12.csv"}
```
- `sap_xep`: `ngau_nhien` · `do_kho` (N→H→V→C) · `noi_dung` (theo chương/bài) · `noi_dung_do_kho`
- `xao_phuong_an`: đảo A/B/C/D của câu trắc nghiệm (tự bỏ qua câu có lời giải ghi "Chọn A…" hay phương án "Cả A và B"). Câu Đúng/Sai không đảo ý.
- `moi_ma_de_cau_khac_nhau`: `true` = mỗi mã đề bốc bộ câu khác; mặc định các mã đề cùng bộ câu, chỉ hoán vị.
- `tranh_cau_da_dung`: ưu tiên câu chưa dùng ở đề trước (`du-lieu/lich_su_dung.json`).
- Chương trình báo khi kho thiếu câu cho một ô ma trận, và nhắc nếu đề không đúng cấu trúc 12–4–6.
- Ma trận viết thẳng bằng JSON (không cần CSV) vẫn dùng được: xem `ma-tran/vi_du_GHK1_lop12.json`.

**3. Kết quả** trong `de-da-ra/<tên>/`:

| File | Dùng để |
|---|---|
| `<tên>_101.tex`, `_102.tex`… | Đề phát cho học sinh: đầu đề Sở/Trường, ô Mã đề, PHẦN I–II–III, "HẾT", chân trang "Trang x/y – Mã đề" |
| `<tên>_101_LoiGiai.tex`… | Đề + lời giải chi tiết + bảng đáp án |
| `<tên>_TatCa_De.tex` | Mọi mã đề trong một file để in một lần |
| `<tên>_TatCa_LoiGiai.tex` | Mọi mã đề kèm lời giải |
| `dap_an_ngang.csv` | Mỗi mã đề một dòng (I.1…I.12, II.1…II.4 dạng ĐSĐS, III.1…III.6) — mở bằng Excel |
| `dap_an.csv`, `danh_sach_cau.csv` | Đáp án từng câu kèm mã câu gốc; danh sách câu đã dùng |

Khung đề chính thức nằm ở `khung/DeThiChinhThuc/mau_de.tex` (in đen trắng). Muốn dạng ôn tập có màu
như phần mềm cũ thì ghi `"khung": "DeThi"` trong file JSON.

## Biên dịch đề
Mở file trong `de-da-ra/<tên>/` bằng TeXstudio, biên dịch **pdfLaTeX** như các đề cũ của phần mềm
(cần gói `vietnam` — có sẵn trong MacTeX đầy đủ). Hoặc thêm `--bien-dich` khi trộn.
Chữ ở đầu/chân trang sửa trong `khung/DeThi/Khaibao/HeaderAndFooter.tex`.

## Tra cứu nhanh
`du-lieu/thong_ke_theo_dang.csv` (mở bằng Excel/Numbers): số câu theo dạng × loại × mức.
`du-lieu/nganhang.sqlite`: mở bằng "DB Browser for SQLite" để lọc câu.
