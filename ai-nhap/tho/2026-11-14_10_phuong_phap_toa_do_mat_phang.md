# Nháp thô từ NotebookLM - Ngày 2026-11-14
## Lớp 10 - Chương Phương pháp toạ độ trong mặt phẳng

```json
[
  {
    "loai": "TL",
    "muc": "N",
    "dang": "Toạ độ điểm, toạ độ vectơ, trung điểm đoạn thẳng và trọng tâm tam giác",
    "de": "Trong mặt phẳng toạ độ $Oxy$, cho ba điểm không thẳng hàng $A(1; 3)$, $B(-2; 6)$, $C(5; 1)$.\na) Tìm toạ độ của vectơ $\\vec{AB}$.\nb) Tìm toạ độ trung điểm $I$ của đoạn thẳng $AB$.\nc) Tìm toạ độ trọng tâm $G$ của tam giác $ABC$.",
    "phuong_an": [],
    "dap_an": "",
    "loi_giai": "a) Toạ độ của vectơ $\\vec{AB}$ là:\n$\\vec{AB} = (x_B - x_A; y_B - y_A) = (-2 - 1; 6 - 3) = (-3; 3)$.\nb) Vì $I$ là trung điểm của đoạn thẳng $AB$ nên:\n$x_I = \\dfrac{x_A + x_B}{2} = \\dfrac{1 + (-2)}{2} = -\\dfrac{1}{2}$, $y_I = \\dfrac{y_A + y_B}{2} = \\dfrac{3 + 6}{2} = \\dfrac{9}{2}$.\nVậy $I\\left(-\\dfrac{1}{2}; \\dfrac{9}{2}\\right)$.\nc) Vì $G$ là trọng tâm của tam giác $ABC$ nên:\n$x_G = \\dfrac{x_A + x_B + x_C}{3} = \\dfrac{1 + (-2) + 5}{3} = \\dfrac{4}{3}$, $y_G = \\dfrac{y_A + y_B + y_C}{3} = \\dfrac{3 + 6 + 1}{3} = \\dfrac{10}{3}$.\nVậy $G\\left(\\dfrac{4}{3}; \\dfrac{10}{3}\\right)$.",
    "nguon": "Gợi ý từ Ví dụ 4, Bài 10 – SGK Toán 10 KNTT tập 1, trang 63"
  },
  {
    "loai": "TL",
    "muc": "H",
    "dang": "Phương trình đường thẳng, đường cao, khoảng cách và góc trong tam giác",
    "de": "Cho tam giác $ABC$ với $A(1; -1)$, $B(3; 5)$, $C(-2; 4)$.\na) Viết phương trình tham số của đường thẳng $AB$.\nb) Viết phương trình đường cao $AH$ của tam giác $ABC$.\nc) Tính khoảng cách từ điểm $A$ đến đường thẳng $BC$.\nd) Tính $\\sin$ của góc giữa hai đường thẳng $AB$ và $AC$.",
    "phuong_an": [],
    "dap_an": "",
    "loi_giai": "a) Ta có $\\vec{AB} = (2; 6)$ là một vectơ chỉ phương của đường thẳng $AB$, suy ra $\\vec{u} = (1; 3)$ cũng là một vectơ chỉ phương của $AB$.\nĐường thẳng $AB$ đi qua điểm $A(1; -1)$ và nhận $\\vec{u} = (1; 3)$ làm vectơ chỉ phương nên có phương trình tham số là:\n$\\begin{cases} x = 1 + t \\\\ y = -1 + 3t \\end{cases}$ ($t \\in \\mathbb{R}$).\nb) Vì đường cao $AH$ vuông góc với $BC$ nên nhận $\\vec{BC} = (-5; -1)$ làm một vectơ pháp tuyến, do đó $\\vec{n} = (5; 1)$ cũng là một vectơ pháp tuyến của $AH$.\nĐường cao $AH$ đi qua $A(1; -1)$ có phương trình tổng quát là:\n$5(x - 1) + 1(y + 1) = 0 \\Leftrightarrow 5x + y - 4 = 0$.\nc) Đường thẳng $BC$ nhận $\\vec{BC} = (-5; -1)$ làm vectơ chỉ phương nên nhận $\\vec{n}' = (1; -5)$ làm một vectơ pháp tuyến. Phương trình tổng quát của $BC$ (đi qua $B(3; 5)$) là:\n$1(x - 3) - 5(y - 5) = 0 \\Leftrightarrow x - 5y + 22 = 0$.\nKhoảng cách từ điểm $A(1; -1)$ đến đường thẳng $BC$ là:\n$d(A, BC) = \\dfrac{|1 - 5\\cdot(-1) + 22|}{\\sqrt{1^2 + (-5)^2}} = \\dfrac{28}{\\sqrt{26}} = \\dfrac{14\\sqrt{26}}{13}$.\nd) Gọi $\\alpha$ là góc giữa hai đường thẳng $AB$ và $AC$. Ta có $\\vec{AB} = (2; 6)$ và $\\vec{AC} = (-3; 5)$.\nKhi đó:\n$\\cos\\alpha = |\\cos(\\vec{AB}, \\vec{AC})| = \\dfrac{|2\\cdot(-3) + 6\\cdot 5|}{\\sqrt{2^2 + 6^2}\\cdot\\sqrt{(-3)^2 + 5^2}} = \\dfrac{24}{\\sqrt{40}\\cdot\\sqrt{34}} = \\dfrac{6}{\\sqrt{85}}$.\nSuy ra $\\sin\\alpha = \\sqrt{1 - \\cos^2\\alpha} = \\sqrt{1 - \\dfrac{36}{85}} = \\dfrac{7}{\\sqrt{85}}$.",
    "nguon": "SBT Toán 10 KNTT tập 2 – Bài 7.55, trang 49, lời giải trang 108"
  },
  {
    "loai": "TL",
    "muc": "H",
    "dang": "Xác định tâm, bán kính đường tròn và viết phương trình tiếp tuyến tại một điểm",
    "de": "Cho đường tròn $(C)$ có phương trình $x^2 + y^2 - 4x + 6y - 12 = 0$.\na) Tìm toạ độ tâm $I$ và bán kính $R$ của $(C)$.\nb) Chứng minh rằng điểm $M(5; 1)$ thuộc $(C)$. Viết phương trình tiếp tuyến $d$ của $(C)$ tại $M$.",
    "phuong_an": [],
    "dap_an": "",
    "loi_giai": "a) Phương trình đường tròn $(C)$ có dạng $x^2 + y^2 - 2ax - 2by + c = 0$ với $a = 2$, $b = -3$, $c = -12$.\nVậy $(C)$ có tâm $I(2; -3)$ và bán kính $R = \\sqrt{2^2 + (-3)^2 - (-12)} = \\sqrt{25} = 5$.\nb) Thay toạ độ điểm $M(5; 1)$ vào phương trình của $(C)$ ta có:\n$5^2 + 1^2 - 4\\cdot 5 + 6\\cdot 1 - 12 = 25 + 1 - 20 + 6 - 12 = 0$.\nVậy điểm $M(5; 1)$ thuộc đường tròn $(C)$.\nTiếp tuyến $d$ của $(C)$ tại điểm $M$ đi qua $M(5; 1)$ và vuông góc với $IM$ nên nhận vectơ $\\vec{IM} = (5 - 2; 1 - (-3)) = (3; 4)$ làm một vectơ pháp tuyến.\nPhương trình tiếp tuyến $d$ là:\n$3(x - 5) + 4(y - 1) = 0 \\Leftrightarrow 3x + 4y - 19 = 0$.",
    "nguon": "SBT Toán 10 KNTT tập 2 – Bài 7.57, trang 50, lời giải trang 109"
  },
  {
    "loai": "TL",
    "muc": "V",
    "dang": "Bài toán thực tế ứng dụng phương trình chính tắc của đường elip",
    "de": "Một người kĩ sư thiết kế một đường hầm một chiều có mặt cắt là một nửa hình elip, chiều rộng của hầm là $12\\text{ m}$, khoảng cách từ điểm cao nhất của elip so với mặt đường là $3\\text{ m}$. Người kĩ sư này muốn đưa ra cảnh báo cho các xe có thể đi qua hầm. Biết rằng những loại xe tải có chiều cao $2{,}8\\text{ m}$ thì có chiều rộng không quá $3\\text{ m}$. Hỏi chiếc xe tải có chiều cao $2{,}8\\text{ m}$ có thể đi qua hầm được không?",
    "phuong_an": [],
    "dap_an": "",
    "loi_giai": "Chọn hệ trục toạ độ $Oxy$ sao cho trục $Ox$ nằm dọc theo mặt đường, gốc $O$ là trung điểm đoạn thẳng nối hai chân vòm hầm trên mặt đường, trục $Oy$ hướng thẳng đứng lên trên (trùng với trục đối xứng của mặt cắt).\nKhi đó nửa hình elip nằm phía trên trục $Ox$ thuộc elip $(E)$ có phương trình chính tắc dạng $\\dfrac{x^2}{a^2} + \\dfrac{y^2}{b^2} = 1$ ($a > b > 0$).\nVì chiều rộng của hầm là $12\\text{ m}$ và khoảng cách từ điểm cao nhất của elip so với mặt đường là $3\\text{ m}$ nên elip $(E)$ đi qua các điểm $A(6; 0)$ và $B(0; 3)$.\nThay toạ độ $A, B$ vào phương trình của $(E)$ ta được $a = 6$ và $b = 3$, suy ra phương trình chính tắc của $(E)$ là:\n$\\dfrac{x^2}{36} + \\dfrac{y^2}{9} = 1$.\nĐể đi qua hầm thuận lợi nhất, xe tải chạy ở chính giữa hầm. Với xe tải có chiều rộng không quá $3\\text{ m}$, điểm cao nhất ở mép ngoài của xe ứng với hoành độ $x = 1{,}5$.\nThay $x = 1{,}5$ vào phương trình elip $(E)$ (với $y_M > 0$), ta tìm được độ cao tối đa của vòm hầm tại vị trí này là:\n$y_M = 3\\sqrt{1 - \\dfrac{1{,}5^2}{36}} = 3\\sqrt{1 - \\dfrac{1}{16}} = \\dfrac{3\\sqrt{15}}{4} \\approx 2{,}905\\text{ (m)}$.\nVì $2{,}905\\text{ m} > 2{,}8\\text{ m}$ nên chiếc xe tải có chiều cao $2{,}8\\text{ m}$ có thể đi qua hầm được (cần khuyến cáo xe phải đi vào chính giữa hầm).",
    "nguon": "SBT Toán 10 KNTT tập 2 – Bài 7.35, trang 46, lời giải trang 105–106"
  },
  {
    "loai": "TL",
    "muc": "C",
    "dang": "Tìm toạ độ điểm thoả mãn điều kiện cực trị khoảng cách (chu vi tam giác nhỏ nhất)",
    "de": "Trong mặt phẳng toạ độ $Oxy$, cho hai điểm $A(-3; 0)$, $B(1; -2)$ và đường thẳng $d: x + y - 1 = 0$.\na) Chứng minh rằng hai điểm $A$ và $B$ nằm cùng phía so với đường thẳng $d$.\nb) Điểm $M$ thay đổi trên đường thẳng $d$. Tìm toạ độ điểm $M$ để chu vi tam giác $ABM$ nhỏ nhất và tính giá trị nhỏ nhất đó.",
    "phuong_an": [],
    "dap_an": "",
    "loi_giai": "a) Đặt $f(x; y) = x + y - 1$. Ta có $f(-3; 0) = -3 + 0 - 1 = -4$ và $f(1; -2) = 1 + (-2) - 1 = -2$.\nVì $f(-3; 0)\\cdot f(1; -2) = (-4)\\cdot(-2) = 8 > 0$ nên hai điểm $A$ và $B$ nằm cùng phía đối với đường thẳng $d$.\nb) Chu vi tam giác $ABM$ là $P_{\\triangle ABM} = AB + MA + MB$.\nTa có $AB = \\sqrt{(1 - (-3))^2 + (-2 - 0)^2} = \\sqrt{16 + 4} = 2\\sqrt{5}$ (không đổi), nên chu vi tam giác $ABM$ nhỏ nhất khi và chỉ khi tổng $MA + MB$ nhỏ nhất.\nGọi $A'$ là điểm đối xứng với $A(-3; 0)$ qua đường thẳng $d: x + y - 1 = 0$.\nĐường thẳng $\\Delta$ đi qua $A(-3; 0)$ và vuông góc với $d$ nhận vectơ chỉ phương của $d$ là $\\vec{u}_d = (1; -1)$ làm vectơ pháp tuyến nên có phương trình:\n$1(x + 3) - 1(y - 0) = 0 \\Leftrightarrow x - y + 3 = 0$.\nGọi $H$ là hình chiếu vuông góc của $A$ lên $d$. Toạ độ điểm $H$ là nghiệm của hệ phương trình:\n$\\begin{cases} x + y - 1 = 0 \\\\ x - y + 3 = 0 \\end{cases} \\Leftrightarrow \\begin{cases} x = -1 \\\\ y = 2 \\end{cases} \\Rightarrow H(-1; 2)$.\nVì $H$ là trung điểm của $AA'$ nên:\n$\\begin{cases} x_{A'} = 2x_H - x_A = 2(-1) - (-3) = 1 \\\\ y_{A'} = 2y_H - y_A = 2(2) - 0 = 4 \\end{cases} \\Rightarrow A'(1; 4)$.\nDo $A'$ đối xứng với $A$ qua $d$ và $M \\in d$ nên $MA = MA'$. Áp dụng bất đẳng thức tam giác ta có:\n$MA + MB = MA' + MB \\ge A'B$.\nVì $A, B$ nằm cùng phía với $d$ nên $A', B$ nằm khác phía đối với $d$, do đó đoạn thẳng $A'B$ cắt $d$. Dấu bằng xảy ra khi và chỉ khi $M$ là giao điểm của đoạn thẳng $A'B$ với $d$.\nTa thấy $A'(1; 4)$ và $B(1; -2)$ có cùng hoành độ bằng $1$ nên đường thẳng $A'B$ có phương trình $x = 1$.\nToạ độ điểm $M$ là nghiệm của hệ $\\begin{cases} x = 1 \\\\ x + y - 1 = 0 \\end{cases} \\Leftrightarrow \\begin{cases} x = 1 \\\\ y = 0 \\end{cases} \\Rightarrow M(1; 0)$ (nằm giữa $A'$ và $B$).\nKhi đó $A'B = \\sqrt{(1 - 1)^2 + (-2 - 4)^2} = 6$.\nVậy chu vi tam giác $ABM$ đạt giá trị nhỏ nhất bằng $6 + 2\\sqrt{5}$ khi $M(1; 0)$.",
    "nguon": "Trích và mở rộng ý b từ Bài 7.17 – SBT Toán 10 KNTT tập 2, trang 38–39"
  }
]
```
