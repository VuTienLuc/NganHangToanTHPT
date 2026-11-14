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

## Ứng dụng "Ra đề theo ma trận" (nhấp đúp, không cần gõ lệnh)

Nhấp đúp **`Ra de theo ma tran.app`** trong thư mục này. Giao diện mở trong trình duyệt (chạy ngay trên máy, không cần mạng):

1. Cột trái: tích các chương cần ra đề.
2. Bảng giữa: mỗi dòng một dạng toán, mỗi ô là số câu cần lấy theo loại (Trắc nghiệm / Đúng-Sai / Trả lời ngắn) và mức (N/H/V/C). Số nhỏ dưới ô là số câu kho đang có.
   Nút **Tự động điền** rải đều số câu theo "Mục tiêu" (mặc định 12 TN – 4 ĐS – 6 TLN) qua các dạng đã chọn.
3. Điền thông tin đề (tên kỳ thi, môn – lớp, số mã đề…), bấm **Xem trước** để xem câu được chọn, rồi **Xuất đề**.
   Nếu máy có MacTeX, ứng dụng tự biên dịch 2 file gộp ra PDF; nút **Mở thư mục đề** mở kết quả trong Finder.
4. **Lưu ma trận** để lần sau mở lại (ô "Mở ma trận đã lưu…"). **Cập nhật kho** sau khi thầy sửa/thêm câu trong `cau-hoi/`.
5. Bấm **Thoát** khi xong (ứng dụng cũng tự tắt sau 3 phút không còn cửa sổ nào mở).

Nếu macOS báo không mở được ứng dụng: nhấp phải vào file `.app` → **Mở** → **Mở** (chỉ cần làm một lần),
hoặc nhấp đúp `Ra de theo ma tran.command` (mở bằng Terminal). Nhật ký lỗi: `/tmp/ra_de_theo_ma_tran.log`.

## Thêm câu hỏi mới vào ngân hàng

**Cách 1: thêm vài câu.** Mở file dạng tương ứng trong `cau-hoi/lopXX/<chương>/<dạng>.tex`, chép một khối mẫu từ
`mau_cau_moi.tex` vào cuối file, sửa nội dung. Mã `%[ma:…]` không cần gõ, chương trình tự gắn.
Xong bấm **Cập nhật kho** trong ứng dụng (hoặc `python3 scripts/lap_chi_muc.py`).

**Cách 2: nhập cả file** (câu thầy tự soạn, đồng nghiệp gửi, đề cũ, file đã trộn của phần mềm cũ…).
Trong ứng dụng bấm **Nhập câu hỏi** → chọn một hay nhiều file `.tex` → xem trước → **Nhập vào ngân hàng**. Hoặc:
```bash
python3 scripts/nhap_cau.py duong/dan/file1.tex file2.tex --thu   # xem trước, chưa ghi
python3 scripts/nhap_cau.py duong/dan/file1.tex file2.tex         # nhập thật
```
Chương trình tự: tách từng câu, xếp vào đúng file dạng theo mã `%[..]` (tạo file dạng mới nếu chưa có),
**bỏ câu trùng** với câu đã có, gỡ lệnh rác nếu file bị mã hoá, gắn mã câu, rồi cập nhật chỉ mục.
Câu chưa có mã dạng vào `cau-hoi/_chua_phan_loai/<tên file>.tex`; gắn mã cho chúng rồi chuyển vào đúng file dạng.

**Nhập file .txt / .json** (cùng nút **Nhập câu hỏi**, cùng lệnh `nhap_cau.py`):
- `.txt` / `.md`: chứa các khối `\begin{ex}…\end{ex}` đúng cấu trúc như file `.tex` (AI trả về kèm rào ```latex cũng được).
- `.json`: mảng câu hỏi, mỗi câu là
  - một chuỗi chứa sẵn khối `\begin{ex}…\end{ex}`, hoặc
  - một đối tượng theo trường — đúng **mẫu 13 trường** của thầy (xem `mau_cau_moi.json`):
    `Loại` (Trắc nghiệm | Đúng/Sai | Trả lời ngắn | Tự luận), `Mức độ nhận thức`, `Nội dung`,
    `Lựa chọn A / Mệnh đề a` … `D`, `Đáp án đúng` (`B` | `a-Đúng, b-Sai, c-Đúng, d-Sai` | `2,5`), `Lời giải`;
    thêm trường `Mã dạng` (vd `2D1N1-2`) nếu có. Tên trường tiếng Anh (`question`, `options`, `answer`, `solution`…) cũng nhận.
  - Công thức trong `$…$`; viết `\\frac` hay lỡ viết `\frac` đều đọc đúng.
- Khi nhập, ứng dụng hỏi **mã dạng mặc định** cho các câu chưa có mã (vd `2D1?1-2`, dấu `?` tự thay bằng mức độ của câu
  N/H/V/C). Để trống thì câu chưa có mã vào `cau-hoi/_chua_phan_loai/`. Dòng lệnh: thêm `--ma-dang 2D1?1-2`.

**Cách 3: nhờ AI gõ lại đề thi** (đề PDF, ảnh chụp, Word chưa có LaTeX)
1. Trong ứng dụng, tích các chương của đề ở cột trái → bấm **Prompt cho AI** → **Chép prompt**
   (hoặc dùng file soạn sẵn theo lớp trong `prompt-ai/prompt_go_de_lop10.md`, `…lop11.md`, `…lop12.md`;
   hay `python3 scripts/tao_prompt.py --pham-vi 2D1,2H2 --ra prompt.md`).
2. Mở ChatGPT / Gemini / Claude, dán prompt, **đính kèm đề**, gửi.
   Prompt yêu cầu AI: mỗi câu một khối `ex`/`bt`, gắn mã dạng lấy từ danh mục (đúng lớp – chương – bài – dạng – mức N/H/V/C),
   trắc nghiệm đúng một `\True` và lời giải không ghi "Chọn A", Đúng/Sai đủ 4 `\itemch` (để đảo ý a, b, c được),
   trả lời ngắn có `\shortans` dấu phẩy thập phân; câu không chắc ghi `% KIEM_TRA`, hình chưa vẽ ghi `% CAN_VE_HINH`.
3. Chép khối mã AI trả về, lưu thành file `.tex` → **Nhập câu hỏi** → xem trước → nhập.
   Câu AI ghi `%[?]` (không tìm được dạng) vào `cau-hoi/_chua_phan_loai/` để thầy phân loại.
   Nên dò lại các câu có `% KIEM_TRA` / `% CAN_VE_HINH` (tìm trong thư mục `cau-hoi/`).
4. Khi nhập, chương trình **tự sửa** số thập phân trong công thức (`$15,25$` → `$15{,}25$`) và **cảnh báo** (⚠ ở bước xem trước):
   Đúng/Sai thiếu `itemchoice` hoặc lời giải ghi "Đúng/Sai" không khớp `\True`, đáp số trả lời ngắn quá 4 ô,
   lời giải trắc nghiệm ghi "Chọn A…". Câu có cảnh báo vẫn nhập được; sửa trong file dạng sau.

**Cách 4: nhờ AI soạn câu hỏi MỚI theo bài học** (từ SGK, chuyên đề, phiếu… của bài)
1. Bấm **Prompt cho AI** → **Soạn câu hỏi theo bài học**.
2. Chọn **Lớp → Chương → Bài học**; tích các **dạng toán** muốn có (mỗi dạng hiện số câu đang có trong kho — dạng ít câu nên ưu tiên).
3. Điền **số câu theo loại × mức** (Trắc nghiệm / Đúng-Sai / Trả lời ngắn / Tự luận × N / H / V / C),
   tên tài liệu sẽ đính kèm, **cách soạn** (bám sát ví dụ – bài tập của tài liệu / soạn mới / kết hợp),
   tuỳ chọn ưu tiên toán thực tế và yêu cầu thêm → **Tạo prompt** → **Chép prompt**.
4. Mở AI, dán prompt, **đính kèm tài liệu của bài**, gửi. Prompt buộc AI: đúng phạm vi bài, rải đều các dạng đã chọn,
   đúng số câu từng mức, nhiễu trắc nghiệm theo lỗi sai thường gặp, đáp án rải đều A–D, Đúng/Sai tăng dần độ khó a → d,
   lời giải chi tiết, đúng định dạng kho và tự kiểm tra trước khi trả.
5. Lưu kết quả thành `.txt`/`.tex` → **Nhập câu hỏi** → xem trước → nhập.

**Bảng mã dạng (tra cứu nhanh):** nút **Bảng mã dạng** trên thanh đầu, hoặc nút **Tra mã…** cạnh ô gán mã khi nhập câu.
Lọc theo lớp, gõ từ khoá không cần dấu (vd `trung vi`, `tich vo huong`, `0D6?3`), chọn mức N/H/V/C hoặc giữ `?`;
bấm một dòng: đang gán mã thì điền thẳng vào ô, không thì chép `%[mã]` để dán vào dòng `\begin{ex}` của câu.
Bản đầy đủ dạng bảng tính: `du-lieu/danh_muc_ma_dang.csv`.

**Quy ước để câu được nhận đúng loại:**
- Trắc nghiệm: `\begin{ex}` + `\choice{…}{…}{…}{…}`, đúng **một** `\True`
- Đúng/Sai: `\begin{ex}` + `\choiceTF{…}{…}{…}{…}`, ý đúng có `\True`
- Trả lời ngắn: `\begin{bt}` + `\shortans{đáp số}`
- Tự luận: `\begin{bt}` không có `\shortans`
- Mã dạng ngay sau `\begin{..}`: `%[2D1N1-2]` → tra trong `du-lieu/danh_muc_ma_dang.csv`

Sau khi nhập, nhớ lưu lên GitHub: `git add -A && git commit -m "Nhập câu …" && git push`.

## Các lệnh

```bash
python3 scripts/lap_chi_muc.py                                   # sau mỗi lần thêm/sửa câu
python3 scripts/tao_mau_ma_tran.py GHK1_12 --pham-vi 2D1,2D2,2H2   # sinh bảng ma trận để điền
python3 scripts/tron_de.py ma-tran/GHK1_12.csv --thu              # xem trước câu được chọn
python3 scripts/tron_de.py ma-tran/GHK1_12.csv --so-ma-de 4 --bien-dich   # xuất đề + PDF
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
- `xao_phuong_an`: đảo A/B/C/D của câu trắc nghiệm (tự bỏ qua câu có lời giải ghi "Chọn A…" hay phương án "Cả A và B").
- `xao_y_dung_sai`: câu Đúng/Sai đảo thứ tự ý **a, b, c**, **giữ ý d (ý khó) ở cuối**; lời giải từng ý đảo theo.
  Tự bỏ qua câu có nội dung nhắc "ý a", "b)"… hoặc lời giải không chia đủ 4 ý (`\\itemch`).
- **In tiết kiệm giấy** (khung đề chính thức): `"tiet_kiem": true, "co_chu": 10` (hoặc 11) — chữ nhỏ, lề hẹp, giãn dòng sát;
  thêm `"hai_cot": true` để in 2 cột (hình vẽ thu nhỏ 75%, hình cạnh đề chuyển xuống dưới). Thử với đề 12–4–6:
  chữ 12 = 5 trang · chữ 11 = 4 trang · chữ 10 = 4 trang · chữ 10 + 2 cột = 3 trang. Trong ứng dụng: ô **Khổ in** và **In 2 cột**.
- `moi_ma_de_cau_khac_nhau`: `true` = mỗi mã đề một bộ câu riêng (4 mã × 12 câu TN = 48 câu khác nhau); mặc định các mã đề cùng bộ câu, chỉ hoán vị.
- **Chọn ngẫu nhiên theo bài**: trong ứng dụng, hàng **Bài …** (nhãn "ngẫu nhiên theo bài") cũng có ô nhập; điền số ở đó thì
  hệ thống lấy câu ở **các dạng khác nhau trong bài**, mỗi mã đề phủ càng nhiều dạng càng tốt và các mã đề khác nhau về dạng.
  "Tự động điền" chọn được **theo từng dạng** hoặc **theo bài**. Trong bảng CSV là dòng `(CẢ BÀI …)` có mã kiểu `2D1?1`.
- **Bù câu thông minh** khi kho thiếu (nhất là lúc nhiều mã đề khác câu):
  1. lấy câu đúng dạng, đúng mức;
  2. thiếu thì lấy **mức cùng nhóm, cùng dạng**: nhóm 1 = Nhận biết + Thông hiểu (N↔H), nhóm 2 = Vận dụng + VDC (V↔C) — `bu_cung_nhom`;
  3. vẫn thiếu thì lấy dạng khác **cùng bài**, rồi bài khác **cùng chương**, giữ nhóm mức — `mo_rong_dang_khac`;
  4. còn thiếu nữa thì cho vài câu dùng chung giữa các mã (không bao giờ trùng trong cùng một mã).
  Câu bù được rải đều cho các mã đề để độ khó các mã ngang nhau; chương trình in rõ đã bù bao nhiêu câu, từ đâu.
- `cau_da_dung` — câu đã ra ở đề trước (ghi trong `du-lieu/lich_su_dung.json` mỗi lần xuất):
  `uu_tien` (mặc định: dùng câu chưa ra trước, hết mới lấy câu cũ ít dùng nhất) · `loai_bo` (**không bao giờ lấy lại**) · `khong` (không xét).
  Trong ứng dụng: ô số nhỏ dưới mỗi ô ma trận ghi `chưa dùng/tổng` (vd `8/12`); nút **Lịch sử đã dùng** xem các đề đã ra,
  **Bỏ một đề…** (trả câu của đề thử về kho) hoặc **Xoá toàn bộ lịch sử** (đầu năm học mới).
- Chương trình báo khi kho thiếu câu cho một ô ma trận, và nhắc nếu đề không đúng cấu trúc 12–4–6.
- Ma trận viết thẳng bằng JSON (không cần CSV) vẫn dùng được: xem `ma-tran/vi_du_GHK1_lop12.json`.

**3. Kết quả**: mỗi lần xuất tạo một thư mục riêng **`de-da-ra/<Tên kỳ thi> - <ngày-tháng-năm>/`**
(xuất lần nữa cùng ngày thì thêm "(2)", "(3)"…):

| File | Nội dung |
|---|---|
| `De_101.pdf` … `De_104.pdf` | Đề từng mã, in cho học sinh (đầu đề Sở/Trường, ô Mã đề, PHẦN I–III, HẾT) |
| `LoiGiai_101.pdf` … | Đề + lời giải + bảng đáp án từng mã |
| `DapAn.xlsx` | Đáp án mọi mã đề theo mẫu Chấm Phiếu AI: sheet **Đáp án**, ô A1 = `Câu`, dòng 1 là mã đề, các dòng `1…12`, `II.1…II.4` (dạng ĐSĐS), `III.1…III.6` (dấu phẩy thập phân); phông Times New Roman, có viền |
| `tex/` | Toàn bộ mã nguồn LaTeX: `De_101.tex`, `De_101_LoiGiai.tex`, `TatCa_De.tex` (mọi mã một file), khung Khaibao… |

PDF chỉ tự xuất khi máy có MacTeX (`pdflatex`). Không có thì mở các file trong `tex/` bằng TeXstudio, biên dịch pdfLaTeX 2 lần.
Nạp đáp án: Chấm Phiếu AI → ô **Đáp án** → **Nhập từ file Excel** → chọn `DapAn.xlsx`.

Khung đề chính thức nằm ở `khung/DeThiChinhThuc/mau_de.tex` (in đen trắng). Muốn dạng ôn tập có màu
như phần mềm cũ thì ghi `"khung": "DeThi"` trong file JSON.

## Ôn thi học kì (ma trận từng câu 12 TN · 4 Đúng/Sai · 6 Trả lời ngắn)

Nút **Ôn thi học kì** trên thanh đầu. Chọn **Lớp 9/10/11/12** và **Kỳ** (giữa/cuối HK I, II); bảng có sẵn ma trận mặc định
22 câu (theo KNTT), mỗi câu một dòng — sửa được **Chủ đề**, **Bài trong ngân hàng**, **Mức** (NB/TH/VD/VDC),
**Ngữ cảnh thực tế**, **Câu mẫu** (+ "Form mẫu": tạo câu mới cùng dạng; "Phân loại 9–10": câu khó). Bảng tự lưu theo lớp.
- **Ra đề từ ngân hàng**: mỗi dòng lấy đúng 1 câu theo bài + mức (thiếu mức thì bù mức cùng nhóm, rồi dạng khác cùng bài),
  xuất như nút Xuất đề (số mã đề, PDF, Word, Leftnote, Beamer, đáp án Excel… theo các ô ở khung chính). Lớp 9 chưa có trong kho.
- **Tạo prompt AI (nguồn ngoài)**: prompt cho ChatGPT/Gemini/Claude sinh đề **JSON** (`trac_nghiem`, `dung_sai`, `tra_loi_ngan`,
  kèm `ma_dang` chọn từ danh sách dạng của bài, `figures` là mã TikZ); tuỳ chọn số mã đề AI, giải thích bẫy sai lầm, tự phản biện.
  JSON AI trả về: **Trộn đề từ file** (ra mã đề, PDF, Word, đáp án) hoặc **Nhập câu hỏi** (đưa vào ngân hàng đúng dạng).

## Câu lạc bài — chuyển đúng dạng hoặc xoá

Nút **Câu lạc bài** trên thanh đầu, 2 thẻ:
- **Nghi lạc bài**: máy so nội dung từng câu với "hồ sơ từ khoá" của mọi bài học; câu nào giống một bài khác rõ hơn bài
  đang gắn thì liệt kê (xếp theo độ lệch, rõ nhất trước) kèm **gợi ý dạng đúng** (vd câu cấp số cộng đang nằm ở
  "Hàm số liên tục" → gợi ý `1D2?2-3 Số hạng tổng quát của cấp số cộng`). Lần đầu mất khoảng 15 giây.
- **Tìm câu theo nội dung**: gõ cụm từ (không cần dấu), mã dạng hoặc mã câu, Enter — để tự tìm câu lạc mà thầy biết.
Mỗi câu: chọn dạng gợi ý, hoặc gõ mã vào ô bên / bấm **Tra mã…** (mở Bảng mã dạng, bấm dòng là điền), rồi
- **Chuyển**: đổi mã `%[..]` (giữ mức N/H/V/C cũ nếu mã có `?`) và dời câu sang file của dạng mới;
- **Xoá**: gỡ câu khỏi kho; **Đúng rồi**: câu xếp đúng, lần sau không báo (lưu `du-lieu/da_kiem_tra_lac.json`).
Có thể tích nhiều câu rồi dùng các nút ở chân hộp thoại. Mọi câu bị chuyển/xoá đều có bản sao trong `du-lieu/da_xoa/`.
Dòng lệnh: `python3 scripts/quan_ly_cau.py` (thống kê) · `python3 scripts/quan_ly_cau.py --tim "cấp số cộng"`.

## Câu hỏi trùng — dò và xoá

Nút **Câu trùng** trên thanh đầu dò toàn bộ ngân hàng (khoảng 10 giây), chia 3 thẻ:
- **Trùng hoàn toàn**: cùng đề bài và cùng bộ phương án/đáp số (chỉ khác cách gõ, khoảng trắng, thứ tự phương án, lời giải).
  Mặc định đã **chọn sẵn các bản thừa**, giữ 1 bản "nên giữ" (đã phân loại dạng, lời giải dài hơn, có hình).
- **Cùng đề, khác phương án**: cùng lời dẫn nhưng khác phương án/đáp án — thường là câu khác nhau, chỉ xoá khi chắc chắn.
- **Gần giống (≥ 90%)**: khác vài chữ, vài số — xem kỹ trước khi xoá.
Mỗi câu hiện mã dạng, loại, đáp án, độ dài lời giải, số lần đã dùng, file chứa, nội dung; mở "Mã LaTeX" để xem đầy đủ.
Tích/bỏ tích rồi **Xoá câu đã chọn** (không cho xoá hết cả một nhóm). Câu bị xoá được lưu bản sao trong
`du-lieu/da_xoa/xoa_trung_<thời điểm>.tex` để khôi phục; chỉ mục tự lập lại. Dòng lệnh: `python3 scripts/cau_trung.py`.

## Trộn đề có sẵn từ file (đề AI gõ lại, đề tự soạn…)

Bấm **Trộn đề từ file** → chọn file `.tex` / `.txt` / `.json` đúng cấu trúc `\begin{ex}…\end{ex}` (ví dụ đề AI gõ lại bằng
"Prompt cho AI → Gõ lại đề thi") → chọn số mã đề, mã bắt đầu, thứ tự câu (đảo trong từng phần / giữ nguyên / theo độ khó),
đảo phương án, đảo ý a b c, **cỡ chữ 10/11/12**, PDF 2 cột, **Xuất PDF**, **Xuất Word**, Word K12Online, quyển đề cương → **Trộn đề**.
Mọi mã đề dùng đúng các câu trong file. Kết quả giống khi ra đề theo ma trận: thư mục `<Tên kỳ thi> - <ngày>` gồm
`De_101.pdf`, `LoiGiai_101.pdf`, `Word_De_101.docx`, `Word_LoiGiai_101.docx`, `DapAn.xlsx` (Chấm Phiếu AI), `tex/`.
File gốc được lưu lại trong `de-da-ra/_nguon/`. Câu trong file không ghi vào lịch sử dùng câu của kho.
Dòng lệnh: `python3 scripts/tron_de.py --tu-file de.txt --so-ma-de 4 --co-chu 11 --word-de --bien-dich`.

## Word đề thi (bố cục như đề PDF)

Ô **"Xuất Word đề thi (bố cục như PDF)"** (khi ra đề theo ma trận) hoặc ô **Xuất Word** (khi trộn từ file): mỗi mã đề 2 file
- `Word_De_101.docx`: đầu đề 2 cột (Sở/Trường – Kỳ thi/Năm học/Môn/Thời gian), "(Đề thi có N trang)", Họ tên/Số báo danh,
  ô **Mã đề 101**, PHẦN I/II/III, `Câu 1.`, phương án A. B. C. D. **tự xếp 4 cột / 2 cột / 1 cột** theo độ dài như đề PDF,
  ý a) b) c) d), "HẾT", chân trang `Trang x/y – Mã đề 101`.
- `Word_LoiGiai_101.docx`: như trên + lời giải dưới từng câu (đáp án đúng gạch chân) + bảng đáp án cuối.
- Cỡ chữ theo ô Khổ in / Cỡ chữ (10, 11, 12). Công thức: Equation của Word hoặc ảnh SVG (ô "Công thức trong Word").

## Bộ 4 file cho mỗi mã đề (như phần mềm cũ)

Ngoài `De_101.pdf` (đề in) và `LoiGiai_101.pdf` (đề + lời giải), mỗi mã đề có thêm (bật sẵn, bỏ tích nếu không cần):
- **`Leftnote_101.pdf`** — ô *Bản Leftnote (chừa lề ghi chú)*: đề in 0,7 bề rộng trang, 0,3 bên phải là cột **GHI CHÚ** có dòng kẻ
  để học sinh ghi lời giải, sửa lỗi sai cạnh câu hỏi.
- **`BeamerTrang_101.pdf`** — ô *Bản Beamer trình chiếu sửa bài*: trình chiếu 16:9, nền trắng chữ đen, chữ to, **mỗi slide 1 câu**
  (chiếu lên bảng để viết, sửa bài trực tiếp). Slide đề → bấm tiếp: tô đáp án đúng / hiện Đúng–Sai từng ý / hiện đáp số
  → slide **Lời giải câu n** (dài thì tự sang nhiều slide).
- **`BeamerXanh_101.pdf`** — cùng nội dung, nền xanh, thanh tiêu đề xanh, hiệu ứng chuyển slide (thao giảng, ôn tập).
- Ô **"Đề bài trên slide Beamer chiếm"**: *2/3 trên* (mặc định) hoặc *1/2 trên* — chữ đề dồn sát mép trên, phần dưới màn hình
  để trống cho giáo viên viết, vẽ khi giảng; *Cả màn hình* — chữ to nhất. Chỉ áp dụng slide đề bài, slide lời giải giữ nguyên.
Cùng thứ tự câu, cùng phương án với mã đề tương ứng. Mở PDF Beamer bằng chế độ toàn màn hình (Preview/Acrobat) để trình chiếu.
Mã nguồn trong `tex/` (`Leftnote_101.tex`, `BeamerTrang_101.tex`, `BeamerXanh_101.tex`).

## Quyển đề cương ôn tập (2 file PDF: Câu hỏi / Lời giải)

Ô **"Gộp thành quyển đề cương ôn tập (PDF)"** (bật sẵn) tạo thêm 2 file trong thư mục đề:
- `Đề cương ôn tập - <Tên kỳ thi> - Câu hỏi.pdf`: bìa → mục lục → tất cả mã đề (không lời giải).
- `Đề cương ôn tập - <Tên kỳ thi> - Lời giải.pdf`: bìa → mục lục → lời giải chi tiết + bảng đáp án từng đề.

Chân trang mọi trang: `GV: <tên giáo viên> | <tên kỳ thi> | Trang x/y`. Tên giáo viên mặc định **Vũ Tiến Lực**, sửa ở ô
"Giáo viên" (hoặc `giao_vien` trong `cau_hinh.json` / ma trận). Mã nguồn: `tex/DeCuong_CauHoi.tex`, `tex/DeCuong_LoiGiai.tex`.
Bỏ quyển này: bỏ tích ô, hoặc `"de_cuong": false`.

## Xuất Word theo mẫu K12Online

Tích **Xuất Word K12Online** trong ứng dụng, hoặc thêm `--word` khi chạy `tron_de.py`
(chạy riêng: `python3 scripts/k12word.py "de-da-ra/<thư mục đề>"`). Mỗi mã đề có thêm `Word_K12Online_<mã>.docx`:

- **Phần I:** Trắc nghiệm nhiều lựa chọn — `Câu 1:` … `A.` `B.` `C.` `D.` (chữ cái đáp án đúng **gạch chân**), rồi `Lời giải:`.
- **Phần II:** Trắc nghiệm đúng – sai — `Câu 1:` … mỗi ý `a)` `b)` `c)` `d)` (ý **đúng** gạch chân `a)`), sau mỗi ý là `Lời giải:` của ý đó.
- **Phần III:** Trả lời ngắn — `Câu 1:` … `Đáp án:` (dòng dưới là đáp số, dấu phẩy thập phân) rồi `Lời giải:`.
- Số câu đánh lại từ 1 ở mỗi phần. Chữ Times New Roman 12.
- **Công thức** chuyển thành **Equation của Word** (thẳng dòng với chữ, sửa được, K12Online nhận được).
  Cần **pandoc**: `brew install pandoc` hoặc `pip3 install pypandoc_binary`. Không có pandoc thì công thức thành ảnh SVG.
- Bảng biến thiên, hình vẽ (và công thức pandoc không đọc được) là **ảnh SVG** sắc nét (kèm PNG 600 dpi) — cần MacTeX đầy đủ.
- **Công thức là ảnh SVG**: chọn ô "Công thức trong Word → Ảnh SVG sắc nét, thẳng hàng chữ" (hoặc `--word-svg`).
  Mỗi công thức được LaTeX vẽ cỡ 12pt bằng phông Times (khớp chữ Times New Roman) và hạ xuống đúng phần nằm dưới
  chân chữ (Font → Advanced → Position: Lowered) nên **thẳng hàng với dòng chữ trong Word (Windows/Mac)**.
  Pages, LibreOffice, Google Docs không hiểu thông số hạ ảnh nên ở đó công thức sẽ nhô lên — hãy mở bằng Word.

- **Thứ tự câu Word K12Online** (ô cạnh "Xuất Word K12Online"):
  - *Theo từng mã đề (đã trộn)*: mỗi mã đề một file `Word_K12Online_101.docx`…
  - *Giữ thứ tự đã chọn trong ma trận (không đảo)*: **1 file** `Word_K12Online_ThuTuDaChon.docx`, mỗi phần xếp câu đúng
    thứ tự các dạng trên bảng ma trận (theo chương trình: bài → dạng, ví dụ câu 1 mệnh đề, câu 2 tập hợp…; trong một dạng
    theo mức N → H → V → C), **không đảo câu, không đảo phương án/ý** — K12Online tự trộn khi giao bài.
    Khi trộn đề từ file: giữ đúng thứ tự câu trong file. Dòng lệnh: `--k12-giu-thu-tu`.
  - *Cả hai*.

## Biên dịch đề
Mở file trong `de-da-ra/<tên>/` bằng TeXstudio, biên dịch **pdfLaTeX** như các đề cũ của phần mềm
(cần gói `vietnam` — có sẵn trong MacTeX đầy đủ). Hoặc thêm `--bien-dich` khi trộn.
Chữ ở đầu/chân trang sửa trong `khung/DeThi/Khaibao/HeaderAndFooter.tex`.

## Tra cứu nhanh
`du-lieu/thong_ke_theo_dang.csv` (mở bằng Excel/Numbers): số câu theo dạng × loại × mức.
`du-lieu/nganhang.sqlite`: mở bằng "DB Browser for SQLite" để lọc câu.

## Phiếu bài học · chuyên đề · ôn tập chương

Nút **Phiếu bài học** trên thanh đầu ứng dụng.

1. Chọn **Lớp → Chương**, tích **bài**:
   - 1 bài → *Phiếu bài học*; vài bài → *Phiếu chuyên đề*; bấm **cả chương** → *Phiếu ôn tập chương*.
2. Tích/bỏ **dạng toán** (bên cạnh là số câu trong kho TN/ĐS/TLN).
3. **Thời lượng** 45 phút (mặc định 8 TN · 2 ĐS · 2 TLN) hoặc 90 phút (12 · 4 · 6) — sửa được số câu.
   Bài tập về nhà có **cùng số câu, cùng dạng, cùng mức** nhưng là câu khác.
   **Bổ sung câu vận dụng / vận dụng cao** (tích ô, nhập số câu): thêm mục "Vận dụng – Vận dụng cao" vào cả Luyện tập và
   Bài tập về nhà (câu khác nhau, rải đều các dạng, nhãn đỏ "Vận dụng"/"Vận dụng cao"), có trong bảng đáp án và lời giải.
   Kho không đủ câu mức đó thì ứng dụng báo thiếu.
4. **I. Kiến thức trọng tâm** — chọn cách in trên phiếu:
   - *In sẵn nội dung*: in nội dung LaTeX thầy dán (có nút *Prompt AI soạn kiến thức trọng tâm*);
   - *Không in (tiết kiệm giấy)*: bỏ hẳn mục I; phiếu đánh số lại I. LUYỆN TẬP, II. BÀI TẬP VỀ NHÀ
     (kiến thức đã soạn vẫn được lưu và vẫn chiếu trên Beamer);
   - *Dòng trống để học sinh tự ghi*: khung "Kiến thức cần nhớ" (4 dòng; 6 dòng với 90 phút) + "Phương pháp" từng dạng (2 dòng; 3 dòng với 90 phút).
   Nội dung đã soạn vẫn được lưu ở `du-lieu/kien_thuc/` và vẫn dùng cho Beamer (chiếu phương pháp để học sinh chép vào phiếu).
   Ô nội dung để trống thì phiếu luôn có dòng kẻ.
5. In ấn: cỡ chữ 10/11/12, 2 cột tiết kiệm giấy. Chân trang: **GV** (ô Giáo viên ở khung chính) · tên phiếu · Trang x/y.

Kết quả ở `de-da-ra/Phiếu … - <tên> - <ngày>/` — mỗi phiếu có **file câu hỏi** (phát học sinh) và **file lời giải** riêng
(bảng đáp án đầu trang, rồi lời giải chi tiết), cả PDF lẫn TeX (thư mục `tex/`, sửa rồi biên dịch lại được):

| PDF | TeX câu hỏi | TeX lời giải |
|---|---|---|
| `<tên>.pdf` – đầy đủ I + II + III | `PhieuBaiHoc.tex` | `PhieuBaiHoc_LoiGiai.tex` |
| `<tên> - Trên lớp.pdf` – I + II | `PhieuTrenLop.tex` | `PhieuTrenLop_LoiGiai.tex` |
| `<tên> - Về nhà.pdf` – bài tập về nhà | `PhieuVeNha.tex` | `PhieuVeNha_LoiGiai.tex` |

| `<tên> - Trình chiếu.pdf` – Beamer 16:9 | `PhieuBeamer.tex` | |

**Beamer trình chiếu** (tích ô *Beamer trình chiếu*): bìa → nội dung các dạng → kiến thức trọng tâm → mỗi dạng một màu:
slide mở dạng → slide **PHƯƠNG PHÁP GIẢI** (các bước đánh số tròn màu) → **Câu 1 – Ví dụ mẫu** (bấm tiếp hiện đáp án, rồi lời giải)
→ **Câu 2 – Học sinh tự làm** (đề chiếm 2/3 trên, chừa chỗ viết; bấm tiếp hiện đáp án, rồi lời giải) → slide giao bài về nhà.
Câu 1, 2 lấy từ phần Luyện tập của phiếu (đúng câu học sinh có trên phiếu).
Phương pháp từng dạng lấy từ ô Kiến thức trọng tâm: dòng `%% DANG <mã dạng>` (prompt AI đã hướng dẫn) hoặc mục `\textbf{Dạng n. …}`;
được lưu ở `du-lieu/phuong_phap/` để dùng lại cho phiếu sau. Chưa có thì slide phương pháp để các bước trống cho thầy ghi bảng.

**Kiểu phiếu "Chỉ tự luận"** (ô *Kiểu phiếu*): mỗi dạng một khối 2 cột song song —
trái **VÍ DỤ MẪU** (đề + lời giải in sẵn), phải **TỰ LUYỆN**: câu tương tự (mặc định 2) + câu vận dụng (1 hoặc 2, nhãn đỏ).
Hai cột có nền màu, mép trên – mép dưới luôn bằng nhau, tự ngắt sang trang sau khi dài (không bỏ trống nửa trang), dòng kẻ làm bài chỉnh được.
Nguồn câu: tự luận → trả lời ngắn → trắc nghiệm đổi sang tự luận (bỏ phương án, chỉ nhận câu có đề tự đủ nghĩa).
Xuất: `<tên>.pdf` (phiếu học sinh), `<tên> - Lời giải.pdf` (lời giải các bài tự luyện, 2 cột), `<tên> - Trình chiếu.pdf`
(Beamer cùng loại phiếu: phương pháp → ví dụ mẫu → từng bài tự luyện: đề chiếm 2/3 trên, bấm tiếp hiện đáp số, rồi lời giải).

**Ngân hàng chưa đủ câu?** Khi tạo phiếu bị thiếu câu (hoặc dạng chưa có câu nào), hộp kết quả có nút
**Prompt AI bổ sung câu thiếu…**: ứng dụng soạn sẵn prompt đúng số câu còn thiếu theo từng dạng × loại × mức
(phiếu tự luận: câu TL có lời giải chi tiết). Chép prompt → dán vào ChatGPT/Gemini/Claude (kèm SGK nếu có) → lưu kết quả thành file
→ bấm **Nhập câu AI trả về…** (chính là chức năng Nhập câu hỏi) → tạo lại phiếu.

Không có hai câu trùng đề (khác mã nhưng cùng nội dung) trong cùng một phiếu.
Câu được lấy xoay vòng qua các dạng, ưu tiên câu chưa dùng; thiếu câu sẽ được báo.
Dòng lệnh: `python3 scripts/phieu_bai_hoc.py cau_hinh.json --bien-dich`.


## Toán 8, Toán 9 (Kết nối tri thức)

Danh mục theo mục lục SGK KNTT:
- Toán 8: 10 chương, 39 bài, 112 dạng — `du-lieu/toan8_kntt.json`
- Toán 9: 10 chương, 32 bài, 99 dạng — `du-lieu/toan9_kntt.json`
Nạp vào `id_map.json` bằng `python3 scripts/them_thcs.py` (sửa/thêm dạng trong file json rồi chạy lại; thêm lớp 6, 7 chỉ cần tạo `toan6_kntt.json`, `toan7_kntt.json` cùng cấu trúc).
Mã dạng: số lớp (`8`/`9`) + `D`/`H` + số chương SGK (chương X ghi `0`) + `?` + **số bài SGK** + `-` + dạng.
Ví dụ `8D2?9-1` = Toán 8 Bài 9 Phân tích đa thức thành nhân tử, dạng 1; `9D6?20-4` = Toán 9 Bài 20 Định lí Viète, dạng 4.

Ngân hàng ban đầu chưa có câu lớp 8, 9. Cách làm phiếu:
1. **Phiếu bài học** → Lớp **8** hoặc **9** → chương → tích bài → chọn kiểu phiếu (tự luận rất hợp với ôn thi vào 10).
2. Bấm **Kiểm tra kho / Prompt AI soạn câu…** → ứng dụng tính đúng số câu cần cho phiếu theo từng dạng × loại × mức
   → **Prompt AI bổ sung câu thiếu…** (prompt riêng cho THCS: bám SGK KNTT; lớp 9 theo đề vào 10 TP.HCM, lớp 8 theo đề kiểm tra; không dùng kiến thức lớp trên).
3. Dán prompt vào AI (kèm file SGK bài đó), lưu kết quả → **Nhập câu AI trả về…** → câu vào `cau-hoi/lop8/…`, `cau-hoi/lop9/…`.
4. Bấm **Tạo phiếu**. Câu đã nhập dùng lại được cho các phiếu, đề sau.
