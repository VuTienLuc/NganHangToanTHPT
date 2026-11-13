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
- Công thức trong `$...$`; dùng `\dfrac`, `\sqrt`, `\left(…\right)`, `\mathbb{R}`, `\overrightarrow{AB}`, hệ `\heva{&x=1\\&y=2}`, tuyển `\hoac{&x=1\\&x=2}`.
- Bảng biến thiên / bảng xét dấu: dùng `tkz-tab` trong `\begin{tikzpicture}…\end{tikzpicture}`.
- Hình vẽ: vẽ lại bằng TikZ nếu làm được. Không chắc thì để
  `\begin{center}\textit{[Hình: mô tả ngắn]}\end{center} % CAN_VE_HINH` — thầy sẽ vẽ sau.
- Hình đặt cạnh đề bài: `\immini{nội dung câu hỏi}{\begin{tikzpicture}…\end{tikzpicture}}`.
- Đề có đáp án/lời giải: dùng của đề. Đề **không** có: tự giải cẩn thận, kiểm tra lại tính toán, viết lời giải ngắn gọn đúng chuẩn.
  Câu nào không chắc chắn, thêm chú thích cuối dòng mở khối: `%[2D1V3-6] % KIEM_TRA: lý do`.
- KHÔNG viết `\documentclass`, `\begin{document}`, lời dẫn hay giải thích ngoài các khối câu hỏi.
- Không đánh số "Câu 1." trong nội dung (số câu tự sinh khi in).

# KẾT QUẢ TRẢ VỀ
Một khối mã duy nhất ```latex … ``` chứa lần lượt mọi câu theo thứ tự trong đề (Phần I → II → III → Tự luận).
Ngay dòng đầu khối ghi chú thích nguồn: `% nguồn: <tên đề, trường, năm học nếu có>`.
Sau khối mã, liệt kê ngắn: số câu mỗi loại, các câu có `% KIEM_TRA` hoặc `% CAN_VE_HINH`.
Thầy sẽ lưu khối mã thành file `.tex` rồi nhập vào ngân hàng.

# DANH MỤC DẠNG (91 dạng) — chỉ dùng các mã dưới đây

### Lớp 12 · Đại số – Giải tích · Ứng dụng đạo hàm để khảo sát hàm số  (mã chương 2D1)
- Bài 1. Sự đồng biến và nghịch biến của hàm số
    - `2D1?1-1` Xét tính đơn điệu của hàm số cho bởi công thức
    - `2D1?1-2` Xét tính đơn điệu dựa vào bảng biến thiên, đồ thị
    - `2D1?1-3` Tìm tham số 𝑚 để hàm số đơn điệu
    - `2D1?1-4` Ứng dụng tính đơn điệu để chứng minh bất đẳng thức, giải phương trình,
    - `2D1?1-5` Toán thực tế ứng dụng sự đồng biến nghịch biến
- Bài 2. Cực trị của hàm số
    - `2D1?2-1` Tìm cực trị của hàm số cho bởi công thức
    - `2D1?2-2` Tìm cực trị dựa vào BBT, đồ thị
    - `2D1?2-3` Tìm 𝑚 để hàm số đạt cực trị tại 1 điểm 𝑥0 cho trước
    - `2D1?2-4` Tìm 𝑚 để hàm số, đồ thị hàm số bậc ba có cực trị thỏa mãn điều kiện
    - `2D1?2-5` Tìm 𝑚 để hàm số, đồ thị hàm số trùng phương có cực trị thỏa mãn điều
    - `2D1?2-6` Tìm 𝑚 để hàm số, đồ thị hàm số các hàm số khác có cực trị thỏa mãn điều
    - `2D1?2-7` Toán thực tế ứng dụng cực trị của hàm số
- Bài 3. Giá trị lớn nhất và giá trị nhỏ nhất của hàm số
    - `2D1?3-1` GTLN, GTNN trên đoạn [𝑎; 𝑏]
    - `2D1?3-2` GTLN, GTNN trên khoảng
    - `2D1?3-3` Sử dụng các đánh giá, bất đẳng thức cổ điển
    - `2D1?3-4` Ứng dụng GTNN, GTLN trong bài toán phương trình, bất phương trình
    - `2D1?3-5` GTLN, GTNN hàm nhiều biến
    - `2D1?3-6` Toán thực tế ứng dụng GTLN, GTNN của hàm số
- Bài 4. Đường tiệm cận
    - `2D1?4-1` Bài toán xác định các đường tiệm cận của hàm số (không chứa tham số )
    - `2D1?4-2` Bài toán xác định các đường tiệm cận của hàm số có chứa tham số
    - `2D1?4-3` Bài toán liên quan đến đồ thị hàm số và các đường tiệm cận
    - `2D1?4-4` Toán thực tế ứng dụng tiệm cận
- Bài 5. Khảo sát sự biến thiên và vẽ đồ thị hàm số
    - `2D1?5-1` Nhận dạng đồ thị
    - `2D1?5-2` Các phép biến đổi đồ thị
    - `2D1?5-3` Biện luận số giao điểm dựa vào đồ thị, bảng biến thiên
    - `2D1?5-4` Sự tương giao của hai đồ thị (liên quan đến tọa độ giao điểm)
    - `2D1?5-5` Đồ thị của hàm đạo hàm
    - `2D1?5-6` Phương trình tiếp tuyến của đồ thị hàm số
    - `2D1?5-7` Điểm đặc biệt của đồ thị hàm số
    - `2D1?5-8` Toán thực tế ứng dụng khảo sát hàm số

### Lớp 12 · Đại số – Giải tích · Các số đặc trưng ... ghép nhóm  (mã chương 2D3)
- Bài 1. Khoảng biến thiên, khoảng tứ phân vị của mẫu số liệu ghép nhóm
    - `2D3?1-1` Công thức lý thuyết
    - `2D3?1-2` Tìm khoảng biến thiên
    - `2D3?1-3` Tìm khoảng tứ phân vị
    - `2D3?1-4` Câu hỏi tổng hợp
- Bài 2. Phương sai, độ lệch chuẩn của mẫu số liệu ghép nhóm
    - `2D3?2-1` Công thức lý thuyết
    - `2D3?2-2` Tìm phương sai, độ lệch chuẩn
    - `2D3?2-3` Câu hỏi tổng hợp

### Lớp 12 · Đại số – Giải tích · Các số đặc trưng ... ghép nhóm  (mã chương 2D4)
- Bài 1. Nguyên hàm
    - `2D4?1-1` Công thức lý thuyết
    - `2D4?1-2` Nguyên hàm cơ bản đa thức, phân thức
    - `2D4?1-3` Nguyên hàm cơ bản hàm lượng giác
    - `2D4?1-4` Nguyên hàm cơ bản hàm mũ, luỹ thừa
    - `2D4?1-5` Phương pháp đổi biến số cơ bản
    - `2D4?1-6` Toán thực tế áp dụng nguyên hàm
- Bài 2. Tích phân
    - `2D4?2-1` Công thức lý thuyết
    - `2D4?2-2` Tích phân cơ bản đa thức, phân thức
    - `2D4?2-3` Tích phân cơ bản hàm lượng giác
    - `2D4?2-4` Tích phân cơ bản hàm mũ, luỹ thừa
    - `2D4?2-5` Phương pháp đổi biến số cơ bản
    - `2D4?2-6` Toán thực tế áp dụng nguyên hàm
- Bài 3. Ứng dụng thực tế và hình học của tích phân
    - `2D4?3-1` Diện tích hình phẳng được giới hạn bởi các đồ thị
    - `2D4?3-2` Bài toán thực tế sử dụng diện tích hình phẳng
    - `2D4?3-3` Thể tích giới hạn bởi các đồ thị (tròn xoay)
    - `2D4?3-4` Thể tích tính theo mặt cắt 𝑆(𝑥)
    - `2D4?3-5` Bài toán thực tế và ứng dụng thể tích tròn xoay, 𝑆(𝑥)

### Lớp 12 · Đại số – Giải tích · Các số đặc trưng ... ghép nhóm  (mã chương 2D6)
- Bài 1. Xác suất có điều kiện
    - `2D6?1-1` Công thức lý thuyết
    - `2D6?1-2` Tính xác suất có điều kiện bằng công thức
    - `2D6?1-3` Tính xác suất có điều kiện bằng sơ đồ cây
    - `2D6?1-4` Bài toán tổng hợp
- Bài 2. Công thức xác suất toàn phần. Công thức Bayes
    - `2D6?2-1` Công thức lý thuyết
    - `2D6?2-2` Tính xác suất bằng công thức xác suất toàn phần
    - `2D6?2-3` Tính xác suất bằng công thức xác suất Bayes
    - `2D6?2-4` Bài toán tổng hợp

### Lớp 12 · Hình học · Tọa độ của véc-tơ trong không gian  (mã chương 2H2)
- Bài 1. Véc-tơ và các phép toán véc-tơ trong không gian (chưa tọa độ hóa)
    - `2H2?1-1` Công thức lý thuyết
    - `2H2?1-2` Tổng, hiệu, tích một số với véc-tơ
    - `2H2?1-3` Tích vô hướng và ứng dụng
    - `2H2?1-4` Toán thực tế áp dụng các phép toán véc-tơ
- Bài 2. Tọa độ của véc-tơ và các công thức
    - `2H2?2-1` Công thức lý thuyết
    - `2H2?2-2` Tìm tọa độ điểm
    - `2H2?2-3` Tìm tọa độ véc-tơ
    - `2H2?2-4` Công thức tọa độ của tích vô hướng và ứng dụng
    - `2H2?2-5` Công thức tọa độ của tích có hướng và ứng dụng
    - `2H2?2-6` Toán thực tế áp dụng các phép toán tọa độ hóa véc-tơ

### Lớp 12 · Hình học · Phương trình mặt phẳng, đường thẳng, mặt cầu  (mã chương 2H5)
- Bài 1. Phương trình mặt phẳng
    - `2H5?1-1` Câu hỏi lý thuyết
    - `2H5?1-2` Xác định véc-tơ pháp tuyến, cặp véc-tơ chỉ phương
    - `2H5?1-3` Viết phương trình tổng quát mặt phẳng
    - `2H5?1-4` Vị trí tương đối giữa hai mặt phẳng (song song, vuông góc)
    - `2H5?1-5` Khoảng cách điểm tới mặt phẳng
    - `2H5?1-6` Góc giữa hai mặt phẳng
    - `2H5?1-7` Toán thực tế áp dụng phương trình mặt phẳng
- Bài 2. Phương trình đường thẳng trong không gian
    - `2H5?2-1` Câu hỏi lý thuyết
    - `2H5?2-2` Xác định cặp véc-tơ chỉ phương, véc-tơ pháp tuyến
    - `2H5?2-3` Viết phương trình tổng quát, chính tắc, tham số đường thẳng
    - `2H5?2-4` Vị trí tương đối giữa hai đường thẳng
    - `2H5?2-5` Vị trí tương đối giữa đường thẳng và mặt phẳng
    - `2H5?2-6` Khoảng cách điểm tới đường thẳng
    - `2H5?2-7` Góc giữa hai đường thẳng, đường thẳng và mặt phẳng
    - `2H5?2-8` Toán thực tế áp dụng phương trình đường thẳng
- Bài 3. Phương trình mặt cầu trong không gian
    - `2H5?3-1` Câu hỏi lý thuyết
    - `2H5?3-2` Xác định tâm, bán kính, đường kính mặt cầu
    - `2H5?3-3` Viết phương trình tổng quát mặt cầu
    - `2H5?3-4` Toán thực tế áp dụng phương trình mặt cầu
