#!/bin/bash
set -euo pipefail

/usr/bin/python3 - <<'PY'
import pathlib
import re
import sys

root = pathlib.Path("/Users/wesleyshu/ep_system/ep_api_system")
skip_parts = {".venv", ".git", "__pycache__", "node_modules"}
skip_file_suffixes = (".bak",)
skip_file_contains = (".bak.",)
skip_dir_prefixes = ("_backup_", ".backup_")
han = re.compile(r"[\u4e00-\u9fff]")

bad = []
for path in root.rglob("*"):
    if any(part in skip_parts for part in path.parts):
        continue
    if any(part.startswith(skip_dir_prefixes) for part in path.parts):
        continue
    if not path.is_file():
        continue
    if path.name.endswith(skip_file_suffixes) or any(token in path.name for token in skip_file_contains):
        continue
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    for lineno, line in enumerate(text.splitlines(), 1):
        if han.search(line):
            bad.append((str(path), lineno, line[:240]))

if bad:
    print("FAIL: Chinese characters found")
    for path, lineno, line in bad:
        print(f"{path}:{lineno}: {line}")
    sys.exit(1)

print("PASS: English-only project state confirmed")
PY
