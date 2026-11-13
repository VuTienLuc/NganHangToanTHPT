# NHIỆM VỤ
Thầy là giáo viên Toán THPT. Đính kèm là một đề thi / đề kiểm tra / phiếu bài tập (PDF, ảnh hoặc Word).
Hãy **gõ lại TOÀN BỘ các câu hỏi** thành mã LaTeX theo đúng định dạng ngân hàng câu hỏi bên dưới, để nhập thẳng vào kho.
Không bỏ câu nào, không gộp câu, không thêm câu ngoài đề. Giữ nguyên số liệu, ký hiệu, cách hỏi của đề.

# ĐỊNH DẠNG BẮT BUỘC
Mỗi câu là MỘT khối riêng. Dòng mở khối có mã dạng ngay sau `\begin{..}`:
`\begin{ex}%[2D1N1-2]` — đọc là: lớp `2` (0 = lớp 10, 1 = lớp 11, 2 = lớp 12) · môn `D` · chương `1` · **mức** `N` · bài `1` - dạng `2`.
Mã lấy từ DANH MỤC DẠNG ở cuối: chép mã `2D1?1-2` rồi **thay dấu `?` bằng chữ mức**:
- `N` Nhận biết: nhớ/nhận ra định nghĩa, công thức, tính chất; làm 1 bước.
- `H` Thông hiểu: áp dụng trực tiếp quy tắc, tính toán 2–3 bước quen thuộc.
- `V` Vận dụng: phối hợp nhiều kiến thức, nhiều bước, bài toán thực tế quen thuộc.
- `C` Vận dụng cao: tình huống mới, tham số phức tạp, tối ưu, lập luận sâu.
Nếu không có dạng nào phù hợp, chọn dạng gần nhất cùng bài/chương; thật sự không có thì ghi `%[?]` (thầy sẽ phân loại sau).

## 1. Trắc nghiệm 4 phương án (Phần I) — `ex` + `\choice`, đúng MỘT `\True`
```latex
\begin{ex}%[2D1N1-1]
	Hàm số $y=x^3-3x$ nghịch biến trên khoảng nào?
	\choice
	{$(-\infty;-1)$}
	{\True $(-1;1)$}
	{$(1;+\infty)$}
	{$(-\infty;+\infty)$}
	\loigiai{
		$y'=3x^2-3<0\Leftrightarrow -1<x<1$.
	}
\end{ex}
```
- Phương án viết KHÔNG có chữ "A." "B."; thứ tự giữ như đề.
- Lời giải **không ghi "Chọn A/B/C/D"** hay "Đáp án B" (vì khi trộn đề các phương án bị đảo).

## 2. Đúng/Sai (Phần II) — `ex` + `\choiceTF`, ý đúng có `\True`, lời giải đủ 4 `\itemch`
```latex
\begin{ex}%[2D1H1-1]
	Cho hàm số $y=x^3-3x$. Các khẳng định sau đúng hay sai?
	\choiceTF
	{\True Hàm số có đạo hàm $y'=3x^2-3$}
	{Hàm số đồng biến trên $(-1;1)$}
	{\True Hàm số nghịch biến trên $(0;1)$}
	{Hàm số đồng biến trên $\mathbb{R}$}
	\loigiai{
		\begin{itemchoice}
			\itemch Đúng. $y'=3x^2-3$.
			\itemch Sai. Trên $(-1;1)$ ta có $y'<0$.
			\itemch Đúng. Vì $(0;1)\subset(-1;1)$.
			\itemch Sai. Hàm số nghịch biến trên $(-1;1)$.
		\end{itemchoice}
	}
\end{ex}
```
- Đúng 4 ý theo thứ tự a, b, c, d của đề; ý d thường là ý khó nhất — giữ ở cuối.
- Mỗi ý viết như một mệnh đề độc lập, **không nhắc "ý a", "câu b)"** trong ý khác hay trong lời giải.
- Lời giải: đúng 4 dòng `\itemch`, mở đầu bằng "Đúng." hoặc "Sai.". Mức của câu Đúng/Sai lấy theo ý khó nhất.

## 3. Trả lời ngắn (Phần III) — `bt` + `\shortans{đáp số}`
```latex
\begin{bt}%[2D1V1-3]
	Có bao nhiêu giá trị nguyên của $m\in[-10;10]$ để hàm số $y=x^3-3mx+1$ đồng biến trên $\mathbb{R}$?
	\shortans{11}
	\loigiai{
		$y'=3x^2-3m\ge 0\ \forall x\Leftrightarrow m\le 0$, có $11$ giá trị nguyên.
	}
\end{bt}
```
- Đáp số là một số, **dấu phẩy thập phân** (`2,5`), tối đa 4 ký tự kể cả dấu `-` và `,`; làm tròn đúng yêu cầu của đề.

## 4. Tự luận — `bt` KHÔNG có `\shortans`
```latex
\begin{bt}%[2D1H1-1]
	Xét tính đơn điệu của hàm số $y=x^4-2x^2$.
	\loigiai{ ... }
\end{bt}
```

# QUY TẮC GÕ
- Công thức trong `$...$`; dùng `\dfrac`, `\sqrt`, `\left(…\right)`, `\mathbb{R}`, hệ `\heva{&x=1\\&y=2}`, tuyển `\hoac{&x=1\\&x=2}`.
- **Vectơ** viết `\overrightarrow{AB}`, `\overrightarrow{F_1}` (không dùng `\vec`).
- **Số thập phân trong công thức** viết dấu phẩy trong ngoặc nhọn: `$15{,}25$`, `$0{,}33\%$`, `$\approx 4{,}11$`
  (viết `$15,25$` LaTeX sẽ in thành "15, 25"). Riêng `\shortans{4,1}` viết phẩy thường, không có `$`.
- Số lớn tách nhóm bằng `\,`: `$10\,000$`. Đơn vị: `$40\text{ km}$`, `$50\text{ N}$`, `$180{,}57\text{ cm}^2$`.
- **Xuống dòng trong đề và lời giải**: mỗi ý/bước tính cuối dòng thêm `\\` (LaTeX bỏ qua xuống dòng thường, các câu sẽ dính vào nhau).
  Công thức dài hoặc quan trọng đặt riêng một dòng: `\[ \overline{x}=\dfrac{1525}{100}=15{,}25. \]`
- Bảng số liệu: `\begin{center}\begin{tabular}{|l|c|c|…|}\hline … \\ \hline\end{tabular}\end{center}`;
  bảng nhiều hơn 8 cột bọc thêm `\resizebox{\linewidth}{!}{ … }` để in 2 cột không tràn.
- Bảng biến thiên / bảng xét dấu: dùng `tkz-tab` trong `\begin{tikzpicture}…\end{tikzpicture}`.
- Hình vẽ: vẽ lại bằng TikZ nếu làm được. Không chắc thì để
  `\begin{center}\textit{[Hình: mô tả ngắn]}\end{center} % CAN_VE_HINH` — thầy sẽ vẽ sau.
- Hình đặt cạnh đề bài: `\immini{nội dung câu hỏi}{\begin{tikzpicture}…\end{tikzpicture}}`.
- Đề có đáp án/lời giải: dùng của đề. Đề **không** có: tự giải cẩn thận, tính lại từng phép tính, viết lời giải ngắn gọn đúng chuẩn.
  Câu nào không chắc chắn, thêm chú thích cuối dòng mở khối: `%[2D1V3-6] % KIEM_TRA: lý do`.
- Lời giải không nhắc tới thứ tự phương án/ý ("Chọn B", "phương án A", "ý a)…") vì khi trộn đề thứ tự bị đảo.
- KHÔNG viết `\documentclass`, `\begin{document}`, lời dẫn hay giải thích ngoài các khối câu hỏi.
- Không đánh số "Câu 1." trong nội dung (số câu tự sinh khi in).

# CHỌN MÃ DẠNG CHO ĐÚNG (quan trọng nhất)
1. Xác định **việc câu hỏi yêu cầu làm** (tính trung bình, tìm trung vị, tính độ lớn hợp lực, đọc giá trị từ bảng…),
   không dựa vào chủ đề bề ngoài (câu "giá cước bưu điện" là *đọc giá trị hàm số cho bởi bảng*, không phải "tính đồng biến").
2. Tìm trong DANH MỤC dạng có **tên mô tả đúng việc đó**, đúng lớp – chương – bài. Đề tổng hợp (cuối kì) gồm nhiều chương: mỗi câu chọn chương riêng.
3. Câu toán thực tế: ưu tiên dạng có tên "Toán thực tế …" / "ứng dụng thực tế" của đúng bài nếu có.
4. Mức độ theo thang N/H/V/C ở trên, xét **độ khó thật** của câu (không mặc định theo phần I/II/III).
5. Không có dạng khớp: chọn dạng gần nhất cùng bài và thêm `% KIEM_TRA: dạng gần đúng`; không có cả bài phù hợp thì ghi `%[?]`.

# TỰ KIỂM TRA TRƯỚC KHI TRẢ KẾT QUẢ
- [ ] Đủ số câu như đề; mỗi câu đúng một khối `\begin{ex}…\end{ex}` hoặc `\begin{bt}…\end{bt}`, ngoặc `{}` đóng mở khớp.
- [ ] Trắc nghiệm: đúng 4 phương án, đúng **một** `\True`, đáp án `\True` khớp với lời giải.
- [ ] Đúng/Sai: đúng 4 ý trong `\choiceTF`; lời giải có `\begin{itemchoice}` với đúng 4 `\itemch` **cùng thứ tự**,
      mỗi `\itemch` bắt đầu bằng "Đúng." hoặc "Sai." **khớp** với `\True` của ý tương ứng.
- [ ] Trả lời ngắn: `\shortans{…}` là một số, tối đa 4 ký tự (kể cả `-` và `,`), đúng yêu cầu làm tròn, khớp kết quả cuối lời giải.
- [ ] Mọi mã `%[…]` có trong DANH MỤC (sau khi thay `?` bằng N/H/V/C).
- [ ] Số thập phân trong `$…$` đã viết `{,}`; các bước lời giải đã có `\\` cuối dòng hoặc `\[…\]`.

# KẾT QUẢ TRẢ VỀ
Một khối mã duy nhất ```latex … ``` chứa lần lượt mọi câu theo thứ tự trong đề (Phần I → II → III → Tự luận).
Ngay dòng đầu khối ghi chú thích nguồn: `% nguồn: <tên đề, trường, năm học nếu có>`.
Sau khối mã, liệt kê ngắn: số câu mỗi loại, các câu có `% KIEM_TRA` hoặc `% CAN_VE_HINH`.
Thầy sẽ lưu khối mã thành file `.tex` (hoặc `.txt`) rồi nhập vào ngân hàng.

# DANH MỤC DẠNG (182 dạng) — chỉ dùng các mã dưới đây

### Lớp 10 · Đại số – Giải tích · Xác suất  (mã chương 0D0)
- Bài 1. Không gian mẫu và biến cố
    - `0D0?1-1` Các câu hỏi lý thuyết tổng hợp
    - `0D0?1-2` Mô tả không gian mẫu, biến cố
    - `0D0?1-3` Đếm phần tử không gian mẫu, biến cố
- Bài 2. Xác suất của biến cố
    - `0D0?2-1` Các câu hỏi lý thuyết tổng hợp
    - `0D0?2-2` Liên quan xúc xắc, đồng tiền (PP liệt kê)
    - `0D0?2-3` Liên quan việc sắp xếp chỗ
    - `0D0?2-4` Liên quan việc chọn người
    - `0D0?2-5` Liên quan việc chọn đối tượng khác
    - `0D0?2-6` Liên quan hình học
    - `0D0?2-7` Liên quan việc đếm số
    - `0D0?2-8` Liên quan bàn tròn hoặc hóan vị lặp
    - `0D0?2-9` Liên quan vấn đề khác

### Lớp 10 · Đại số – Giải tích · Mệnh đề. Tập hợp  (mã chương 0D1)
- Bài 1. Mệnh đề
    - `0D1?1-1` Xác định mệnh đề, mệnh đề chứa biến
    - `0D1?1-2` Tính đúng-sai của mệnh đề
    - `0D1?1-3` Phủ định của một mệnh đề
    - `0D1?1-4` Mệnh đề kéo theo, mệnh đề đảo, mệnh đề tương đương
    - `0D1?1-5` Mệnh đề với mọi, tồn tại (và phủ định chúng)
    - `0D1?1-6` Áp dụng mệnh đề vào suy luận có lí
- Bài 2. Tập hợp
    - `0D1?2-1` Tập hợp và phần tử của tập hợp
    - `0D1?2-2` Tập hợp con. Hai tập hợp bằng nhau
    - `0D1?2-3` Ký hiệu khoảng, đoạn, nửa khoảng
- Bài 3. Các phép toán tập hợp
    - `0D1?3-1` Giao và hợp của hai tập hợp (rời rạc)
    - `0D1?3-2` Hiệu và phần bù của hai tập hợp (rời rạc)
    - `0D1?3-3` Giao và hợp (dùng đoạn, khoảng)
    - `0D1?3-4` Hiệu và phần bù (dùng đoạn, khoảng)
    - `0D1?3-5` Toán thực tế  ứng dụng của tập hợp

### Lớp 10 · Đại số – Giải tích · BPT và hệ BPT bậc nhất hai ẩn  (mã chương 0D2)
- Bài 1. Bất phương trình bậc nhất hai ẩn
    - `0D2?1-1` Các khái niệm về BPT bậc nhất hai ẩn
    - `0D2?1-2` Miền nghiệm của BPT bậc nhất hai ẩn
    - `0D2?1-3` Toán thực tế  về BPT bậc nhất hai ẩn
- Bài 2. Hệ bất phương trình bậc nhất hai ẩn
    - `0D2?2-1` Các khái niệm về Hệ BPT bậc nhất hai ẩn
    - `0D2?2-2` Miền nghiệm của Hệ BPT bậc nhất hai ẩn
    - `0D2?2-3` Toán thực tế  về Hệ BPT bậc nhất hai ẩn

### Lớp 10 · Đại số – Giải tích · Hàm số bậc hai và đồ thị  (mã chương 0D3)
- Bài 1. Hàm số và đồ thị
    - `0D3?1-1` Xác định một hàm số
    - `0D3?1-2` Tập xác định của hàm số
    - `0D3?1-3` Giá trị của hàm số
    - `0D3?1-4` Đồ thị của hàm số
    - `0D3?1-5` Tính đồng biến, nghịch biến
    - `0D3?1-6` Tính chẵn, lẻ
    - `0D3?1-7` Toán thực tế  về hàm số
- Bài 2. Hàm số bậc hai
    - `0D3?2-1` Xác định hàm số bậc hai
    - `0D3?2-2` Bảng biến thiên, tính đơn điệu, max, min
    - `0D3?2-3` Đồ thị của hàm số bậc hai
    - `0D3?2-4` Bài toán về sự tương giao
    - `0D3?2-5` Hàm số chứa dấu giá trị tuyệt đối
    - `0D3?2-6` Toán thực tế  ứng dụng hàm số bậc hai

### Lớp 10 · Đại số – Giải tích · Thống kê  (mã chương 0D6)
- Bài 1. Số gần đúng. Sai số
    - `0D6?1-1` Tính và ước lượng sai số tuyệt đối, tương đối
    - `0D6?1-2` Tính và xác định độ chính xác của kết quả
    - `0D6?1-3` Quy tròn số gần đúng
    - `0D6?1-4` Viết số gần đúng cho số đúng biết độ chính xác
- Bài 2. Mô tả và biểu diễn dữ liệu trên các bảng và biểu đồ
    - `0D6?2-1` Đọc và phân tích thông tin trên bảng số liệu
    - `0D6?2-2` Đọc và phân tích thông tin trên biểu đồ
    - `0D6?2-3` Số liệu bất thường trên bảng số liệu
    - `0D6?2-4` Số liệu bất thường trên biểu đồ
- Bài 3. Các số đặc trưng đo xu thế trung tâm của mẫu số liệu
    - `0D6?3-1` Câu hỏi lý thuyết
    - `0D6?3-2` Số trung bình cộng
    - `0D6?3-3` Số trung vị
    - `0D6?3-4` Tứ phân vị
    - `0D6?3-5` Mốt
- Bài 4. Các số đặc trưng đo mức độ phân tán của mẫu số liệu
    - `0D6?4-1` Câu hỏi lý thuyết
    - `0D6?4-2` Khoảng biến thiên, khoảng tứ phân vị
    - `0D6?4-3` Giá trị bất thường của mẫu số liệu
    - `0D6?4-4` Phương sai, độ lệch chuẩn của mẫu số liệu

### Lớp 10 · Đại số – Giải tích · Bất phương trình bậc 2 một ẩn  (mã chương 0D7)
- Bài 1. Dấu của tam thức bậc 2
    - `0D7?1-1` Xác định tam thức bậc 2
    - `0D7?1-2` Dấu của tam thức bậc 2 và ứng dụng
    - `0D7?1-3` Bài toán xét dấu biết BXD, đồ thị
    - `0D7?1-4` Xét dấu biểu thức dạng tích, thương
    - `0D7?1-5` Toán thực tế  ứng dụng dấu tam thức bậc 2
- Bài 2. Giải bất phương trình bậc 2 một ẩn
    - `0D7?2-1` Bất phương trình bậc 2 và ứng dụng
    - `0D7?2-2` Giải bất phương trình bậc hai biết BXD, đồ thị
    - `0D7?2-3` Bất phương trình dạng tích, thương
    - `0D7?2-4` Hệ bất phương trình BPT bậc 2
    - `0D7?2-5` Bất phương trình chứa căn, | · |
    - `0D7?2-6` Bài toán có tham số 𝑚
    - `0D7?2-7` Toán thực tế  ứng dụng bất phương trình bậc 2 một ẩn
- Bài 3. Phương trình quy về phương trình bậc hai
    - `0D7?3-1` Phương trình căn
    - `0D7?3-2` Phương trình căn
    - `0D7?3-3` Phương trình căn thức có tham số
    - `0D7?3-4` Phương trình căn thức (dạng khác)
    - `0D7?3-5` Phương trình khác quy về phương trình bậc 2
    - `0D7?3-6` Toán hình, toán thực tế  ứng dụng phương trình quy về bậc 2

### Lớp 10 · Đại số – Giải tích · Đại số tổ hợp  (mã chương 0D8)
- Bài 1. Quy tắc cộng-quy tắc nhân
    - `0D8?1-1` Bài toán chỉ sử dụng quy tắc cộng
    - `0D8?1-2` Bài toán chỉ sử dụng quy tắc nhân
    - `0D8?1-3` Bài toán kết hợp quy tắc cộng và quy tắc nhân
    - `0D8?1-4` Bài toán dùng quy tắc bù trừ
    - `0D8?1-5` Bài toán đếm số tự nhiên
    - `0D8?1-6` Sơ đồ hình cây
- Bài 2. Hoán vị. Chỉnh hợp. Tổ hợp
    - `0D8?2-1` Lý thuyết tổng hợp về 𝑃, 𝐶, 𝐴
    - `0D8?2-2` Bài toán có biểu thức 𝑃, 𝐶, 𝐴
    - `0D8?2-3` Bài toán đếm số tự nhiên
    - `0D8?2-4` Bài toán chọn người
    - `0D8?2-5` Bài toán chọn đối tượng khác
    - `0D8?2-6` Bài toán có yếu tố hình học
    - `0D8?2-7` Bài toán xếp chỗ (không tròn, không lặp)
    - `0D8?2-8` Hoán vị bàn tròn
    - `0D8?2-9` Hoán vị lặp
- Bài 3. Nhị thức Newton
    - `0D8?3-1` Các câu hỏi lý thuyết tổng hợp
    - `0D8?3-2` Khai triển một nhị thức Newton
    - `0D8?3-3` Tìm hệ  số, số hạng trong khai triển bằng tam giác Pascal
    - `0D8?3-4` Tìm hệ  số, số hạng trong khai triển
    - `0D8?3-5` Tính tổng nhờ khai triển nhị thức Newton
    - `0D8?3-6` Toán tổ hợp có dùng nhị thức Newton

### Lớp 10 · Hình học · Hệ thức lượng trong tam giác  (mã chương 0H4)
- Bài 1. Giá trị lượng giác của góc (0 −180∘)
    - `0H4?1-1` Xét dấu của biểu thức lượng giác
    - `0H4?1-2` Tính các giá trị lượng giác
    - `0H4?1-3` Biến đổi, rút gọn biểu thức lượng giác
- Bài 2. Định lý sin và định lý côsin
    - `0H4?2-1` Bài toán chỉ dùng định lý Sin, Côsin
    - `0H4?2-2` Bài toán có dùng công thức diện tích
    - `0H4?2-3` Biến đổi, rút gọn biểu thức
    - `0H4?2-4` Nhận dạng tam giác
- Bài 3. Giải tam giác và ứng dụng thực tế 
    - `0H4?3-1` Giải tam giác
    - `0H4?3-2` Các ứng dụng thực tế

### Lớp 10 · Hình học · Véctơ (chưa xét tọa độ)  (mã chương 0H5)
- Bài 1. Khái niệm véctơ
    - `0H5?1-1` Xác định một véctơ
    - `0H5?1-2` Xét phương và hướng của các véctơ
    - `0H5?1-3` Hai véctơ bằng nhau
    - `0H5?1-4` Hai véctơ đối nhau
    - `0H5?1-5` Độ dài của một véctơ
    - `0H5?1-6` Toán thực tế  áp dụng véctơ
- Bài 2. Tổng và hiệu của hai véctơ
    - `0H5?2-1` Tính toán, thu gọn hiệu các véctơ
    - `0H5?2-2` Tính đúng-sai của 1 đẳng thức véctơ
    - `0H5?2-3` Tìm điểm nhờ đẳng thức véctơ
    - `0H5?2-4` Tính độ dài của véctơ tổng, hiệu
    - `0H5?2-5` Cực trị hình học
    - `0H5?2-6` Toán thực tế  áp dụng tổng hiệu véctơ
- Bài 3. Tích của một số với véctơ
    - `0H5?3-1` Xác định 𝑘. và độ dài của nó
    - `0H5?3-2` Biến đổi, thu gọn 1 đẳng thức véctơ
    - `0H5?3-3` Tìm điểm nhờ đẳng thức véctơ
    - `0H5?3-4` Sự cùng phương của 2 véctơ và ứng dụng
    - `0H5?3-5` Phân tích 1 véctơ theo 2 véctơ không cùng phương
    - `0H5?3-6` Tính độ dài của véctơ tổng, hiệu
    - `0H5?3-7` Tập hợp điểm
    - `0H5?3-8` Cực trị hình học
    - `0H5?3-9` Toán thực tế  áp dụng tích 1 số với véctơ
- Bài 4. Tích vô hướng (chưa xét tọa độ)
    - `0H5?4-1` Tích vô hướng, góc giữa 2 véctơ
    - `0H5?4-2` Tìm góc nhờ tích vô hướng
    - `0H5?4-3` Đẳng thức về tích vô hướng hoặc độ dài
    - `0H5?4-4` Điều kiện vuông góc
    - `0H5?4-5` Các bài toán tìm điểm và tập hợp điểm
    - `0H5?4-6` Cực trị và chứng minh bất đẳng thức
    - `0H5?4-7` Toán thực tế  áp dụng tích vô hướng

### Lớp 10 · Hình học · Phương pháp tọa độ trong mặt phẳng (𝑂𝑥𝑦)  (mã chương 0H9)
- Bài 1. Tọa độ của véctơ
    - `0H9?1-1` Tọa độ điểm, độ dài đại số của véctơ trên 1 trục
    - `0H9?1-2` Phép toán véctơ (tổng, hiệu, tích với số ) trong Oxy
    - `0H9?1-3` Tọa độ điểm và véctơ trên hệ  trục Oxy
    - `0H9?1-4` Sự cùng phương của 2 véctơ và ứng dụng
    - `0H9?1-5` Phân tích một véctơ theo 2 véctơ không cùng phương
    - `0H9?1-6` Toán thực tế  dùng hệ  tọa độ
- Bài 2. Tích vô hướng (theo tọa độ)
    - `0H9?2-1` Tích vô hướng, góc giữa 2 véctơ
    - `0H9?2-2` Tìm góc nhờ tích vô hướng
    - `0H9?2-3` Đẳng thức về tích vô hướng hoặc độ dài
    - `0H9?2-4` Điều kiện vuông góc
    - `0H9?2-5` Các bài toán tìm điểm và tập hợp điểm
    - `0H9?2-6` Cực trị và chứng minh bất đẳng thức
    - `0H9?2-7` Toán thực tế, liên môn
- Bài 3. Đường thẳng trong mặt phẳng tọa độ
    - `0H9?3-1` Điểm, véctơ, hệ  số góc của đường thẳng
    - `0H9?3-2` Phương trình đường thẳng
    - `0H9?3-3` Vị trí tương đối giữa hai đường thẳng
    - `0H9?3-4` Bài toán về góc giữa hai đường thẳng
    - `0H9?3-5` Bài toán về khoảng cách
    - `0H9?3-6` Bài toán tìm điểm
    - `0H9?3-7` Bài toán dùng cho tam giác, tứ giác
    - `0H9?3-8` Bài toán thực tế, PP tọa độ hóa
    - `0H9?3-9` Bài toán có dùng PT chính tắc
- Bài 4. Đường tròn trong mặt phẳng tọa độ
    - `0H9?4-1` Tìm tâm, bán kính và điều kiện là đường tròn
    - `0H9?4-2` Phương trình đường tròn
    - `0H9?4-3` Phương trình tiếp tuyến của đường tròn
    - `0H9?4-4` Vị trí tương đối liên quan đường tròn
    - `0H9?4-5` Toán tổng hợp đường thẳng và đường tròn
    - `0H9?4-6` Bài toán dùng cho tam giác, tứ giác
    - `0H9?4-7` Bài toán thực tế, PP tọa độ hóa
- Bài 5. Ba đường conic trong mặt phẳng tọa độ
    - `0H9?5-0` Bài toán tổng hợp/thực tế, PP tọa độ hóa 3 đường conic
    - `0H9?5-1` Xác định các yếu tố của elip
    - `0H9?5-2` Phương trình chính tắc của elip
    - `0H9?5-3` Bài toán điểm trên elip
    - `0H9?5-4` Xác định các yếu tố của hypebol
    - `0H9?5-5` Phương trình chính tắc của hypebol
    - `0H9?5-6` Bài toán điểm trên hypebol
    - `0H9?5-7` Xác định các yếu tố của parabol
    - `0H9?5-8` Phương trình chính tắc của parabol
    - `0H9?5-9` Bài toán điểm trên parabol

### Lớp 10 · Chuyên đề / Xác suất · Phương pháp tọa độ trong mặt phẳng (𝑂𝑥𝑦)  (mã chương 0C1)
- Bài 1. Hệ phương trình bậc nhất 3 ẩn và ứng dụng
    - `0C1?1-1` Các khái niệm về Hệ PT bậc nhất 3 ẩn
    - `0C1?1-2` Giải Hệ PT bậc nhất 3 ẩn
    - `0C1?1-3` Toán thực tế ứng dụng Hệ PT bậc nhất 3 ẩn

### Lớp 10 · Chuyên đề / Xác suất · Phương pháp quy nạp toán học  (mã chương 0C2)
- Bài 1. Phương pháp quy nạp toán học
    - `0C2?1-1` Quy nạp chứng minh các đẳng thức/công thức/chia hết
    - `0C2?1-2` Quy nạp chứng minh các bất đẳng thức
