from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List


TRIGGER_PREFIXES = ("ep/trigger1",)


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, round(value, 3)))


def _contains_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def _contains_arabic(text: str) -> bool:
    return bool(re.search(r"[\u0600-\u06FF]", text))


def detect_language(text: str) -> str:
    if _contains_arabic(text):
        return "ar"
    if _contains_cjk(text):
        return "zh"
    return "en"


def normalize_text(raw_text: str) -> str:
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def trigger_present(text: str) -> bool:
    lowered = text.lower().strip()
    return any(lowered.startswith(prefix) for prefix in TRIGGER_PREFIXES)


def detect_domain_type(text: str) -> str:
    lowered = text.lower()
    if any(k in lowered for k in ["ep", "energetic paradigm", "energy", "governance", "judgment", "methodology"]):
        return "ep"
    if any(k in lowered for k in ["api", "endpoint", "port", "token", "auth", "fastapi", "server", "boundary"]):
        return "api"
    if any(k in lowered for k in ["contract", "law", "legal", "complaint", "court", "regulation"]):
        return "legal"
    if any(k in lowered for k in ["write", "rewrite", "draft", "essay", "article", "poem", "translate"]):
        return "writing"
    if any(k in lowered for k in ["research", "paper", "arxiv", "experiment", "reference"]):
        return "research"
    if any(k in lowered for k in ["system", "service", "deploy", "restart", "backend", "frontend"]):
        return "system"
    return "general"


def detect_speech_act(text: str) -> str:
    lowered = text.lower().strip()
    if lowered.startswith(("please ", "start", "continue", "do ", "make ", "build ", "fix ", "write ")):
        return "requesting"
    if lowered.endswith("?") or lowered.startswith(("what ", "why ", "how ", "can ", "could ", "is ", "are ")):
        return "asking"
    if any(k in lowered for k in ["must", "should", "need to", "priority", "next step"]):
        return "directing"
    return "stating"


def score_ambiguity(text: str) -> float:
    lowered = text.lower()
    vague_terms = ["something", "somehow", "maybe", "etc", "whatever", "that thing", "kind of"]
    score = 0.10 + 0.08 * sum(1 for t in vague_terms if t in lowered)
    if len(text.split()) < 4:
        score += 0.20
    if "?" in text and len(text.split()) <= 8:
        score += 0.15
    return _clamp(score)


def score_complexity(text: str) -> float:
    words = text.split()
    long_words = sum(1 for w in words if len(w) >= 8)
    punctuation = len(re.findall(r"[,:;()/\-]", text))
    score = 0.10 + min(len(words) / 80.0, 0.45) + min(long_words / 30.0, 0.20) + min(punctuation / 30.0, 0.15)
    return _clamp(score)


def score_urgency(text: str) -> float:
    lowered = text.lower()
    urgent_terms = ["urgent", "asap", "now", "immediately", "today", "last chance", "right now"]
    score = 0.05 + 0.18 * sum(1 for t in urgent_terms if t in lowered)
    if "!" in text:
        score += 0.08
    return _clamp(score)


def score_emotional_intensity(text: str) -> float:
    exclam = text.count("!")
    all_caps_tokens = sum(1 for t in text.split() if len(t) >= 3 and t.isupper())
    score = 0.04 + min(exclam * 0.05, 0.25) + min(all_caps_tokens * 0.08, 0.24)
    return _clamp(score)


def score_decision_density(text: str) -> float:
    lowered = text.lower()
    markers = [
        "choose", "decide", "should", "need", "priority", "route", "governance",
        "risk", "strategy", "baseline", "architecture", "next step", "functional"
    ]
    score = 0.12 + 0.07 * sum(1 for t in markers if t in lowered)
    return _clamp(score)


def score_ep_compatibility(domain_type: str, text: str, decision_density: float) -> str:
    lowered = text.lower()
    if domain_type == "ep":
        return "high"
    if any(k in lowered for k in ["energy", "path", "stability", "compression", "coordination", "governance"]):
        return "high"
    if decision_density >= 0.45:
        return "medium"
    return "low"


def local_hits(text: str) -> Dict[str, int]:
    lowered = text.lower()
    hit_map = {
        "admin": ["admin", "policy", "permission", "access"],
        "writing": ["write", "rewrite", "draft", "translate", "essay", "article", "poem"],
        "legal": ["legal", "law", "court", "contract", "complaint", "regulation"],
        "research": ["research", "paper", "arxiv", "reference", "experiment", "methodology"],
        "api": ["api", "endpoint", "token", "auth", "port", "boundary", "provider", "fastapi"],
        "system": ["system", "service", "backend", "frontend", "server", "deploy", "restart"],
    }
    output: Dict[str, int] = {}
    for key, terms in hit_map.items():
        output[key] = sum(1 for term in terms if term in lowered)
    return output


def governance_blockers(text: str) -> List[str]:
    lowered = text.lower()
    flags: List[str] = []
    if len(lowered.strip()) == 0:
        flags.append("empty_input")
    if len(lowered.split()) <= 2 and not trigger_present(lowered):
        flags.append("too_short")
    if any(t in lowered for t in ["hack into", "steal password", "bypass token"]):
        flags.append("unsafe_request")
    return flags


def decide_route(
    authorized: bool,
    domain_type: str,
    speech_act: str,
    ambiguity: float,
    decision_density: float,
    ep_compatibility: str,
    hits: Dict[str, int],
    blockers: List[str],
) -> Dict[str, Any]:
    if not authorized:
        return {"mode": "auth_reject", "reason": "client_not_authorized"}
    if blockers:
        if "unsafe_request" in blockers:
            return {"mode": "safe_refusal", "reason": "governance_blocker_unsafe_request"}
        return {"mode": "clarify_or_narrow", "reason": "governance_blocker_present"}
    if ambiguity >= 0.55 and speech_act in {"asking", "requesting"}:
        return {"mode": "clarify_or_narrow", "reason": "high_ambiguity"}
    if domain_type == "ep" or ep_compatibility == "high":
        return {"mode": "ep_reasoning", "reason": "ep_trigger_or_high_ep_compatibility"}
    if domain_type == "legal":
        return {"mode": "structured_answer", "reason": "legal_domain_requires_structure"}
    if hits.get("api", 0) > 0 or hits.get("system", 0) > 0:
        if ambiguity >= 0.30 and decision_density <= 0.20:
            return {"mode": "clarify_or_narrow", "reason": "ambiguous_system_or_api_request"}
        return {"mode": "admin_tooling", "reason": "api_or_system_hits"}
    if hits.get("writing", 0) > 0:
        return {"mode": "writing_mode", "reason": "writing_hits"}
    if decision_density >= 0.50:
        return {"mode": "structured_answer", "reason": "high_decision_density"}
    return {"mode": "direct_answer", "reason": "default_route"}


def build_listening_profile(
    raw_text: str,
    client_fp: str,
    authorized: bool,
    source: str = "ep_api",
) -> Dict[str, Any]:
    normalized = normalize_text(raw_text)
    domain = detect_domain_type(normalized)
    speech_act = detect_speech_act(normalized)
    ambiguity = score_ambiguity(normalized)
    complexity = score_complexity(normalized)
    urgency = score_urgency(normalized)
    emotional_intensity = score_emotional_intensity(normalized)
    decision_density = score_decision_density(normalized)
    ep_compatibility = score_ep_compatibility(domain, normalized, decision_density)
    hits = local_hits(normalized)
    blockers = governance_blockers(normalized)
    route = decide_route(
        authorized=authorized,
        domain_type=domain,
        speech_act=speech_act,
        ambiguity=ambiguity,
        decision_density=decision_density,
        ep_compatibility=ep_compatibility,
        hits=hits,
        blockers=blockers,
    )

    return {
        "request_id": str(uuid.uuid4()),
        "authorized": authorized,
        "source": source,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "client_fp": client_fp,
        "raw_text": raw_text,
        "normalized_text": normalized,
        "trigger_present": trigger_present(normalized),
        "signals": {
            "language": detect_language(normalized),
            "ambiguity": ambiguity,
            "complexity": complexity,
            "urgency": urgency,
            "emotional_intensity": emotional_intensity,
            "decision_density": decision_density,
            "domain_type": domain,
            "speech_act": speech_act,
            "ep_compatibility": ep_compatibility,
            "local_hits": hits,
        },
        "routing": route,
        "governance": {
            "allowed": len(blockers) == 0,
            "needs_narrowing": route["mode"] == "clarify_or_narrow",
            "needs_context": ambiguity >= 0.55,
            "risk_flags": blockers,
        },
    }
