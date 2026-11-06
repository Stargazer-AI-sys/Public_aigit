"""Version selection without rewriting historical results."""
from pathlib import Path

from .core import AnalysisError, load_schema, strict_json

SCHEMA_DIR = Path(__file__).resolve().parent.parent / 'output'
V02_VERSIONS = ('0.2-draft', '0.2')
SCHEMA_FILES = {
    '0.1': 'study_material_analysis_schema_v0.1.json',
    '0.2-draft': 'study_material_analysis_schema_v0.2_draft.json',
    '0.2': 'study_material_analysis_schema_v0.2.json',
}
DEFAULT_SCHEMA = SCHEMA_DIR / SCHEMA_FILES['0.2']


def version_of(analysis):
    if not isinstance(analysis, dict):
        raise AnalysisError('SCHEMA_VERSION_ERROR', '분석 결과는 JSON 객체여야 합니다.')
    version = analysis.get('schema_version', '0.1')
    if not isinstance(version, str) or version not in SCHEMA_FILES:
        raise AnalysisError('SCHEMA_VERSION_ERROR', '지원하지 않는 schema_version입니다.')
    return version


def schema_for(analysis, explicit=None):
    return load_schema(explicit or SCHEMA_DIR / SCHEMA_FILES[version_of(analysis)])


def schema_for_run(directory, explicit=None):
    if explicit:
        return load_schema(explicit)
    # raw_response.json is the saved wire response, sometimes JSON encoded twice.
    raw = strict_json((Path(directory) / 'raw_response.json').read_text(encoding='utf-8-sig'))
    try:
        result = strict_json(raw) if isinstance(raw, str) else raw
    except ValueError:
        # Let the analysis pipeline report the original JSON parsing failure.
        return load_schema(DEFAULT_SCHEMA)
    return schema_for(result)
