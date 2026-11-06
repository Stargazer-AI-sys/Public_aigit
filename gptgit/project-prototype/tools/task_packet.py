"""Read-only task packet validation; does not approve, dispatch, or run a model."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path, PureWindowsPath

ROLES = {"master", "planner", "planning-reviewer", "developer", "qa", "documenter"}
PROVIDERS = {"master": "codex", "planner": "codex", "qa": "codex", "planning-reviewer": "claude", "developer": "claude", "documenter": "hermes"}
REQUIRED = {"task_id", "role", "goal", "work_spec", "development_plan", "acceptance", "inputs", "write_scope", "constraints", "expected_output", "session"}


def confined(root: Path, value: object, *, existing: bool = False) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("path must be a nonempty relative string")
    normalized = value.replace("\\", "/")
    parts = normalized.split("/")
    if PureWindowsPath(value).drive or normalized.startswith("/") or any(p in {"", ".", ".."} for p in parts):
        raise ValueError(f"unsafe relative path: {value}")
    if any(re.search(r'[<>:"|?*\x00-\x1f]', p) for p in parts):
        raise ValueError(f"unsupported path syntax: {value}")
    destination = root.joinpath(*parts).resolve()
    if not destination.is_relative_to(root):
        raise ValueError(f"path escapes project, including link/junction: {value}")
    if existing and not destination.is_file():
        raise ValueError(f"input is not an existing file: {value}")
    return destination


def validate(packet: object, root: Path) -> list[str]:
    """Return errors without changing any files. Success is not authorization."""
    errors: list[str] = []
    root = root.resolve()
    if not root.is_dir():
        return ["project root must be an existing directory"]
    if not isinstance(packet, dict):
        return ["packet must be an object"]
    missing = REQUIRED - packet.keys()
    if missing:
        return ["missing fields: " + ", ".join(sorted(missing))]
    role = packet["role"]
    if not isinstance(role, str) or role not in ROLES:
        errors.append("unsupported role")
        return errors
    if packet.get("template_only"):
        errors.append("template must be completed and template_only removed before use")
    if not isinstance(packet["task_id"], str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}", packet["task_id"]):
        errors.append("task_id must be a stable 1-80 character identifier")
    for key in ("goal", "expected_output"):
        if not isinstance(packet[key], str) or not packet[key].strip():
            errors.append(f"{key} must be nonempty")
    for key in ("acceptance", "constraints"):
        if not isinstance(packet[key], list) or not packet[key] or not all(isinstance(x, str) and x.strip() for x in packet[key]):
            errors.append(f"{key} must contain nonempty strings")
    session = packet["session"]
    if not isinstance(session, dict) or "actual_id" not in session or "provider" not in session:
        errors.append("session needs provider and actual_id (null until observed)")
    elif (session["actual_id"] is not None and (not isinstance(session["actual_id"], str) or not session["actual_id"].strip())) or not isinstance(session["provider"], str) or not session["provider"].strip():
        errors.append("invalid session identity")
    elif session["provider"] != PROVIDERS[role]:
        errors.append(f"{role} must use provider {PROVIDERS[role]}")
    source_paths: set[Path] = set()
    for key in ("work_spec", "development_plan"):
        if key == "development_plan" and packet[key] is None and role in {"master", "planner"}:
            continue
        try:
            source = confined(root, packet[key], existing=True)
            if "records" in source.relative_to(root).parts or source.name.lower() in {"management_log.md", "work_log.md", "timeline.md"}:
                raise ValueError("history cannot replace a work specification or development plan")
            source_paths.add(source)
        except ValueError as exc:
            errors.append(f"{key}: {exc}")
    inputs = packet["inputs"]
    if not isinstance(inputs, list) or not inputs:
        errors.append("inputs must be a nonempty list of explicit files")
    else:
        for item in inputs:
            if not isinstance(item, dict) or "path" not in item or not isinstance(item.get("reason"), str) or not item["reason"].strip():
                errors.append("each input needs path and reason")
                continue
            try:
                path = confined(root, item["path"], existing=True)
                source_paths.add(path)
                relative = path.relative_to(root).as_posix().lower()
                lines = item.get("lines")
                valid_lines = isinstance(lines, list) and len(lines) == 2 and all(type(x) is int for x in lines) and 1 <= lines[0] <= lines[1]
                if lines is not None and not valid_lines:
                    raise ValueError("lines must be [positive start, inclusive end]")
                if ("records" in relative.split("/") or path.name.lower() in {"management_log.md", "work_log.md", "timeline.md"}) and not valid_lines:
                    raise ValueError("history input requires a selected line range; whole history is prohibited")
                if valid_lines:
                    length = len(path.read_text(encoding="utf-8-sig").splitlines())
                    if lines[1] > length:
                        raise ValueError("input line range exceeds file length")
            except (ValueError, OSError, UnicodeError) as exc:
                errors.append(f"input: {exc}")
    writes = packet["write_scope"]
    if not isinstance(writes, list):
        errors.append("write_scope must be a list")
    else:
        if role in {"planning-reviewer", "qa"} and writes:
            errors.append("review/QA returns findings; source writes are not allowed")
        for value in writes:
            try:
                path = confined(root, value)
                if path.exists() and path.is_dir():
                    raise ValueError("write scope must name files, not directories")
                if role == "documenter":
                    parts = path.relative_to(root).parts
                    if len(parts) < 5 or parts[0:2] != ("docs", "workflows") or parts[3] != "drafts":
                        raise ValueError("documenter may write only docs/workflows/<run>/drafts/<file>")
                    if path in source_paths:
                        raise ValueError("documenter must not overwrite an input")
            except ValueError as exc:
                errors.append(f"write_scope: {exc}")
    test_writes = packet.get("test_write_scope", [])
    if not isinstance(test_writes, list):
        errors.append("test_write_scope must be a list")
    else:
        if test_writes and role != "qa":
            errors.append("only QA may declare test_write_scope")
        for value in test_writes:
            try:
                path = confined(root, value)
                parts = path.relative_to(root).parts
                if len(parts) < 4 or parts[:3] != (".local", "qa", packet["task_id"]):
                    raise ValueError("QA test writes must name files under .local/qa/<task_id>/")
                if path.exists() and path.is_dir():
                    raise ValueError("test write scope must name files, not directories")
                if path in source_paths:
                    raise ValueError("QA test writes must not overwrite any input")
            except ValueError as exc:
                errors.append(f"test_write_scope: {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("--root", required=True, type=Path, help="explicit project root")
    args = parser.parse_args()
    try:
        packet_path = args.packet.resolve()
        if not packet_path.is_relative_to(args.root.resolve()):
            raise ValueError("packet must be inside project root")
        errors = validate(json.loads(packet_path.read_text(encoding="utf-8-sig")), args.root)
    except (ValueError, OSError) as exc:
        errors = [str(exc)]
    print(json.dumps({"valid": not errors, "errors": errors, "authorization": "not_evaluated", "model_called": False, "files_changed": False}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
