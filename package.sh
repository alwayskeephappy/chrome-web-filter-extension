#!/usr/bin/env bash
set -euo pipefail

OUTPUT="chrome-web-filter-extension.zip"
rm -f "$OUTPUT"

if command -v zip >/dev/null 2>&1; then
  zip -r "$OUTPUT" manifest.json background.js icons
else
  python3 - <<'PY'
import zipfile
from pathlib import Path

output = "chrome-web-filter-extension.zip"
files = [Path("manifest.json"), Path("background.js")]
files.extend(sorted(path for path in Path("icons").glob("*") if path.is_file()))

with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for file_path in files:
        zf.write(file_path, arcname=file_path.as_posix())
PY
fi

echo "Created: $OUTPUT"
