#!/bin/bash
# ======================================================================
#  CÀI ĐẶT NGÂN HÀNG CÂU HỎI TOÁN (thầy Vũ Tiến Lực) TRÊN MÁY MAC MỚI
#  Nhấp đúp file này (nếu macOS chặn: chuột phải → Mở). Chạy lại bao nhiêu lần cũng được.
#  Đặt file sao lưu SaoLuu_NganHang_*.zip (tạo trong ứng dụng: Ngân hàng → Sao lưu & chuyển máy)
#  CẠNH file này: máy tự chép khoá AI, bí mật thi trực tuyến, thư mục đề đã xuất;
#  không vào được GitHub thì lấy cả kho từ file zip.
# ======================================================================
URL="https://github.com/VuTienLuc/NganHangToanTHPT.git"
DICH="$HOME/NganHangCaNhan"          # để ngoài iCloud cho git chạy ổn định
NGUON="$(cd "$(dirname "$0")" && pwd)"
export PATH="/Library/TeX/texbin:/opt/homebrew/bin:/usr/local/bin:$PATH"
ZIP="$(ls -t "$NGUON"/SaoLuu_NganHang_*.zip 2>/dev/null | head -1)"
TAM="$(mktemp -d /tmp/nh_saoluu.XXXX)"
dung() { echo; read -n 1 -s -r -p "Bấm phím bất kì để đóng…"; echo; exit "${1:-0}"; }

echo
echo " === BƯỚC 1/4: Kiểm tra phần mềm cần thiết ==="
if ! xcode-select -p >/dev/null 2>&1; then
  echo " - Máy chưa có công cụ dòng lệnh của Apple (git, python3). Đang mở cửa sổ cài đặt…"
  xcode-select --install 2>/dev/null
  echo
  echo " ============================================================"
  echo "  Bấm 'Cài đặt' trong cửa sổ vừa hiện, đợi xong (5–15 phút)"
  echo "  rồi NHẤP ĐÚP LẠI file cài đặt này."
  echo " ============================================================"
  dung
fi
echo " - git: $(git --version 2>/dev/null)"
echo " - python3: $(python3 --version 2>/dev/null)"
if command -v pdflatex >/dev/null 2>&1; then
  echo " - LaTeX: đã có"
else
  echo " - LaTeX (pdflatex) CHƯA có — cần để xuất PDF."
  if command -v brew >/dev/null 2>&1; then
    read -r -p "   Cài MacTeX bằng Homebrew bây giờ (khoảng 5 GB, máy hỏi mật khẩu)? [c/K] " tl
    [[ "$tl" =~ ^[cCyY] ]] && brew install --cask mactex-no-gui
  else
    echo "   Đang mở trang tải MacTeX: tải file MacTeX.pkg, cài xong mở lại ứng dụng là xuất được PDF."
    open "https://www.tug.org/mactex/mactex-download.html"
  fi
  echo "   (Ứng dụng vẫn dùng được khi chưa có LaTeX: chọn câu, xuất Word, prompt AI…)"
fi

echo
echo " === BƯỚC 2/4: Tải ngân hàng ==="
if [ -n "$ZIP" ]; then
  echo " - Thấy bản sao lưu: $(basename "$ZIP")"
  ditto -x -k "$ZIP" "$TAM" 2>/dev/null || unzip -q -o "$ZIP" -d "$TAM" || echo "   ⚠ Không giải nén được file sao lưu."
fi
git config --global user.name >/dev/null 2>&1 || { read -r -p "   Tên hiển thị khi lưu lên GitHub (vd Vu Tien Luc): " T; git config --global user.name "$T"; }
git config --global user.email >/dev/null 2>&1 || { read -r -p "   Email tài khoản GitHub: " M; git config --global user.email "$M"; }
if [ -d "$DICH/.git" ]; then
  echo " - Đã có ngân hàng ở $DICH — đang cập nhật…"
  git -C "$DICH" pull --ff-only || echo "   ⚠ Chưa cập nhật được (mạng / đăng nhập) — dùng bản đang có."
else
  echo " - Đang tải về $DICH"
  echo "   (Nếu hỏi Username: gõ VuTienLuc · Password: dán mã Personal access token của GitHub)"
  if ! git clone "$URL" "$DICH"; then
    if [ -f "$TAM/kho.bundle" ]; then
      echo " - Không vào được GitHub: lấy kho từ bản sao lưu (kho.bundle)…"
      git clone "$TAM/kho.bundle" "$DICH" && git -C "$DICH" remote set-url origin "$URL"
    else
      echo " [!] Chưa tải được. Kiểm tra mạng / đăng nhập GitHub rồi chạy lại file này"
      echo "     (hoặc đặt file SaoLuu_NganHang_*.zip cạnh file này để lấy kho từ bản sao lưu)."
      dung 1
    fi
  fi
fi

echo
echo " === BƯỚC 3/4: Chép khoá AI, bí mật thi trực tuyến, thư mục đề ==="
mkdir -p "$DICH/thi-truc-tuyen"
chep() {   # $1 tên file   $2 đích
  if [ -f "$2" ]; then echo " - $1: đã có, giữ nguyên"; return; fi
  for s in "$NGUON/bi_mat/$1" "$TAM/bi_mat/$1"; do
    if [ -f "$s" ]; then cp "$s" "$2"; echo " - $1: đã chép"; return; fi
  done
  echo " - $1: không có trong bản sao lưu (bỏ qua)"
}
chep ai_khoa.json "$DICH/ai_khoa.json"
chep bi_mat.json "$DICH/thi-truc-tuyen/bi_mat.json"
chep mat_khau_dau.json "$DICH/thi-truc-tuyen/mat_khau_dau.json"
if [ -d "$TAM/de-da-ra" ]; then
  echo " - Chép lại thư mục đề đã xuất (không ghi đè file đã có)…"
  mkdir -p "$DICH/de-da-ra"
  rsync -a --ignore-existing "$TAM/de-da-ra/" "$DICH/de-da-ra/" 2>/dev/null || cp -Rn "$TAM/de-da-ra/." "$DICH/de-da-ra/"
fi
rm -rf "$TAM"

echo
echo " === BƯỚC 4/4: Tạo lối tắt ==="
APP="$DICH/Ra de theo ma tran.app"
xattr -dr com.apple.quarantine "$APP" 2>/dev/null
chmod +x "$APP/Contents/MacOS/"* "$DICH/"*.command 2>/dev/null
if [ ! -e "$HOME/Desktop/Ra de theo ma tran" ]; then
  ln -s "$APP" "$HOME/Desktop/Ra de theo ma tran" && echo " - Desktop có lối tắt \"Ra de theo ma tran\""
fi
echo
echo " ============================================================"
echo "  XONG! Mở ứng dụng bằng lối tắt \"Ra de theo ma tran\" trên Desktop."
echo "  Lần đầu ứng dụng lập chỉ mục ~30.000 câu, mất khoảng 1 phút."
echo " ============================================================"
open "$APP"
dung
