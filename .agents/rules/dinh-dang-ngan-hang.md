---
trigger: always_on
description: Định dạng bắt buộc của mỗi câu hỏi trong ngân hàng LaTeX NganHangCaNhan (ex/bt, choice, choiceTF, shortans, loigiai, mã dạng)
---

# Định dạng câu hỏi ngân hàng (bắt buộc)

Mỗi câu một khối. Dòng mở khối có mã dạng NGAY sau `\begin{..}`: `\begin{ex}%[0H5H3-2]`
- Mã = lớp (0=10, 1=11, 2=12, 6…9 THCS) · môn (D/H/C) · chương · **mức** · bài - dạng. Lấy `0H5?3-2` từ `scripts/tra_dang.py`, thay `?` bằng mức.
- Mức: `N` nhận biết (1 bước, nhớ công thức) · `H` thông hiểu (2–3 bước quen) · `V` vận dụng (nhiều bước, thực tế quen) · `C` vận dụng cao.
- Không ghi `%[ma:…]` — chương trình tự gắn. Thêm dòng chú thích nguồn ngay dưới dòng mở: `% nguon: <tài liệu> – <trang/ví dụ>`.

| Loại | Môi trường | Bắt buộc |
|---|---|---|
| Trắc nghiệm 4 PA | `ex` + `\choice{…}{…}{…}{…}` | đúng MỘT `\True`; PA không ghi "A."; lời giải KHÔNG ghi "Chọn A"/"Đáp án B" |
| Đúng/Sai | `ex` + `\choiceTF{…}{…}{…}{…}` | ý đúng có `\True`; lời giải `\begin{itemchoice}` đủ 4 `\itemch` mở đầu "Đúng." / "Sai."; ý d khó nhất; không nhắc "ý a", "b)" |
| Trả lời ngắn | `bt` + `\shortans{đáp số}` | đáp số ≤ 4 ký tự, dấu phẩy thập phân (`2,5`), làm tròn theo đề |
| Tự luận | `bt`, không `\shortans` | lời giải đủ bước |

Mọi câu có `\loigiai{…}` không rỗng. Công thức trong `$…$` (không dùng `\(` `\[`), số thập phân trong công thức viết `15{,}25`.
Không Markdown (`**`, `#`) bên trong khối. Hình: `tikzpicture` (đặt trong `\immini{đề}{hình}` nếu muốn hình cạnh đề); hình chưa vẽ được thì ghi `% CAN_VE_HINH` và mô tả.
Câu không chắc đáp án/nguồn → thêm dòng `% KIEM_TRA: <lý do>`.

Mẫu tin cậy: `mau_cau_moi.tex` (tex) · `mau_cau_moi.json` (JSON 13 trường, thêm trường `"Mã dạng"`).
Ví dụ Trả lời ngắn:
```latex
\begin{bt}%[0D3V2-3]
% nguon: SGK Toán 10 KNTT tập 1 – Bài 6, Bài tập 6.10
	Một quả bóng được ném lên theo quỹ đạo $y=-0{,}1x^2+x+1$ (mét). Độ cao lớn nhất của quả bóng là bao nhiêu mét?
	\shortans{3,5}
	\loigiai{
		Đỉnh parabol: $x=-\dfrac{b}{2a}=5$, $y(5)=-2{,}5+5+1=3{,}5$ (m).
	}
\end{bt}
```
