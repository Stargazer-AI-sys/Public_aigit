"""Build an allowlisted, source-data-free Analyzer distribution."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'study/study-system'


def build(destination):
    files = [p for folder in ('analyzer', 'collector') for p in sorted((SOURCE / folder).glob('*.py'))]
    files += [SOURCE / 'analyzer/review.html']
    files += [SOURCE / name for name in ('requirements.txt', 'launch.py', 'run_analyzer.cmd', 'smoke_check.py')]
    files += [SOURCE / 'output' / name for name in (
        'study_material_analysis_schema_v0.1.json',
        'study_material_analysis_schema_v0.2_draft.json',
        'study_material_analysis_schema_v0.2.json')]
    entries = {p.relative_to(SOURCE).as_posix(): p.read_bytes() for p in files}
    manifest = {'default_schema': '0.2', 'supported_schemas': ['0.1', '0.2-draft', '0.2'],
                'includes_source_materials': False, 'includes_credentials': False,
                'files': {name: hashlib.sha256(data).hexdigest() for name, data in entries.items()}}
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Avoid replacing an earlier release package silently.
    with ZipFile(destination, 'x', ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            archive.writestr('study-system/' + name, data)
        archive.writestr('study-system/distribution_manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    manifest = build(args.output)
    print(f"Built {args.output}: {len(manifest['files'])} files; original materials/ledgers/caches excluded")
