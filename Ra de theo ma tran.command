#!/bin/bash
# Dự phòng: nhấp đúp file này (mở Terminal) nếu file .app bị macOS chặn.
cd "$(dirname "$0")" || exit 1
export PATH="/Library/TeX/texbin:/usr/local/bin:/opt/homebrew/bin:$PATH"
python3 scripts/ung_dung.py
