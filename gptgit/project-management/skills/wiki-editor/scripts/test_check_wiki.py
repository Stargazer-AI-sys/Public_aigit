"""Exercise the checker on isolated temporary pages inside the project root."""
import subprocess
import sys
import tempfile
import re
from pathlib import Path

checker = Path("skills/wiki-editor/scripts/check_wiki.py")
base = """---
type: concept
tags: [test]
created: 2026-11-05
updated: 2026-11-05
confidence: unknown
source_status: unreviewed
status: unknown
sources: [source.md]
---
# Page
[source](source.md)
```
[example](not-a-file.md)
```
"""
with tempfile.TemporaryDirectory(dir=".local", prefix="wiki-check-test-") as tmp:
    folder = Path(tmp)
    (folder / "source.md").write_text("source", encoding="utf-8")
    cases = [
        ("valid", base, 0, "0 error(s)"),
        ("missing field", base.replace("confidence: unknown\n", ""), 1, "missing field: confidence"),
        ("invalid enum", base.replace("type: concept", "type: other"), 1, "invalid type"),
        ("bad date", base.replace("2026-11-05", "'2026-99-05'", 1), 1, "invalid created date"),
        ("missing source", base.replace("sources: [source.md]", "sources: [missing.md]"), 1, "source: file not found"),
        ("missing link", base.replace("[source](source.md)", "[source](missing.md)"), 1, "link: file not found"),
        ("diagram absent", base.replace("type: concept", "type: architecture"), 1, "architecture requires"),
        ("wikilink", base + "[[source]]\n", 1, "unsupported wikilink"),
        ("outside root", base.replace("sources: [source.md]", "sources: [../../../outside.md]"), 1, "outside project root"),
        ("valid architecture", base.replace("type: concept", "type: architecture") + "```mermaid\nflowchart LR\nA-->B\n```\n", 0, "0 error(s)"),
        ("empty source conflict", base.replace("sources: [source.md]", "sources: []").replace("confidence: unknown", "confidence: high"), 1, "empty sources require"),
        ("invalid YAML date", base.replace("2026-11-05", "2026-99-05", 1), 1, "invalid YAML"),
        ("anchor source", base.replace("sources: [source.md]", "sources: ['#fragment']"), 1, "source requires"),
        ("duplicate field", base.replace("type: concept", "type: concept\ntype: decision"), 1, "duplicate YAML key"),
        ("unclosed diagram", base.replace("type: concept", "type: architecture") + "```mermaid\nflowchart LR\n", 1, "unclosed code fence"),
        ("missing heading", base.replace("# Page\n", ""), 1, "missing H1"),
    ]
    schema = Path("skills/wiki-editor/references/schema.md").read_text(encoding="utf-8")
    example = re.search(r"```yaml\n(.*?)\n```", schema, re.S)
    assert example, "schema YAML example missing"
    cases.append(("schema example", example.group(1) + "\n# Example\n", 0, "0 error(s)"))
    for index, (label, content, expected, message) in enumerate(cases):
        page = folder / f"case{index}.md"
        page.write_text(content, encoding="utf-8")
        run = subprocess.run([sys.executable, str(checker), str(page)], capture_output=True, text=True, encoding="utf-8")
        assert run.returncode == expected and message in run.stdout, (label, run.returncode, run.stdout, run.stderr)
        print(f"PASS {label}: exit {run.returncode}")
print(f"{len(cases)} cases passed")
