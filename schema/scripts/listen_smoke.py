from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path("/Users/wesleyshu/ep_system/ep_api_system")
sys.path.insert(0, str(ROOT))

from core.listening_engine import build_listening_profile


CASES = [
    "ep/trigger1 what is ep",
    "Please build the listening engine into the EP API and add governance.",
    "Fix the token auth on the boundary endpoint now!",
    "Translate this article into English.",
    "Can this contract clause be enforced under Taiwan law?",
    "something about system",
]

profiles = [
    build_listening_profile(
        raw_text=case,
        client_fp="local_smoke",
        authorized=True,
        source="script",
    )
    for case in CASES
]

print(json.dumps(profiles, ensure_ascii=False, indent=2))
