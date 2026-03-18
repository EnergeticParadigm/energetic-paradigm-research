
from typing import Any, Dict


def example_query_handler(payload: Dict[str, Any]) -> Dict[str, Any]:
    question = str(payload.get("question", ""))
    mode = str(payload.get("mode", "ep"))
    return {
        "answer": f"EP bridge received: {question}",
        "mode": mode,
        "metadata": {"handler": "example_query_handler", "ok": True},
    }


def example_compare_handler(payload: Dict[str, Any]) -> Dict[str, Any]:
    question = str(payload.get("question", ""))
    left_mode = str(payload.get("left_mode", "ep"))
    right_mode = str(payload.get("right_mode", "baseline"))
    return {
        "question": question,
        "results": [
            {"mode": left_mode, "answer": f"{left_mode} result for: {question}"},
            {"mode": right_mode, "answer": f"{right_mode} result for: {question}"},
        ],
        "output_format": str(payload.get("output_format", "structured_text")),
        "metadata": {"handler": "example_compare_handler", "ok": True},
    }
