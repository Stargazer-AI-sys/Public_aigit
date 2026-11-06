"""Read-only checks for project artifact structure and local Markdown links."""
from pathlib import Path
import re
import sys
from urllib.parse import unquote

root = Path(__file__).resolve().parents[1]
required = ['README.md', 'AGENTS.md', 'CLAUDE.md', 'docs/requirements.md',
            'docs/development-plan.md', 'docs/workflow.md', 'docs/runtime.md',
            'docs/context-and-agents.md', 'docs/tool-inventory.md',
            'docs/records/work_log.md', 'wiki/index.md', 'tools/start_role.ps1',
            'tools/dispatch_task.py', 'tools/task_packet.py', 'tools/workflow.py']
errors = [f'missing {p}' for p in required if not (root / p).is_file()]
count = 0
for file in root.rglob('*.md'):
    if '.local' in file.parts:
        continue
    content = re.sub(r'```.*?```', '', file.read_text(encoding='utf-8-sig'), flags=re.S)
    for target in re.findall(r'\]\(([^)]+)\)', content):
        if '://' in target or target.startswith('#'):
            continue
        relative = unquote(target.split('#')[0].strip('<>'))
        if relative:
            count += 1
            if not (file.parent / relative).exists():
                errors.append(f'{file.relative_to(root)}: broken {relative}')
for error in errors:
    print(error)
print(f'required={len(required)} local_links={count} errors={len(errors)}')
sys.exit(bool(errors))
