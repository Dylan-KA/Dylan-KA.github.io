#!/usr/bin/env bash
# Renders resume/resume.html to Resume.pdf at the repo root using headless Chrome.
# Usage: ./resume/build-pdf.sh   (or: npm run resume)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
INPUT="$SCRIPT_DIR/resume.html"
OUTPUT="$REPO_ROOT/Resume.pdf"

find_chrome() {
    if [[ -n "${CHROME:-}" ]]; then echo "$CHROME"; return; fi
    local candidates=(
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        "/Applications/Chromium.app/Contents/MacOS/Chromium"
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
    )
    for c in "${candidates[@]}"; do
        [[ -x "$c" ]] && { echo "$c"; return; }
    done
    for c in google-chrome google-chrome-stable chromium chromium-browser; do
        command -v "$c" >/dev/null 2>&1 && { command -v "$c"; return; }
    done
    echo "Chrome not found. Set CHROME=/path/to/chrome and retry." >&2
    exit 1
}

CHROME_BIN="$(find_chrome)"
TMP_DIR="$(mktemp -d)"
TMP_PDF="$TMP_DIR/Resume.pdf"
trap 'rm -rf "$TMP_DIR"' EXIT

"$CHROME_BIN" \
    --headless \
    --disable-gpu \
    --no-pdf-header-footer \
    --virtual-time-budget=5000 \
    --print-to-pdf="$TMP_PDF" \
    "file://$INPUT" >/dev/null 2>&1

if [[ ! -s "$TMP_PDF" ]]; then
    echo "PDF generation failed." >&2
    exit 1
fi

PAGES="$(grep -a -o "/Count [0-9]*" "$TMP_PDF" | head -1 | cut -d" " -f2 || true)"
mv "$TMP_PDF" "$OUTPUT"
echo "Wrote $OUTPUT (${PAGES} page(s))"
if [[ "$PAGES" != "1" ]]; then
    echo "Warning: resume is not 1 page. Shorten text or reduce spacing." >&2
fi
