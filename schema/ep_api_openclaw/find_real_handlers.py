import ast
import os
from pathlib import Path

ROOT_DIR = Path("/Users/wesleyshu/ep_system")
OUTPUT_FILE = Path("/Users/wesleyshu/ep_system/ep_api_system/ep_api_openclaw/real_handler_candidates.txt")

SKIP_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "logs",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".deps_ep_api_openclaw",
}

EXCLUDED_MODULE_PREFIXES = (
    "ep_api_openclaw.example_engine_handlers",
)

NAME_TERMS = (
    "query",
    "compare",
    "answer",
    "respond",
    "response",
    "handle",
    "handler",
    "engine",
    "listen",
    "run",
    "generate",
    "process",
)

PATH_TERMS = (
    "ep",
    "engine",
    "api",
    "gateway",
    "listen",
    "response",
    "query",
    "compare",
)

def build_module_path(source_file_path: Path) -> str:
    relative_path = source_file_path.relative_to(ROOT_DIR)
    return ".".join(relative_path.with_suffix("").parts)

def build_signature_text(function_node):
    if not isinstance(function_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return "()"

    signature_parts = []

    for positional_only_arg in function_node.args.posonlyargs:
        signature_parts.append(positional_only_arg.arg)

    for positional_arg in function_node.args.args:
        signature_parts.append(positional_arg.arg)

    if function_node.args.vararg:
        signature_parts.append("*" + function_node.args.vararg.arg)

    for keyword_only_arg in function_node.args.kwonlyargs:
        signature_parts.append(keyword_only_arg.arg)

    if function_node.args.kwarg:
        signature_parts.append("**" + function_node.args.kwarg.arg)

    return "(" + ", ".join(signature_parts) + ")"

def points_for_path(path_text: str) -> int:
    total_points = 0
    lowered_path_text = path_text.lower()
    for path_term in PATH_TERMS:
        if path_term in lowered_path_text:
            total_points += 2
    return total_points

def points_for_name(name_text: str) -> int:
    total_points = 0
    lowered_name_text = name_text.lower()
    for name_term in NAME_TERMS:
        if name_term in lowered_name_text:
            total_points += 3
    return total_points

def candidate_sort_key(candidate_entry):
    return (
        -candidate_entry["points"],
        candidate_entry["callable"],
        candidate_entry["file"],
        candidate_entry["line"],
    )

candidate_list = []

for walk_root, walk_dirs, walk_files in os.walk(ROOT_DIR):
    walk_dirs[:] = [dir_name for dir_name in walk_dirs if dir_name not in SKIP_DIR_NAMES]

    for walk_file in walk_files:
        if not walk_file.endswith(".py"):
            continue

        source_file_path = Path(walk_root) / walk_file

        try:
            source_text = source_file_path.read_text(encoding="utf-8")
        except Exception:
            continue

        try:
            syntax_tree = ast.parse(source_text, filename=str(source_file_path))
        except Exception:
            continue

        module_path = build_module_path(source_file_path)
        if any(module_path.startswith(excluded_prefix) for excluded_prefix in EXCLUDED_MODULE_PREFIXES):
            continue

        path_points = points_for_path(str(source_file_path))

        for function_node in ast.walk(syntax_tree):
            if not isinstance(function_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            function_name = function_node.name
            name_points = points_for_name(function_name)
            total_points = path_points + name_points

            if total_points <= 0:
                continue

            candidate_entry = {
                "points": total_points,
                "callable": "{}:{}".format(module_path, function_name),
                "file": str(source_file_path),
                "line": function_node.lineno,
                "signature": build_signature_text(function_node),
            }
            candidate_list.append(candidate_entry)

candidate_list.sort(key=candidate_sort_key)

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT_FILE.open("w", encoding="utf-8") as output_handle:
    output_handle.write("REAL EP HANDLER CANDIDATES\\n")
    output_handle.write("=" * 80 + "\\n\\n")

    if not candidate_list:
        output_handle.write("No candidates found.\\n")
    else:
        for candidate_index, candidate_entry in enumerate(candidate_list[:120], 1):
            output_handle.write("{:03d}. points={}\\n".format(candidate_index, candidate_entry["points"]))
            output_handle.write("     callable={}\\n".format(candidate_entry["callable"]))
            output_handle.write("     file={}:{}\\n".format(candidate_entry["file"], candidate_entry["line"]))
            output_handle.write("     signature={}\\n\\n".format(candidate_entry["signature"]))

print(str(OUTPUT_FILE))
