"""Read-only checks of explicitly named wiki knowledge pages."""
import argparse
import datetime as dt
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml

FIELDS = {"type", "tags", "created", "updated", "confidence", "source_status", "status", "sources"}
ENUMS = {"type": {"concept", "architecture", "decision", "operation"},
         "confidence": {"unknown", "low", "medium", "high"},
         "source_status": {"unreviewed", "reviewed", "verified"},
         "status": {"current", "historical", "superseded", "draft", "unknown"}}
LINK = re.compile(r"!?\[[^\]\n]*\]\((<[^>\n]+>|[^\s()]+)\)")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")


class UniqueLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise yaml.YAMLError(f"duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", help="pages relative to project root (current directory)")
    args = parser.parse_args()
    root = Path.cwd().resolve()
    errors = []

    def error(file, message):
        errors.append(f"{file}: {message}")

    def path_check(file, target, kind):
        target = target.strip("<>")
        parsed = urlsplit(target)
        if parsed.scheme in ("http", "https") and parsed.netloc:
            return
        if parsed.scheme or parsed.netloc or target.startswith(("/", "\\")):
            error(file, f"{kind}: unsupported absolute or URL path: {target}")
            return
        if not parsed.path:
            if kind == "source":
                error(file, f"source requires a file path or URL: {target}")
            return
        resolved = (file.parent / unquote(parsed.path)).resolve()
        if not resolved.is_relative_to(root):
            error(file, f"{kind}: path outside project root: {target}")
        elif not resolved.is_file():
            error(file, f"{kind}: file not found: {target}")

    for name in args.files:
        file = (root / name).resolve()
        if not file.is_relative_to(root):
            error(name, "file outside project root")
            continue
        try:
            content = file.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as exc:
            error(name, f"cannot read file: {exc}")
            continue
        match = re.match(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", content, re.S)
        if not match:
            error(name, "missing or incomplete YAML frontmatter")
            continue
        try:
            data = yaml.load(match.group(1), Loader=UniqueLoader)
        except (yaml.YAMLError, ValueError, TypeError) as exc:
            error(name, f"invalid YAML: {exc}")
            continue
        if not isinstance(data, dict):
            error(name, "frontmatter must be a mapping")
            continue
        for key in sorted(FIELDS - data.keys()):
            error(name, f"missing field: {key}")
        for key, allowed in ENUMS.items():
            if key in data and (not isinstance(data[key], str) or data[key] not in allowed):
                error(name, f"invalid {key}: {data[key]!r}")
        dates = {}
        for key in ("created", "updated"):
            if key in data:
                value = data[key]
                try:
                    dates[key] = dt.date.fromisoformat(str(value))
                    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(value)):
                        raise ValueError()
                except ValueError:
                    error(name, f"invalid {key} date: {value!r}")
        if len(dates) == 2 and dates['updated'] < dates['created']:
            error(name, "updated precedes created")
        for key in ("tags", "sources"):
            if key in data and (not isinstance(data[key], list) or
                                any(not isinstance(item, str) or not item.strip() for item in data[key])):
                error(name, f"{key} must be a list of nonempty strings")
        if isinstance(data.get("sources"), list):
            if not data["sources"] and (data.get("confidence") != "unknown" or
                                       data.get("source_status") != "unreviewed" or
                                       data.get("status") not in ("unknown", "draft")):
                error(name, "empty sources require unknown confidence, unreviewed source_status and unknown or draft status")
            for source in data["sources"]:
                if isinstance(source, str) and source.strip():
                    if "[[" in source or "]]" in source:
                        error(name, f"unsupported wikilink in sources: {source}")
                    else:
                        path_check(file, source, "source")
        body = content[match.end():]
        fenced = False
        marker = ""
        diagram = False
        for line in body.splitlines():
            fence = FENCE.match(line)
            if fence:
                token, suffix = fence.groups()
                if not fenced:
                    fenced, marker = True, token
                    if suffix.strip().lower() == "mermaid":
                        diagram = True
                elif token[0] == marker[0] and len(token) >= len(marker) and not suffix.strip():
                    fenced = False
                continue
            if fenced:
                continue
            prose = re.sub(r"(`+).*?\1", "", line)
            if re.search(r"\[\[.*?\]\]", prose):
                error(name, "unsupported wikilink")
            for link in LINK.finditer(prose):
                path_check(file, link.group(1), "link")
        if data.get("type") == "architecture" and not diagram:
            error(name, "architecture requires a Mermaid block")
        if fenced:
            error(name, "unclosed code fence")
        if not re.search(r"(?m)^#\s+\S", body):
            error(name, "missing H1 heading")
    for item in errors:
        print("ERROR", item)
    print(f"Checked {len(args.files)} explicit file(s); {len(errors)} error(s).")
    print("Excluded: anchors, external URL access, reference/complex links, Mermaid rendering, diagram accuracy, orphans, conflicts, facts and freshness.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
