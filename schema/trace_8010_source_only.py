#!/usr/bin/env python3
import os
import re
import time
import subprocess
from pathlib import Path

ROOT = Path("/Users/wesleyshu/ep_system")
OUT = Path("/Users/wesleyshu/ep_system/ep_api_system/trace_8010_source_only_" + time.strftime("%Y%m%d_%H%M%S") + ".log")

TEXT_SUFFIXES = {".py", ".sh", ".service", ".yaml", ".yml", ".plist", ".conf", ".ini"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", "venv", ".venv", "dist", "build"}
SKIP_SUFFIXES = {".log", ".json", ".md", ".txt", ".png", ".jpg", ".jpeg", ".webp", ".pdf"}

PATTERNS = {
    "PORT_8010": [r"8010"],
    "AUTH": [
        r"Authorization",
        r"Bearer",
        r"client_registry",
        r"require_auth",
        r"auth_token",
        r"verify.*token",
        r"token.*verify",
        r"authenticate",
        r"check_auth"
    ],
    "FRAMEWORK": [
        r"FastAPI\(",
        r"APIRouter",
        r"uvicorn",
        r"@app\.get",
        r"@app\.post",
        r"@router\.get",
        r"@router\.post",
        r"add_api_route"
    ],
    "ROUTES": [
        r"/v1/ep/health",
        r"/v1/ep/respond",
        r"/v1/ep/analyze",
        r"/v1/ep/providers"
    ]
}

def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr

def rel(path):
    try:
        return str(path.relative_to(ROOT))
    except Exception:
        return str(path)

def should_skip(path):
    parts = set(path.parts)
    if parts & SKIP_DIRS:
        return True
    if path.suffix.lower() in SKIP_SUFFIXES:
        return True
    return False

def read_text(path):
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""

def find_matches(path):
    text = read_text(path)
    if not text:
        return None
    lines = text.splitlines()
    hits = {}
    score = 0
    for group, regs in PATTERNS.items():
        group_hits = []
        for i, line in enumerate(lines, start=1):
            for reg in regs:
                if re.search(reg, line):
                    group_hits.append((i, line[:240]))
                    break
        if group_hits:
            hits[group] = group_hits[:20]
            score += len(group_hits) * (3 if group == "ROUTES" else 2 if group == "AUTH" else 1)
    if not hits:
        return None
    return score, hits

def main():
    out = []
    out.append("=== TRACE 8010 SOURCE ONLY ===")
    out.append("TIME=" + time.strftime("%Y-%m-%d %H:%M:%S"))
    out.append("ROOT=" + str(ROOT))
    out.append("")

    code, stdout, stderr = run(["/usr/sbin/lsof", "-nP", "-iTCP:8010", "-sTCP:LISTEN"])
    out.append("=== LSOF 8010 ===")
    out.append(stdout.strip() or stderr.strip() or "NO_LISTENER_FOUND")
    out.append("")

    pid = None
    rows = [r for r in stdout.splitlines() if r.strip()]
    if len(rows) >= 2:
        cols = rows[1].split()
        if len(cols) >= 2 and cols[1].isdigit():
            pid = cols[1]

    out.append("=== PS 8010 COMMAND ===")
    if pid:
        code, stdout, stderr = run(["/bin/ps", "-p", pid, "-o", "pid=,ppid=,command="])
        out.append(stdout.strip() or stderr.strip() or "PS_EMPTY")
    else:
        out.append("PID_NOT_FOUND")
    out.append("")

    candidates = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if should_skip(path):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        found = find_matches(path)
        if found:
            score, hits = found
            candidates.append((score, path, hits))

    candidates.sort(key=lambda x: (-x[0], str(x[1])))

    out.append("=== TOP CANDIDATE FILES ===")
    for score, path, hits in candidates[:30]:
        out.append("")
        out.append("FILE=" + rel(path))
        out.append("SCORE=" + str(score))
        for group in ["PORT_8010", "FRAMEWORK", "AUTH", "ROUTES"]:
            if group in hits:
                out.append("[" + group + "]")
                for lineno, line in hits[group][:8]:
                    out.append(str(lineno) + ": " + line)
    out.append("")

    out.append("=== ROUTE DECLARATION FILES ===")
    for score, path, hits in candidates:
        if "ROUTES" in hits:
            out.append(rel(path))
    out.append("")

    out.append("=== AUTH FILES ===")
    for score, path, hits in candidates:
        if "AUTH" in hits:
            out.append(rel(path))
    out.append("")

    out.append("=== PORT 8010 FILES ===")
    for score, path, hits in candidates:
        if "PORT_8010" in hits:
            out.append(rel(path))
    out.append("")

    OUT.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("REPORT=" + str(OUT))

if __name__ == "__main__":
    main()
