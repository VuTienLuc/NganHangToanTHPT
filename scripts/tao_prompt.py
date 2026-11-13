# -*- coding: utf-8 -*-
"""
SINH PROMPT để AI (ChatGPT, Gemini, Claude…) gõ lại một đề thi (PDF/ảnh/Word) thành câu hỏi LaTeX
đúng định dạng ngân hàng: mỗi câu một khối ex/bt, có mã %[lớp môn chương mức bài-dạng], lời giải.
  python3 scripts/tao_prompt.py --pham-vi 2D1,2D2,2H2              # in prompt ra màn hình
  python3 scripts/tao_prompt.py --pham-vi 1D1 --ra prompt_lop11.md  # ghi ra file
Dán prompt vào AI, đính kèm đề → lưu kết quả thành file .tex → ứng dụng "Nhập câu hỏi".
"""
import os, sys, re, argparse, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nh_core import *

MON = {"D": "Đại số – Giải tích", "H": "Hình học", "C": "Chuyên đề / Xác suất", "X": "Khác", "T": "Khác"}

def danh_muc(pham_vi):
    id_map = tai_id_map()
    def thuoc(k):
        return not pham_vi or any(k.startswith(t) and (len(t) <= 2 or len(k) == len(t) or k[len(t)] in "?-") for t in pham_vi)
    ds = [k for k in id_map if thuoc(k)]
    ds.sort(key=lambda k: (k[0], "DHC".find(k[1]), int(re.match(r"..(\d+)", k).group(1)),
                           int(k.split("?")[1].split("-")[0]), int(k.split("-")[1])))
    dong, chuong, bai = [], None, None
    for k in ds:
        t = id_map[k]
        kc = k.split("?")[0]
        if kc != chuong:
            chuong = kc; bai = None
            dong.append(f"\n### Lớp {10 + int(k[0])} · {MON.get(k[1], k[1])} · {t['chap_name']}  (mã chương {kc})")
        b = k.split("?")[1].split("-")[0]
        if b != bai:
            bai = b
            dong.append(f"- Bài {b}. {t['lesson_name']}")
        dong.append(f"    - `{kc}?{b}-{k.split('-')[1]}` {t['type_name'].strip()}")
    return "\n".join(dong), len(ds)

MAU = r'''# NHIỆM VỤ
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

# DANH MỤC DẠNG ({SO} dạng) — chỉ dùng các mã dưới đây
{DANH_MUC}
'''

def tao_prompt(pham_vi):
    dm, so = danh_muc(pham_vi)
    return MAU.replace("{SO}", str(so)).replace("{DANH_MUC}", dm)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pham-vi", default="", help="tiền tố mã chương, vd 2D1,2H2 (bỏ trống = mọi lớp)")
    ap.add_argument("--ra", help="ghi ra file .md")
    a = ap.parse_args()
    pv = [x.strip() for x in a.pham_vi.split(",") if x.strip()]
    p = tao_prompt(pv)
    if a.ra:
        open(a.ra, "w", encoding="utf-8").write(p); print(f"Đã ghi {a.ra} ({len(p):,} ký tự).")
    else:
        print(p)
