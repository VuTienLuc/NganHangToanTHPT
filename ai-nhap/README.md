# ai-nhap — hộp thư đến của câu hỏi do AI soạn

- `ai-nhap/*.tex | *.json` — file đã chuẩn hoá, chờ `/nhap-kho` (kiểm tra → xem trước → nhập).
- `ai-nhap/tho/` — câu trả lời nguyên văn của NotebookLM (giữ để đối chiếu nguồn).
- `ai-nhap/da-nhap/` — file đã nhập xong.

Nhập bằng tay (không cần Antigravity):
```bash
python3 scripts/kiem_tra_ai.py ai-nhap/<file>      # kiểm tra chặt
python3 scripts/nhap_cau.py ai-nhap/<file> --thu   # xem trước
python3 scripts/nhap_cau.py ai-nhap/<file>         # nhập thật
```
