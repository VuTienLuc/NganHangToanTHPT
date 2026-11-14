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
- Công thức trong `$...$`; dùng `\dfrac`, `\sqrt`, `\left(…\right)`, `\mathbb{R}`, hệ `\heva{&x=1\\&y=2}`, tuyển `\hoac{&x=1\\&x=2}`.
- **Vectơ** viết `\overrightarrow{AB}`, `\overrightarrow{F_1}` (không dùng `\vec`).
- **Số thập phân trong công thức** viết dấu phẩy trong ngoặc nhọn: `$15{,}25$`, `$0{,}33\%$`, `$\approx 4{,}11$`
  (viết `$15,25$` LaTeX sẽ in thành "15, 25"). Riêng `\shortans{4,1}` viết phẩy thường, không có `$`.
- Số lớn tách nhóm bằng `\,`: `$10\,000$`. Đơn vị: `$40\text{ km}$`, `$50\text{ N}$`, `$180{,}57\text{ cm}^2$`.
- **Xuống dòng trong đề và lời giải**: mỗi ý/bước tính cuối dòng thêm `\\` (LaTeX bỏ qua xuống dòng thường, các câu sẽ dính vào nhau).
  Công thức dài hoặc quan trọng đặt riêng một dòng: `\[ \overline{x}=\dfrac{1525}{100}=15{,}25. \]`
- Bảng số liệu: `\begin{center}\begin{tabular}{|l|c|c|…|}\hline … \\ \hline\end{tabular}\end{center}`;
  bảng nhiều hơn 8 cột bọc thêm `\resizebox{\linewidth}{!}{ … }` để in 2 cột không tràn.
- Hình vẽ, đồ thị, bảng biến thiên: làm theo mục **HÌNH VẼ (TikZ)** bên dưới.
- Đề có đáp án/lời giải: dùng của đề. Đề **không** có: tự giải cẩn thận, tính lại từng phép tính, viết lời giải ngắn gọn đúng chuẩn.
  Câu nào không chắc chắn, thêm chú thích cuối dòng mở khối: `%[2D1V3-6] % KIEM_TRA: lý do`.
- Lời giải không nhắc tới thứ tự phương án/ý ("Chọn B", "phương án A", "ý a)…") vì khi trộn đề thứ tự bị đảo.
- KHÔNG viết `\documentclass`, `\begin{document}`, lời dẫn hay giải thích ngoài các khối câu hỏi.
- Không đánh số "Câu 1." trong nội dung (số câu tự sinh khi in).

# HÌNH VẼ (TikZ) — cấu trúc và vị trí
**Nguyên tắc chung**
- Mỗi hình là MỘT khối `\begin{tikzpicture}[scale=…] … \end{tikzpicture}`, gõ thẳng trong câu hỏi.
  KHÔNG viết `\documentclass`, `\usepackage`, `\usetikzlibrary`, `\begin{document}`, không dùng `\includegraphics`, không file ảnh ngoài.
- Gói đã có sẵn: `tikz` (thư viện calc, angles, quotes, intersections, patterns, arrows.meta, decorations.markings, shapes),
  `tkz-euclide`, `tkz-tab` (bảng biến thiên), `tikz-3dplot`, `pgfplots`. Chỉ dùng lệnh của các gói này.
- Trong khối tikzpicture: **không để dòng trống**, không chú thích `%`, ngoặc `{}` `[]` `()` đóng mở khớp,
  mỗi lệnh kết thúc bằng `;`. Nhãn toán trong `$…$`: `node[below]{$A$}`. Không dùng `\pgfmathsetmacro`, `\newcommand`, `\def` trong hình.
- Kích thước: hình đặt cạnh đề rộng ≤ 5 cm, hình đặt giữa rộng ≤ 9 cm (dùng `scale=0.6`…`1`); nét `line join=round`, mũi tên `->` hoặc `-stealth`.
- Đồ thị hàm số: `\draw[thick,smooth,samples=100,domain=a:b] plot(\x,{biểu thức});` — biểu thức viết kiểu pgf:
  `\x^2` → `(\x)^2` hoặc `\x*\x`, `e^x` → `exp(\x)`, `ln x` → `ln(\x)`, `sin x` (radian) → `sin(\x r)`.
- Hình không vẽ chắc chắn đúng thì KHÔNG vẽ bừa: để `\begin{center}\textit{[Hình: mô tả ngắn]}\end{center} % CAN_VE_HINH`.

**Vị trí đặt hình trong câu** (sai vị trí là lỗi nhập/biên dịch hay gặp)
1. Hình nhỏ minh hoạ đề (đồ thị, hình học phẳng/không gian) → đặt **bên phải đề** bằng `\immini`, ngay sau dòng mở khối, **trước** `\choice`:
```latex
\begin{ex}%[2D1H1-1]
	\immini{Cho hàm số $y=f(x)$ có đồ thị như hình bên. Hàm số đồng biến trên khoảng nào?}
	{\begin{tikzpicture}[scale=0.7,>=stealth]
		\draw[->] (-2,0)--(3,0) node[below]{$x$};
		\draw[->] (0,-2)--(0,3) node[left]{$y$};
		\draw[thick,smooth,samples=100,domain=-1.3:2.4] plot(\x,{(\x)^3-1.5*(\x)^2});
		\node[below left] at (0,0) {$O$};
	\end{tikzpicture}}
	\choice
	{$(0;1)$}
	{\True $(1;+\infty)$}
	{$(-1;0)$}
	{$(-\infty;1)$}
	\loigiai{ … }
\end{ex}
```
   `\immini` có đúng **2 cặp ngoặc**: `{nội dung đề}` rồi `{khối tikzpicture}`; câu hỏi chính nằm trong cặp ngoặc thứ nhất.
2. Hình lớn hoặc **bảng biến thiên / bảng xét dấu** → đặt **giữa đề** trong `\begin{center}…\end{center}`, sau câu dẫn, trước câu hỏi chính và trước `\choice`:
```latex
	Cho hàm số $y=f(x)$ có bảng biến thiên như sau:
	\begin{center}
		\begin{tikzpicture}
			\tkzTabInit[lgt=1.2,espcl=2.2]{$x$/0.8,$y'$/0.8,$y$/2}{$-\infty$,$-1$,$1$,$+\infty$}
			\tkzTabLine{,+,0,-,0,+,}
			\tkzTabVar{-/$-\infty$,+/$3$,-/$-1$,+/$+\infty$}
		\end{tikzpicture}
	\end{center}
	Hàm số đạt cực đại tại điểm nào?
	\choice …
```
   Số cột của `\tkzTabLine` = 2×(số giá trị $x$) − 1 ô (dùng `,` ngăn cách; `0` là nghiệm, `d` là không xác định, `+`/`-` là dấu).
   `\tkzTabVar`: mỗi giá trị $x$ một mục `-/giá trị` (đáy) hoặc `+/giá trị` (đỉnh).
3. Hình trong **lời giải** → đặt **bên trong** `\loigiai{ … }` (thường trong `\begin{center}…\end{center}`).
4. Hình làm **phương án** A/B/C/D (chọn đồ thị đúng) → mỗi phương án một tikzpicture nhỏ (`scale=0.4`, rộng ≤ 3,5 cm) đặt trong ngoặc của phương án:
   `{\begin{tikzpicture}[scale=0.4] … \end{tikzpicture}}`.
5. KHÔNG đặt hình sau `\choice`/`\shortans`, giữa các phương án, hay ngoài `\end{ex}`.

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
- [ ] Mỗi hình: khối tikzpicture không dòng trống, ngoặc khớp, đúng vị trí (immini / center / trong \loigiai / trong ngoặc phương án).
- [ ] Số thập phân trong `$…$` đã viết `{,}`; các bước lời giải đã có `\\` cuối dòng hoặc `\[…\]`.

# KẾT QUẢ TRẢ VỀ
Một khối mã duy nhất ```latex … ``` chứa lần lượt mọi câu theo thứ tự trong đề (Phần I → II → III → Tự luận).
Ngay dòng đầu khối ghi chú thích nguồn: `% nguồn: <tên đề, trường, năm học nếu có>`.
Sau khối mã, liệt kê ngắn: số câu mỗi loại, các câu có `% KIEM_TRA` hoặc `% CAN_VE_HINH`.
Thầy sẽ lưu khối mã thành file `.tex` (hoặc `.txt`) rồi nhập vào ngân hàng.

# DANH MỤC DẠNG ({SO} dạng) — chỉ dùng các mã dưới đây
{DANH_MUC}
'''

def tao_prompt(pham_vi):
    dm, so = danh_muc(pham_vi)
    return MAU.replace("{SO}", str(so)).replace("{DANH_MUC}", dm)

# ======================================================================= SOẠN CÂU HỎI MỚI THEO BÀI HỌC
LOAI_TEN = {"TN": "Trắc nghiệm 4 phương án", "DS": "Đúng/Sai (4 ý)", "TLN": "Trả lời ngắn", "TL": "Tự luận"}
MUC_TEN = {"N": "Nhận biết", "H": "Thông hiểu", "V": "Vận dụng", "C": "Vận dụng cao"}
CACH_SOAN = {
    "bam_sat": "BÁM SÁT tài liệu: lấy ý tưởng từ lý thuyết, ví dụ, luyện tập, bài tập trong tài liệu; ĐỔI số liệu, "
               "đổi ngữ cảnh để thành câu mới (không chép nguyên văn).",
    "sang_tao": "SOẠN MỚI cùng dạng, cùng mức với nội dung tài liệu: câu hỏi mới hoàn toàn nhưng chỉ dùng kiến thức có trong tài liệu.",
    "ket_hop": "KẾT HỢP: khoảng một nửa bám sát ví dụ/bài tập của tài liệu (đổi số liệu), một nửa soạn mới cùng dạng.",
}

def danh_sach_dang():
    """Toàn bộ dạng trong danh mục (kể cả dạng chưa có câu) cho ứng dụng chọn bài."""
    id_map = tai_id_map()
    ra = []
    for k, t in id_map.items():
        m = re.match(r"(\d)([A-Z])(\d+)\?(\d+)-(\d+)$", k)
        if m:
            ra.append({"k": k, "lop": 10 + int(m.group(1)), "mon": m.group(2), "chuong": int(m.group(3)),
                       "bai": int(m.group(4)), "dang": int(m.group(5)), "ten_chuong": t.get("chap_name", "").strip(),
                       "ten_bai": t.get("lesson_name", "").strip(), "ten_dang": t.get("type_name", "").strip()})
    ra.sort(key=lambda d: (d["lop"], "DHC".find(d["mon"]), d["chuong"], d["bai"], d["dang"]))
    return ra

def tao_prompt_soan(cac_dang, so_cau, tai_lieu="", cach="ket_hop", thuc_te=False, ghi_chu=""):
    """cac_dang: danh sách mã '2D1?1-2'; so_cau: {"TN":[N,H,V,C], ...}."""
    id_map = tai_id_map()
    cac_dang = [k for k in cac_dang if k in id_map]
    if not cac_dang:
        raise ValueError("Chưa chọn dạng nào.")
    bai = sorted({(id_map[k]["chap_name"].strip(), id_map[k]["lesson_name"].strip(), k.split("?")[0], k.split("?")[1].split("-")[0])
                  for k in cac_dang})
    lop = 10 + int(cac_dang[0][0])
    ten_bai = "; ".join(f"{b[1]}" for b in bai)
    dong_bang, tong = [], 0
    for l in ("TN", "DS", "TLN", "TL"):
        v = [int(x or 0) for x in (so_cau.get(l) or [0, 0, 0, 0])][:4]
        if sum(v):
            tong += sum(v)
            dong_bang.append(f"| {LOAI_TEN[l]} | " + " | ".join(str(x) for x in v) + f" | **{sum(v)}** |")
    if not tong:
        raise ValueError("Chưa nhập số câu.")
    dang_txt = "\n".join(f"- `{k}` {id_map[k]['type_name'].strip()}  _(bài: {id_map[k]['lesson_name'].strip()})_" for k in cac_dang)
    chung = MAU[MAU.index("# ĐỊNH DẠNG BẮT BUỘC"):MAU.index("# KẾT QUẢ TRẢ VỀ")]
    chung = chung.replace("Lấy từ DANH MỤC DẠNG ở cuối", "Lấy từ DANH SÁCH DẠNG ở trên").replace(
        "Mã lấy từ DANH MỤC DẠNG ở cuối", "Mã lấy từ DANH SÁCH DẠNG ĐƯỢC CHỌN ở trên")
    chung = re.sub(r"- Đề có đáp án/lời giải: dùng của đề\. Đề \*\*không\*\* có: ", "- ", chung)
    i, j = chung.find("# CHỌN MÃ DẠNG CHO ĐÚNG"), chung.find("# TỰ KIỂM TRA")
    if 0 <= i < j:
        chung = chung[:i] + chung[j:]
    chung = chung.replace("Đủ số câu như đề", "Đủ số câu theo loại × mức như bảng")
    p = f"""# NHIỆM VỤ
Thầy là giáo viên Toán THPT (chương trình GDPT 2018). Đính kèm là **tài liệu học tập**{(': ' + tai_lieu) if tai_lieu else ''}.
Hãy **đọc kỹ tài liệu** (lý thuyết, định nghĩa, công thức, ví dụ, luyện tập, bài tập) rồi **SOẠN CÂU HỎI MỚI** cho:
**Lớp {lop} — {ten_bai}** ({bai[0][0]}).
Câu hỏi phải đúng phạm vi bài học: chỉ dùng kiến thức có trong tài liệu và các bài trước, KHÔNG dùng kiến thức của bài sau.

## Cách soạn
- {CACH_SOAN.get(cach, CACH_SOAN['ket_hop'])}
- Mỗi câu đúng MỘT dạng trong danh sách dưới; **rải đều các dạng** (mỗi dạng có ít nhất 1 câu nếu đủ số câu), không dồn một dạng.
{'- Ưu tiên **toán thực tế** (đời sống, khoa học, kinh tế, kĩ thuật): khoảng một nửa số câu Vận dụng / Vận dụng cao là bài toán thực tế.' if thuc_te else '- Có một số câu vận dụng gắn với tình huống thực tế khi phù hợp.'}
- Trắc nghiệm: phương án nhiễu lấy từ **lỗi sai thường gặp** của học sinh (sai dấu, nhầm công thức, quên điều kiện…);
  đáp án đúng **rải đều A, B, C, D**; không dùng phương án "Cả A, B đều đúng", "Không có đáp án".
- Đúng/Sai: 4 ý **tăng dần độ khó** a → d (ý d khó nhất); các câu có số ý đúng khác nhau (không phải lúc nào cũng 2 Đúng 2 Sai).
- Trả lời ngắn: đáp số là một số, tối đa 4 ký tự (kể cả `-` và `,`); nếu cần làm tròn thì nói rõ trong đề ("làm tròn đến hàng phần mười").
- Mọi câu có **lời giải chi tiết**, tính toán đã được kiểm tra lại; số liệu đẹp, đáp án duy nhất.
{('- Yêu cầu thêm của thầy: ' + ghi_chu) if ghi_chu else ''}

## Số lượng câu cần soạn (tổng {tong} câu)
| Loại câu | Nhận biết (N) | Thông hiểu (H) | Vận dụng (V) | Vận dụng cao (C) | Cộng |
|---|---|---|---|---|---|
{chr(10).join(dong_bang)}

Mức của từng câu phải đúng như bảng (chữ mức N/H/V/C ghi trong mã `%[…]`).

## DANH SÁCH DẠNG ĐƯỢC CHỌN — chỉ dùng các mã dưới đây (thay `?` bằng N/H/V/C)
{dang_txt}

{chung}
# KẾT QUẢ TRẢ VỀ
Một khối mã duy nhất ```latex … ``` chứa các câu xếp theo loại (Trắc nghiệm → Đúng/Sai → Trả lời ngắn → Tự luận), trong mỗi loại xếp theo mức N → H → V → C.
Dòng đầu khối: `% nguồn: Soạn theo {ten_bai} – {tai_lieu or 'tài liệu đính kèm'}`.
Sau khối mã, liệt kê ngắn: số câu theo loại × mức, số câu mỗi dạng, các câu có `% KIEM_TRA` hoặc `% CAN_VE_HINH`.
Thầy sẽ lưu khối mã thành file `.tex` (hoặc `.txt`) rồi nhập vào ngân hàng.
"""
    return re.sub(r"\n{3,}", "\n\n", p)

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
