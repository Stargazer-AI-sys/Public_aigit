"""Best-effort PreToolUse guard, not a security boundary.

Inspects shell/Bash/exec_command tool inputs (also MCP names with those suffixes),
command/cmd strings or argv lists, and literal shell -c/-Command wrappers.
Variables, aliases, scripts, encodings, dynamically constructed commands, other
MCP tools, unsupported shell grammar, herdr raw cmd forwarding and unhooked launches can bypass it.
Hook errors and missing context fail open. The approved project launcher must
validate policy itself; this guard does not validate a running session's model.
"""
import json
import ntpath

from pathlib import Path
import re
import shlex
import sys
from check_agent_model import validate

ROOT = Path(__file__).resolve().parent.parent
# Only these project trees and common directories are in scope.
SCOPE = {"project-management", "project-prototype", "tools", "tests", "skills", "docs"}

TOOLS = {"shell", "bash", "exec_command"}


def in_scope(cwd):
    if not isinstance(cwd, str) or not cwd:
        return False
    try:
        rel = Path(cwd).resolve().relative_to(ROOT)
        return not rel.parts or rel.parts[0].lower() in SCOPE
    except (OSError, ValueError):
        return False


def executable(token):
    name = ntpath.basename(token.strip("'\" ")).lower()
    return re.sub(r"\.(exe|cmd|bat|ps1)$", "", name)


def tokenize(command):
    # posix=False preserves Windows path separators. This is not a shell parser.
    lexer = shlex.shlex(command, posix=False, punctuation_chars=";&|\n")
    lexer.whitespace_split = True
    lexer.commenters = ""
    return [t.strip("'\"") for t in lexer]


def inspect_tokens(tokens):
    if not tokens:
        return None
    # Literal shell wrappers only. Do not scan arbitrary arguments as commands.
    name = executable(tokens[0])
    if name in {"bash", "sh", "zsh", "pwsh", "powershell", "cmd"}:
        for i, arg in enumerate(tokens[1:], 1):
            if arg.lower() in {"-c", "-command", "/c"} and i + 1 < len(tokens):
                return inspect_command(tokens[i + 1])
        return None
    if name == "codex":
        args = [x.lower() for x in tokens[1:]]
        if args in (["--help"], ["-h"], ["features"], ["features", "list"], ["login", "status"]):
            return None
        return "Direct codex launch is ambiguous; use the approved project launcher."
    if name == "herdr" and len(tokens) >= 4 and [x.lower() for x in tokens[1:3]] == ["agent", "start"]:
        args = tokens[3:]
        split = args.index("--") if "--" in args else len(args)
        options, native = args[:split], args[split + 1:]
        kinds = []
        for i, arg in enumerate(options):
            if arg == "--kind":
                kinds.append(options[i + 1] if i + 1 < len(options) else "")
            elif arg.startswith("--kind="):
                kinds.append(arg.partition("=")[2])
        if "codex" not in kinds:
            return None
        if kinds != ["codex"]:
            return "Ambiguous herdr agent kind."
        models = []
        for i, arg in enumerate(native):
            if arg == "--model":
                models.append(native[i + 1] if i + 1 < len(native) else "")
            elif arg.startswith("--model=") or arg == "-m" or arg.startswith("-m=") or (arg.startswith("-m") and len(arg) > 2):
                return "Use exactly one explicit --model MODEL; model aliases are not accepted."
            elif arg in ("-c", "--config"):
                if i + 1 >= len(native) or re.match(r"\s*model(?:\s*[.=]|\s*$)", native[i + 1], re.I):
                    return "Model configuration override is not allowed."
            elif arg.startswith("--config=") or (arg.startswith("-c") and len(arg) > 2):
                config = arg.partition("=")[2] if arg.startswith("--config=") else arg[2:].lstrip("=")
                if re.match(r"\s*model(?:\s*[.=]|\s*$)", config, re.I):
                    return "Model configuration override is not allowed."
        if len(models) != 1 or validate("worker", "codex", models[0]):
            return "herdr Codex workers require exactly one allowed --model MODEL."
    return None


def inspect_command(command):
    if isinstance(command, list):
        if not all(isinstance(x, str) for x in command):
            return None
        return inspect_tokens(command)
    if not isinstance(command, str):
        return None
    tokens = tokenize(command)
    segment = []
    for token in tokens + [";"]:
        if token and all(c in ";&|\n" for c in token):
            decision = inspect_tokens(segment)
            if decision:
                return decision
            segment = []
        else:
            segment.append(token)
    return None


def evaluate(data):
    if not isinstance(data, dict) or data.get("hook_event_name") != "PreToolUse":
        return None
    if not in_scope(data.get("cwd")):
        return None
    name = data.get("tool_name", "")
    if not isinstance(name, str) or name.lower().split("__")[-1] not in TOOLS:
        return None
    tool_input = data.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    for key in ("command", "cmd"):
        if key in tool_input:
            reason = inspect_command(tool_input[key])
            if reason:
                return reason
    return None


def main():
    try:
        reason = evaluate(json.load(sys.stdin))
        if reason:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}}))
    except Exception as exc:
        print("agent_model_hook: " + str(exc), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())


