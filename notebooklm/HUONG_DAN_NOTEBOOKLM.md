# Antigravity (bộ não) + NotebookLM (kho dữ liệu) → Ngân hàng LaTeX

```
 NotebookLM                    Antigravity (Gemini, mở thư mục NganHangCaNhan)          Ngân hàng
 SGK, SBT, đề cũ  ──đọc nguồn──▶ chọn mã dạng · tự giải lại · chuẩn LaTeX/JSON ──▶ ai-nhap/*.tex|json
 (MCP notebooklm-mcp)  JSON nháp      kiem_tra_ai.py (0 LỖI) · nhap_cau.py --thu           │ /nhap-kho
                                                                                      cau-hoi/lopXX/… + git
```

NotebookLM giỏi **đọc đúng tài liệu của thầy** (ít bịa), nhưng không biết mã dạng, không biết khuôn `\choice`/`\True`.
Antigravity giỏi **suy luận, chạy lệnh, sửa file**. Ghép lại: NotebookLM đưa nguyên liệu có nguồn, Antigravity biến nó thành câu đúng chuẩn và nhập kho bằng chính công cụ của thầy.

## 1. Cài một lần

1. Nhấp đúp **`Cai dat NotebookLM cho Antigravity.command`** (trong `NganHangCaNhan`). File này:
   cài `uv` + gói `notebooklm-mcp-cli`, mở trình duyệt để đăng nhập Google, ghi cấu hình MCP cho Antigravity, thử liệt kê notebook.
2. Mở **Antigravity → Open Folder → `NganHangCaNhan`**. Antigravity tự đọc `AGENTS.md` (bộ não) và `.agents/rules/` (luật định dạng).
3. Khung Agent → `…` → **MCP Servers**: thấy `notebooklm-mcp` là được. Gõ `/` sẽ thấy 3 lệnh `nlm-soan-cau`, `nlm-go-de`, `nhap-kho`.
   - Bản Antigravity cũ không hiện lệnh `/`? Đổi tên thư mục `.agents` thành `.agent` (bản cũ dùng tên này).

> Gói `notebooklm-mcp-cli` là công cụ **không chính thức** (Google chưa có API NotebookLM cho tài khoản cá nhân), nó dùng cookie đăng nhập của thầy.
> Khi Google đổi giao diện có thể hỏng vài ngày → chạy lại file `.command` để cập nhật; trong lúc chờ dùng chế độ thủ công (mục 5).

## 2. Tổ chức notebook

Mỗi khối một notebook, tên khớp `notebooklm/so_tay_notebook.json`: **NH Toán 10 KNTT**, **NH Toán 11 KNTT**, **NH Toán 12 KNTT**, **NH Toán 9 – Vào 10 TP.HCM**.
- Nguồn: SGK **tách theo bài** (PDF mỗi bài một file, tên rõ "Toán 10 – Bài 9 Tích vectơ với một số") — NotebookLM trích chính xác hơn file cả quyển.
- Đề cũ: đặt tên "Đề GHK1 Toán 11 – <trường> – 2025". Đề scan → để NotebookLM tự OCR, hoặc đổi sang PDF có chữ trước.
- Notebook miễn phí giới hạn số nguồn; hết chỗ thì tách notebook theo học kì ("NH Toán 10 KNTT – HK1").
- Lần đầu chạy lệnh, Antigravity tự điền `id` notebook vào sổ tay.

## 3. Dùng hằng ngày (gõ trong khung Agent của Antigravity)

| Việc | Gõ |
|---|---|
| Soạn câu mới theo bài | `/nlm-soan-cau Toán 10 Bài 9 Tích vectơ với một số — 8 TN, 4 ĐS, 6 TLN, ưu tiên thực tế` |
| Bổ sung dạng đang ít câu | `/nlm-soan-cau Toán 11 chương 3 — chỉ các dạng dưới 15 câu, mỗi dạng 4 câu` |
| Gõ lại đề có trong notebook | `/nlm-go-de notebook "NH Toán 11 KNTT" nguồn "Đề GHK1 Toán 11 – Trần Phú – 2025"` |
| Xuất JSON thay vì LaTeX | thêm `xuất json` vào cuối lệnh |
| Nhập vào kho | `/nhap-kho` (Antigravity hỏi thầy trước khi nhập thật và trước khi push) |

Kết quả nằm ở `ai-nhap/`; câu trả lời gốc của NotebookLM ở `ai-nhap/tho/` để đối chiếu nguồn.
Mỗi câu nhập vào kho mang dòng `% nguon: …` nên sau này biết câu lấy từ đâu.

## 4. Hai công cụ mới trong `scripts/`

- `kiem_tra_ai.py <file>` — kiểm tra **chặt** (lỗi là chặn): mã dạng có trong danh mục, đúng 1 `\True`, ĐS đủ 4 `\itemch` khớp Đúng/Sai,
  TLN ≤ 4 ký tự và dấu phẩy, có lời giải, không "Chọn A", ngoặc `{}` và `$` cân, không sót Markdown, trùng kho / trùng trong lô.
  `--json` cho máy đọc; `--cho-phep-chua-ma` khi gõ đề có câu `%[?]`.
- `tra_dang.py "<từ khoá>"` hoặc `--tien-to 0H5?3 [--it 20]` — tra mã dạng + số câu đang có (không cần gõ dấu).

## 5. Chế độ thủ công (khi MCP chưa cài được hoặc tạm hỏng)

1. Mở notebook trên notebooklm.google.com, chép **MẪU 1** hoặc **MẪU 2** trong `notebooklm/mau_hoi_notebooklm.md`, điền `<…>`, gửi.
2. Chép khối ```json NotebookLM trả về, lưu thành `ai-nhap/tho/<tên>.json`.
3. Trong Antigravity gõ: `Xử lý ai-nhap/tho/<tên>.json theo bước 4–7 của /nlm-soan-cau` — phần bộ não chạy y như cũ.
   (Không có Antigravity: `python3 scripts/nhap_cau.py ai-nhap/tho/<tên>.json --ma-dang 0H5?3-2 --thu` vẫn nhập được, nhưng không có bước tự giải lại.)
