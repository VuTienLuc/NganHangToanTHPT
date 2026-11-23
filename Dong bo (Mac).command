#!/bin/bash
# ĐỒNG BỘ NGÂN HÀNG LÊN GITHUB (máy Mac) — nhấp đúp. Giống "Dong bo (Windows).bat":
# lưu câu hỏi / dữ liệu mới → lấy thay đổi từ máy khác → đẩy lên GitHub. Không đụng file bí mật, không đụng de-da-ra.
cd "$(dirname "$0")" || exit 1
dung() { echo; read -n 1 -s -r -p "Bấm phím bất kì để đóng…"; echo; exit "${1:-0}"; }
command -v git >/dev/null || { echo " [!] Máy chưa có git — chạy \"Cai dat tren Mac.command\" trước."; dung 1; }
echo " === Đồng bộ ngân hàng ==="
git add -- cau-hoi cau-hoi-ts10 du-lieu ai-nhap ma-tran notebooklm prompt-ai tai-lieu 2>/dev/null
if git diff --cached --quiet; then
  echo "   không có thay đổi mới"
else
  git commit -q -m "Cập nhật từ máy Mac $(scutil --get ComputerName 2>/dev/null || hostname)" && echo "   đã ghi nhận thay đổi"
fi
if ! git pull --no-rebase --no-edit; then
  git merge --abort >/dev/null 2>&1
  echo
  echo " [!] Hai máy cùng sửa một câu / một file nên Git chưa tự gộp được."
  echo "     Em đã huỷ lần gộp này, ngân hàng trên máy vẫn nguyên vẹn."
  echo "     Thầy nhờ trợ lý AI (Claude) xử lý giúp."
  dung 1
fi
if git push; then
  echo
  echo " ✅ Đã đồng bộ lên GitHub."
else
  echo " [!] Chưa đẩy lên được (mạng / đăng nhập GitHub). Thầy chạy lại file này sau."
fi
dung
