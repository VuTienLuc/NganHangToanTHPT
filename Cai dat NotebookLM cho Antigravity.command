#!/bin/bash
# Cài NotebookLM MCP (gói notebooklm-mcp-cli) và nối vào Antigravity cho thư mục NganHangCaNhan.
# Nhấp đúp file này (lần đầu: nhấp phải → Mở). Chạy lại bất cứ lúc nào để cập nhật / đăng nhập lại.
cd "$(dirname "$0")" || exit 1
KHO="$(pwd)"
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

echo "== 1/5 Kiểm tra uv (trình cài gói Python) =="
if ! command -v uv >/dev/null 2>&1; then
  echo "Chưa có uv → cài…"
  curl -LsSf https://astral.sh/uv/install.sh | sh || { echo "Cài uv lỗi. Thử: brew install uv"; read -r -p "Enter để đóng"; exit 1; }
  export PATH="$HOME/.local/bin:$PATH"
fi
uv --version

echo; echo "== 2/5 Cài / cập nhật notebooklm-mcp-cli =="
uv tool install --upgrade notebooklm-mcp-cli || uv tool upgrade notebooklm-mcp-cli
BIN="$(command -v notebooklm-mcp || echo "$HOME/.local/bin/notebooklm-mcp")"
NLM="$(command -v nlm || echo "$HOME/.local/bin/nlm")"
echo "MCP server: $BIN"

echo; echo "== 3/5 Đăng nhập Google cho NotebookLM =="
if "$NLM" login --check >/dev/null 2>&1; then
  echo "Đã đăng nhập sẵn."
else
  echo "Trình duyệt sẽ mở — đăng nhập đúng tài khoản Google có các notebook của thầy."
  "$NLM" login
fi

echo; echo "== 4/5 Ghi cấu hình MCP cho Antigravity =="
python3 - "$BIN" "$KHO" <<'PY'
import json, os, sys, shutil, time
bin_, kho = sys.argv[1], sys.argv[2]
muc = {"command": bin_, "args": [], "env": {"NOTEBOOKLM_QUERY_TIMEOUT": "300"}}
dich = [os.path.join(kho, ".agents", "mcp_config.json"),                       # riêng thư mục kho
        os.path.expanduser("~/.gemini/config/mcp_config.json")]                # chung (Antigravity mới)
cu = os.path.expanduser("~/.gemini/antigravity/mcp_config.json")               # Antigravity bản cũ
if os.path.isdir(os.path.dirname(cu)):
    dich.append(cu)
for p in dich:
    os.makedirs(os.path.dirname(p), exist_ok=True)
    data = {}
    if os.path.exists(p):
        shutil.copy(p, p + ".bak-" + time.strftime("%Y%m%d%H%M%S"))
        try:
            data = json.load(open(p, encoding="utf-8")) or {}
        except Exception:
            data = {}
    data.setdefault("mcpServers", {})["notebooklm-mcp"] = muc
    json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("  ✓", p)
PY
# cấu hình riêng máy, không đưa lên GitHub
grep -qx ".agents/mcp_config.json" .gitignore 2>/dev/null || printf '\n# cấu hình MCP riêng máy\n.agents/mcp_config.json\n' >> .gitignore

echo; echo "== 5/5 Thử đọc danh sách notebook =="
"$NLM" notebook list || echo "Chưa đọc được — chạy lại file này để đăng nhập lại."

echo
echo "XONG. Mở Antigravity → File → Open Folder → chọn thư mục NganHangCaNhan."
echo "Trong khung Agent: … → MCP Servers → kiểm tra 'notebooklm-mcp' có đèn xanh."
echo "Rồi gõ: /nlm-soan-cau Toán 10 Bài 9 — 8 TN, 4 ĐS, 6 TLN"
read -r -p "Enter để đóng"
