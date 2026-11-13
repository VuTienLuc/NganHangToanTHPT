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

# DANH MỤC DẠNG (257 dạng) — chỉ dùng các mã dưới đây

### Lớp 11 · Đại số – Giải tích · Hàm số lượng giác và phương trình lượng giác  (mã chương 1D1)
- Bài 1. Góc lượng giác
    - `1D1?1-1` Câu hỏi lý thuyết
    - `1D1?1-2` Chuyển đổi đơn vị độ và radian
    - `1D1?1-3` Số đo của một góc lượng giác
    - `1D1?1-4` Độ dài của một cung tròn
    - `1D1?1-5` Đường tròn lượng giác và ứng dụng
    - `1D1?1-6` Toán thực tế áp dụng góc lượng giác
- Bài 2. Giá trị lượng giác của một góc lượng giác
    - `1D1?2-1` Câu hỏi lý thuyết
    - `1D1?2-2` Xét dấu giá trị lượng giác. Tính giá trị lượng giác của một góc
    - `1D1?2-3` Biến đổi, rút gọn biểu thức lượng giác; chứng minh đẳng thức lượng giác
    - `1D1?2-4` Các góc lượng giác có liên quan đặc biệt: bù nhau, phụ nhau, đối nhau,
    - `1D1?2-5` Toán thực tế áp dụng giá trị của một góc lượng giác
- Bài 3. Các công thức lượng giác
    - `1D1?3-1` Câu hỏi lý thuyết
    - `1D1?3-2` Áp dụng công thức cộng
    - `1D1?3-3` Áp dụng công thức nhân đôi - hạ bậc
    - `1D1?3-4` Áp dụng công thức biến đổi tích <-> tổng
    - `1D1?3-5` Kết hợp nhiều công thức lượng giác
    - `1D1?3-6` Nhận dạng tam giác
    - `1D1?3-7` Toán thực tế áp dụng công thức lượng giác
- Bài 4. Hàm số lượng giác và đồ thị
    - `1D1?4-1` Câu hỏi lý thuyết
    - `1D1?4-2` Tìm tập xác định
    - `1D1?4-3` Xét tính đơn điệu
    - `1D1?4-4` Xét tính chẵn, lẻ
    - `1D1?4-5` Xét tính tuần hoàn, tìm chu kỳ
    - `1D1?4-6` Tìm tập giá trị và min, max
    - `1D1?4-7` Bảng biến thiên và đồ thị
    - `1D1?4-8` Toán thực tế áp dụng hàm số lượng giác
- Bài 5. Phương trình lượng giác cơ bản
    - `1D1?5-1` Câu hỏi lý thuyết. Khái niệm phương trình tương đương
    - `1D1?5-2` Điều kiện có nghiệm
    - `1D1?5-3` Phương trình cơ bản dùng Radian
    - `1D1?5-4` Phương trình cơ bản dùng Độ
    - `1D1?5-5` Phương trình đưa về dạng cơ bản
    - `1D1?5-6` Toán thực tế áp dụng phương trình lượng giác
- Bài 6. [Giảm] Phương trình lượng giác thường gặp
    - `1D1?6-1` Phương trình bậc n theo một hàm số lượng giác
    - `1D1?6-2` Phương trình đẳng cấp bậc n đối với sinx và cosx
    - `1D1?6-3` Phương trình bậc nhất đối với sinx và cosx
    - `1D1?6-4` Phương trình đối xứng, phản đối xứng
    - `1D1?6-5` Phương trình lượng giác không mẫu mực
    - `1D1?6-6` Phương trình lượng giác có chứa ẩn ở mẫu số
    - `1D1?6-7` Phương trình lượng giác có chứa tham số
    - `1D1?6-8` Toán thực tế áp dụng phương trình lượng giác thường gặp

### Lớp 11 · Đại số – Giải tích · Dãy số. Cấp số cộng. Cấp số nhân  (mã chương 1D2)
- Bài 1. Dãy số
    - `1D2?1-1` Câu hỏi lý thuyết
    - `1D2?1-2` Số hạng tổng quát, biểu diễn dãy số
    - `1D2?1-3` Tìm số hạng cụ thể của dãy số
    - `1D2?1-4` Dãy số tăng, dãy số giảm
    - `1D2?1-5` Dãy số bị chặn
    - `1D2?1-6` Toán thực tế áp dụng dãy số
- Bài 2. Cấp số cộng
    - `1D2?2-1` Câu hỏi lý thuyết
    - `1D2?2-2` Nhận diện cấp số cộng, công sai 𝑑
    - `1D2?2-3` Số hạng tổng quát của cấp số cộng
    - `1D2?2-4` Tìm số hạng cụ thể trong cấp số cộng
    - `1D2?2-5` Điều kiện để dãy số là cấp số cộng
    - `1D2?2-6` Tính tổng của cấp số cộng
    - `1D2?2-7` Toán thực tế áp dụng cấp số cộng
- Bài 3. Cấp số nhân
    - `1D2?3-1` Câu hỏi lý thuyết
    - `1D2?3-2` Nhận diện cấp số nhân, công bội 𝑞
    - `1D2?3-3` Số hạng tổng quát của cấp số nhân
    - `1D2?3-4` Tìm số hạng cụ thể trong cấp số nhân
    - `1D2?3-5` Điều kiện để dãy số là cấp số nhân
    - `1D2?3-6` Tính tổng của cấp số nhân
    - `1D2?3-7` Kết hợp cấp số nhân và cấp số cộng
    - `1D2?3-8` Toán thực tế áp dụng cấp số nhân

### Lớp 11 · Đại số – Giải tích · Giới hạn. Hàm số liên tục  (mã chương 1D3)
- Bài 1. Giới hạn của dãy số
    - `1D3?1-1` Câu hỏi lý thuyết
    - `1D3?1-2` Phương pháp đặt thừa số chung (lim hữu hạn)
    - `1D3?1-3` Phương pháp lượng liên hợp (lim hữu hạn)
    - `1D3?1-4` Giới hạn vô cực
    - `1D3?1-5` Cấp số nhân lùi vô hạn
    - `1D3?1-6` Toán thực tế áp dụng giới hạn của dãy số
- Bài 2. Giới hạn của hàm số
    - `1D3?2-1` Câu hỏi lý thuyết
    - `1D3?2-2` Thay số trực tiếp
    - `1D3?2-3` PP đặt thừa số chung, kết quả hữu hạn
    - `1D3?2-4` PP đặt thừa số chung, kết quả vô cực
    - `1D3?2-5` PP lượng liên hợp, kết quả hữu hạn
    - `1D3?2-6` PP lượng liên hợp, kết quả vô cực
    - `1D3?2-7` Giới hạn một bên
    - `1D3?2-8` Toán thực tế áp dụng giới hạn của hàm số
- Bài 3. Hàm số liên tục
    - `1D3?3-1` Câu hỏi lý thuyết
    - `1D3?3-2` Tính liên tục thể hiện qua đồ thị
    - `1D3?3-3` Hàm số liên tục tại một điểm
    - `1D3?3-4` Hàm số liên tục trên khoảng, đoạn
    - `1D3?3-5` Bài toán phương trình có nghiệm
    - `1D3?3-6` Toán thực tế áp dụng hàm số liên tục

### Lớp 11 · Đại số – Giải tích · Các số đặc trưng đo xu thế trung tâm cho mẫu số liệu  (mã chương 1D5)
- Bài 1. Số trung bình và mốt của mẫu số liệu ghép nhóm
    - `1D5?1-1` Câu hỏi lý thuyết
    - `1D5?1-2` Mẫu số liệu ghép nhóm
    - `1D5?1-3` Số trung bình
    - `1D5?1-4` Mốt
- Bài 2. Trung vị và tứ phân vị của mẫu số liệu ghép nhóm
    - `1D5?2-1` Câu hỏi lý thuyết
    - `1D5?2-2` Trung vị
    - `1D5?2-3` Tứ phân vị

### Lớp 11 · Đại số – Giải tích · Hàm số mũ và hàm số lôgarít  (mã chương 1D6)
- Bài 1. Phép tính luỹ thừa
    - `1D6?1-1` Tính giá trị của biểu thức chứa lũy thừa
    - `1D6?1-2` Biến đổi, rút gọn biểu thức chứa lũy thừa
    - `1D6?1-3` Điều kiện cho luỹ thừa, căn thức
    - `1D6?1-4` So sánh các lũy thừa
- Bài 2. Phép tính lôgarít
    - `1D6?2-1` Tính giá trị biểu thức chứa lôgarít
    - `1D6?2-2` Biến đổi, biểu diễn biểu thức chứa lôgarít
    - `1D6?2-3` Rút gọn, chứng minh biểu thức lôgarít
    - `1D6?2-4` Số e và bài toán lãi kép
    - `1D6?2-5` Toán thực tế áp dụng phép tính lôgarít
- Bài 3. Hàm số mũ. Hàm số lôgarít
    - `1D6?3-1` Câu hỏi lý thuyết hàm số lũy thừa, mũ, lôgarít
    - `1D6?3-2` Tập xác định của hàm số
    - `1D6?3-3` Sự biến thiên và đồ thị của hàm số mũ, lôgarít
    - `1D6?3-4` So sánh các luỹ thừa và lôgarít
    - `1D6?3-5` Toán thực tế áp dụng hàm số mũ, lôgarít
- Bài 4. Phương trình, bất phương trình mũ và lôgarít
    - `1D6?4-1` Điều kiện có nghiệm
    - `1D6?4-2` Phương trình mũ, lôgarít cơ bản
    - `1D6?4-3` Bất phương trình mũ, lôgarít cơ bản
    - `1D6?4-4` Phương trình mũ, lôgarít đưa về cùng cơ số
    - `1D6?4-5` Bất phương trình mũ, lôgarít đưa về cùng cơ số
    - `1D6?4-6` Toán thực tế áp dụng phương trình mũ, lôgarít
- Bài 5. [Giảm] Các phương pháp giải được giảm tải
    - `1D6?5-1` Phương pháp đặt ẩn phụ cho PT mũ, lôgarít
    - `1D6?5-2` Phương pháp lôgarít hóa, mũ cho PT mũ, lôgarít
    - `1D6?5-3` Phương pháp hàm số, đánh giá cho PT mũ, lôgarít
    - `1D6?5-4` Hệ PT mũ, lôgarít
    - `1D6?5-5` Toán thực tế áp dụng phương trình mũ, lôgarít

### Lớp 11 · Đại số – Giải tích · Đạo hàm  (mã chương 1D7)
- Bài 1. Đạo hàm
    - `1D7?1-1` Tính đạo hàm bằng định nghĩa
    - `1D7?1-2` Số gia hàm số, số gia biến số
    - `1D7?1-3` Ý nghĩa Hình học của đạo hàm
    - `1D7?1-4` Ý nghĩa Vật lý của đạo hàm
    - `1D7?1-5` Toán thực tế khác áp dụng định nghĩa đạo hàm
- Bài 2. Các quy tắc đạo hàm
    - `1D7?2-1` Tính đạo hàm
    - `1D7?2-2` Đẳng thức có 𝑦và 𝑦′
    - `1D7?2-3` Tiếp tuyến tại một điểm
    - `1D7?2-4` Tiếp tuyến biết trước hệ  số góc
    - `1D7?2-5` Tiếp tuyến chưa biết tiếp điểm và hệ  số góc
    - `1D7?2-6` Giới hạn hàm số lượng giác, hàm số mũ, lôgarít
    - `1D7?2-7` Dùng đạo hàm cho nhị thức Newton
    - `1D7?2-8` Toán thực tế áp dụng quy tắc đạo hàm
- Bài 3. Đạo hàm cấp hai
    - `1D7?3-1` Tính đạo hàm cấp hai
    - `1D7?3-2` Đẳng thức có 𝑦và (𝑦′, 𝑦′′)
    - `1D7?3-3` Toán thực tế và Ý nghĩa Vật lý của đạo hàm cấp hai

### Lớp 11 · Đại số – Giải tích · Xác suất  (mã chương 1D9)
- Bài 1. Biến cố giao và quy tắc nhân xác suất
    - `1D9?1-1` Câu hỏi lý thuyết
    - `1D9?1-2` Xác định và đếm số phần tử biến cố giao
    - `1D9?1-3` Công thức nhân xác suất cho 2 biến cố độc lập
    - `1D9?1-4` Tính xác suất biến cố giao bằng sơ đồ hình cây
- Bài 2. Biến cố hợp và quy tắc cộng xác suất
    - `1D9?2-1` Câu hỏi lý thuyết
    - `1D9?2-2` Xác định và đếm số phần tử biến cố hợp
    - `1D9?2-3` Quy tắc cộng cho hai biến cố xung khắc
    - `1D9?2-4` Quy tắc cộng cho hai biến cố bất kì
    - `1D9?2-5` Tính xác suất biến cố hợp bằng sơ đồ hình cây

### Lớp 11 · Hình học · Đường thẳng, mặt phẳng. Quan hệ song song trong  (mã chương 1H4)
- Bài 1. Điểm, đường thẳng và mặt phẳng
    - `1H4?1-1` Câu hỏi lý thuyết
    - `1H4?1-2` Hình biểu diễn của một hình không gian
    - `1H4?1-3` Tìm giao tuyến của hai mặt phẳng
    - `1H4?1-4` Tìm giao điểm của đường thẳng và mặt phẳng
    - `1H4?1-5` Xác định thiết diện
    - `1H4?1-6` Ba điểm thẳng hàng, ba đường thẳng đồng quy
    - `1H4?1-7` Toán thực tế áp dụng điểm, đường thẳng và mặt phẳng
- Bài 2. Hai đường thẳng song song
    - `1H4?2-1` Câu hỏi lý thuyết
    - `1H4?2-2` Hai đường thẳng song song
    - `1H4?2-3` Tìm giao tuyến bằng cách kẻ song song
    - `1H4?2-4` Tìm giao điểm của đường thẳng và mặt phẳng
    - `1H4?2-5` Xác định thiết diện bằng cách kẻ song song
    - `1H4?2-6` Ba điểm thẳng hàng
    - `1H4?2-7` Bài toán quỹ tích và điểm cố định
    - `1H4?2-8` Toán thực tế áp dụng hai đường thẳng song song
- Bài 3. Đường thẳng và mặt phẳng song song
    - `1H4?3-1` Câu hỏi lý thuyết
    - `1H4?3-2` Đường thẳng song song với mặt phẳng
    - `1H4?3-3` Tìm giao tuyến bằng cách kẻ song song
    - `1H4?3-4` Tìm giao điểm của đường thẳng và mặt phẳng
    - `1H4?3-5` Xác định thiết diện bằng cách kẻ song song
    - `1H4?3-6` Ba điểm thẳng hàng
    - `1H4?3-7` Bài toán quỹ tích và điểm cố định
    - `1H4?3-8` Toán thực tế áp dụng đường thẳng song song mặt phẳng
- Bài 4. Hai mặt phẳng song song
    - `1H4?4-1` Câu hỏi lý thuyết
    - `1H4?4-2` Hai mặt phẳng song song
    - `1H4?4-3` Chứng minh đường thẳng song song mặt phẳng
    - `1H4?4-4` Xác định mặt phẳng đi qua một điểm và song song với một mặt phẳng
    - `1H4?4-5` Xác định mặt phẳng chứa đường thẳng (hoặc đi qua hai điểm) và song
    - `1H4?4-6` Bài toán tổng hợp
    - `1H4?4-7` Toán thực tế áp dụng hai mặt phẳng song song
- Bài 5. Hình lăng trụ và hình hộp (xiên)
    - `1H4?5-1` Câu hỏi lý thuyết
    - `1H4?5-2` Bài toán về hình lăng trụ (xiên)
    - `1H4?5-3` Bài toán về hình hộp (xiên)
    - `1H4?5-4` Toán thực tế áp dụng hình lăng trụ và hình hộp
- Bài 6. Phép chiếu song song
    - `1H4?6-1` Câu hỏi lý thuyết
    - `1H4?6-2` Hình biểu diễn của một hình không gian
    - `1H4?6-3` Xác định yếu tố song song
    - `1H4?6-4` Xác định phương chiếu
    - `1H4?6-5` Tính tỉ số đoạn thẳng, diện tích qua phép chiếu

### Lớp 11 · Hình học · Quan hệ vuông góc trong không gian  (mã chương 1H8)
- Bài 1. Hai đường thẳng vuông góc
    - `1H8?1-1` Câu hỏi lý thuyết
    - `1H8?1-2` Xác định hai đường thẳng vuông góc
    - `1H8?1-3` Tìm góc giữa hai đường thẳng
    - `1H8?1-4` Toán thực tế áp dụng hai đường thẳng vuông góc
- Bài 2. Đường thẳng vuông góc với mặt phẳng
    - `1H8?2-1` Câu hỏi lý thuyết
    - `1H8?2-2` Xác định hoặc chứng minh đường thẳng và mặt phẳng vuông góc
    - `1H8?2-3` Xác định hoặc chứng minh hai đường thẳng vuông góc
    - `1H8?2-4` Dựng mặt phẳng, tìm thiết diện
    - `1H8?2-5` Hình chiếu vuông góc của một hình trên mặt phẳng (tìm điểm, tìm đoạn
    - `1H8?2-6` Toán thực tế áp dụng đường thẳng vuông góc mặt phẳng
- Bài 3. Phép chiếu vuông góc
    - `1H8?3-1` Lý thuyết về phép chiếu vuông góc
    - `1H8?3-2` Hình chiếu vuông góc của đa giác trên mặt phẳng
    - `1H8?3-3` Các bài toán thực tế áp dụng phép chiếu vuông góc
- Bài 4. Hai mặt phẳng vuông góc
    - `1H8?4-1` Câu hỏi lý thuyết
    - `1H8?4-3` Xác định góc giữa hai mặt phẳng
    - `1H8?4-4` Dựng mặt phẳng, thiết diện
    - `1H8?4-5` Nhận dạng và tính toán liên quan các hình thông dụng
    - `1H8?4-6` Bài toán cho trước góc giữa 𝑑và (𝑃)
    - `1H8?4-7` Toán thực tế áp dụng hai mặt phẳng vuông góc
- Bài 5. Khoảng cách
    - `1H8?5-1` Câu hỏi lý thuyết
    - `1H8?5-2` Khoảng cách giữa 2 điểm, từ 1 điểm đến 1 đường thẳng
    - `1H8?5-3` Khoảng cách từ một điểm đến một mặt phẳng
    - `1H8?5-4` Khoảng cách giữa hai đường thẳng chéo nhau
    - `1H8?5-5` Đường vuông góc chung của hai đường thẳng chéo nhau
    - `1H8?5-6` Toán thực tế áp dụng khoảng cách
- Bài 6. Góc giữa đường thẳng và mặt phẳng. Góc nhị diện
    - `1H8?6-1` Góc giữa đường thẳng và mặt phẳng
    - `1H8?6-2` Góc nhị diện, góc phẳng nhị diện
    - `1H8?6-3` Góc giữa 2 mặt phẳng, biết trước góc (𝑑, (𝑃))
    - `1H8?6-4` Khoảng cách giữa điểm, đường, biết trước góc (𝑑, (𝑃))
    - `1H8?6-5` Khoảng cách giữa điểm - mặt phẳng, biết trước góc (𝑑, (𝑃))
    - `1H8?6-6` Khoảng cách giữa 2 đường chéo nhau, biết trước góc (𝑑, (𝑃))
    - `1H8?6-7` Toán thực tế về góc đường thẳng, mặt phẳng, góc nhị diện
- Bài 7. Hình lăng trụ đứng. Hình chóp đều. Thể tích
    - `1H8?7-1` Câu hỏi lý thuyết, công thức
    - `1H8?7-2` Thể tích khối chóp tam giác
    - `1H8?7-3` Thể tích khối chóp tứ giác
    - `1H8?7-4` Thể tích khối lăng trụ tam giác
    - `1H8?7-5` Thể tích khối lăng trụ tứ giác
    - `1H8?7-6` Thể tích khối chóp cụt và các khối khác
    - `1H8?7-7` Tỉ số thể tích
    - `1H8?7-8` Ứng dụng thể tích tính góc, khoảng cách,...
    - `1H8?7-9` Toán thực tế hình lăng trụ đứng, chóp đều, thể tích

### Lớp 11 · Chuyên đề / Xác suất · Phép biến hình phẳng  (mã chương 1C1)
- Bài 1. Phép biến hình, phép dời hình và hai hình bằng nhau
    - `1C1?1-1` Câu hỏi lý thuyết
    - `1C1?1-2` Bài toán xác định một phép đặt tương ứng có là phép dời hình hay không?
    - `1C1?1-3` Xác định ảnh khi thực hiện phép dời hình
- Bài 2. Phép tịnh tiến
    - `1C1?2-1` Câu hỏi lý thuyết
    - `1C1?2-2` Tìm ảnh hoặc tạo ảnh khi thực hiện phép tịnh tiến
    - `1C1?2-3` Ứng dụng phép tịnh tiến
- Bài 3. Phép đối xứng trục
    - `1C1?3-1` Câu hỏi lý thuyết
    - `1C1?3-2` Tìm ảnh hoặc tạo ảnh khi thực hiện phép đối xứng trục
    - `1C1?3-3` Xác định trục đối xứng và số trục đối xứng của một hình
    - `1C1?3-4` Ứng dụng phép đối xứng trục
- Bài 4. Phép đối xứng tâm
    - `1C1?4-1` Câu hỏi lý thuyết
    - `1C1?4-2` Tìm ảnh, tạo ảnh khi thực hiện phép đối xứng tâm
    - `1C1?4-3` Xác định hình có tâm đối xứng
    - `1C1?4-4` Ứng dụng phép đối xứng tâm
- Bài 5. Phép quay
    - `1C1?5-1` Câu hỏi lý thuyết
    - `1C1?5-2` Xác định vị trí ảnh của điểm, hình khi thực hiện phép quay cho trước
    - `1C1?5-3` Tìm tọa độ ảnh của điểm, phương trình của một đường thẳng khi thực
    - `1C1?5-4` Ứng dụng phép quay
- Bài 6. Phép vị tự
    - `1C1?6-1` Câu hỏi lý thuyết
    - `1C1?6-2` Xác định ảnh, tạo ảnh khi thực hiện phép vị tự
    - `1C1?6-3` Tìm tâm vị tự của hai đường tròn
    - `1C1?6-4` Ứng dụng phép vị tự
- Bài 7. Phép đồng dạng
    - `1C1?7-1` Câu hỏi lý thuyết
    - `1C1?7-2` Xác định ảnh, tạo ảnh khi thực hiện phép đồng dạng

### Lớp 11 · Chuyên đề / Xác suất · Lý thuyết đồ thị  (mã chương 1C2)
- Bài 1. Đồ thị
    - `1C2?1-1` Câu hỏi về đỉnh, cạnh của đồ thị
    - `1C2?1-2` Câu hỏi về bậc của đồ thị
    - `1C2?1-3` Câu hỏi tổng hợp
- Bài 2. Đường đi Euler và Harmilton
    - `1C2?2-1` Đường đi Euler
    - `1C2?2-2` Đường đi Harmilton
    - `1C2?2-3` Câu hỏi tổng hợp
- Bài 3. Bài toán tìm đường đi ngắn nhất
    - `1C2?3-1` Bài toán tìm đường đi ngắn nhất
    - `1C2?3-2` Tổng hợp

### Lớp 11 · Chuyên đề / Xác suất · Một số yếu tố vẽ kỹ thuật  (mã chương 1C3)
- Bài 1. Hình biểu diễn của một hình, khối
    - `1C3?1-1` Lý thuyết về phép chiếu và hình biểu diễn song song
    - `1C3?1-2` Lý thuyết về phép chiếu vuông góc
    - `1C3?1-3` Lý thuyết về phép chiếu trục đo
    - `1C3?1-4` Tổng hợp
- Bài 2. Bản vẽ kỹ thuật
    - `1C3?2-1` Lý thuyết cơ bản về bản vẽ kỹ thuật
    - `1C3?2-2` Phương pháp biểu diễn bản vẽ kỹ thuật
    - `1C3?2-3` Tổng hợp
