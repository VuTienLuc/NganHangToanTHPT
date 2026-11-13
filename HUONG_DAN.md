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

## Biên dịch đề
Mở file trong `de-da-ra/<tên>/` bằng TeXstudio, biên dịch **pdfLaTeX** như các đề cũ của phần mềm
(cần gói `vietnam` — có sẵn trong MacTeX đầy đủ). Hoặc thêm `--bien-dich` khi trộn.
Chữ ở đầu/chân trang sửa trong `khung/DeThi/Khaibao/HeaderAndFooter.tex`.

## Tra cứu nhanh
`du-lieu/thong_ke_theo_dang.csv` (mở bằng Excel/Numbers): số câu theo dạng × loại × mức.
`du-lieu/nganhang.sqlite`: mở bằng "DB Browser for SQLite" để lọc câu.
