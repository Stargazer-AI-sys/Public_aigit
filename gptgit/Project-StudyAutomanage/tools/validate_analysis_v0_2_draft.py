"""Local draft validation; never calls an API or fetches a citation URL.

Run from the project root with a Python environment containing jsonschema.
Schema checks shape. The additional checks verify local links and source text,
not technical truth, citation support, or whether a comment is useful.
"""
import copy
import hashlib
import json
import re
import unicodedata
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / 'output/study_material_analysis_schema_v0.2_draft.json'
EXAMPLE = ROOT / 'output/examples/18_day_analysis_v0.2_draft.json'
SOURCE = ROOT / 'test_file/18일차.txt'
REPORT = ROOT / 'output/v0.2_draft_validation_report.json'


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def pointer(document, path):
    value = document
    for key in path.split('/')[1:]:
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def validate(data, schema, source):
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = [f"schema:/{'/'.join(map(str, e.absolute_path))}: {e.message}"
              for e in validator.iter_errors(data)]
    if errors:
        return errors
    raw = source.read_bytes()
    text = raw.decode('utf-8-sig').replace('\r\n', '\n').replace('\r', '\n')
    if data['source']['material_id'].lower() != hashlib.sha256(raw).hexdigest():
        errors.append('source: SHA-256 does not match source bytes')
    if data['source']['filename'] != source.name or data['source']['extension'] != source.suffix:
        errors.append('source: filename/extension mismatch')
    names = [c['name'] for c in data.get('concepts', [])]
    normalized = [re.sub(r'\s+', '', unicodedata.normalize('NFKC', n)).casefold() for n in names]
    if len(normalized) != len(set(normalized)):
        errors.append('concepts: duplicate names')
    for relation in data.get('relationships', []):
        if relation['from'] not in names or relation['to'] not in names:
            errors.append('relationships: missing concept')

    def visit(value):
        if isinstance(value, dict):
            if 'evidence' in value and value['evidence'] not in text:
                errors.append('evidence: quote not found in source')
            if any(n not in names for n in value.get('related_concepts', [])):
                errors.append('related_concepts: missing concept')
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
        elif isinstance(value, str) and not value.strip():
            errors.append('text: whitespace-only string')
    visit(data)
    if len(re.findall(r'[.!?。！？]+(?=\s|$)', data['summary'])) > 1:
        errors.append('summary: more than one sentence')
    sections = data['sections']
    references = data.get('references', [])
    for label, objects in [('sections', sections), ('references', references)]:
        ids = [item['id'] for item in objects]
        if len(ids) != len(set(ids)):
            errors.append(f'{label}: duplicate ids')
    reference_by_id = {r['id']: r for r in references}
    used = set()
    for section in sections:
        for ref in section['content_refs']:
            try:
                pointer(data, ref)
            except (KeyError, IndexError, ValueError, TypeError):
                errors.append(f"sections/{section['id']}: unresolved content pointer {ref}")
        comment = section.get('comment')
        if comment is None:
            continue
        if len(re.findall(r'[.!?。！？]+(?=\s|$)', comment['text'])) > 1:
            errors.append(f"sections/{section['id']}: comment has more than one sentence")
        for ref_id in comment['reference_ids']:
            used.add(ref_id)
            ref = reference_by_id.get(ref_id)
            if ref is None:
                errors.append(f'comment: missing reference {ref_id}')
            elif ref['verification_status'] != 'source_checked':
                errors.append(f'comment: reference {ref_id} is not source_checked; keep in review')
    if set(reference_by_id) - used:
        errors.append('references: unused references in final display example')
    return errors


def main():
    schema, example = read_json(SCHEMA), read_json(EXAMPLE)
    Draft202012Validator.check_schema(schema)
    baseline = validate(example, schema, SOURCE)
    cases = []

    def check(name, data, expected_valid):
        errors = validate(data, schema, SOURCE)
        cases.append({'case': name, 'expected_valid': expected_valid,
                      'actual_valid': not errors, 'pass': (not errors) == expected_valid,
                      'errors': errors})

    check('normal_18_day_example', example, True)
    data = copy.deepcopy(example)
    for section in data['sections']:
        section.pop('comment', None)
    data.pop('references', None)
    check('no_comments_is_valid', data, True)

    def invalid(name, mutate):
        data = copy.deepcopy(example)
        mutate(data)
        check(name, data, False)

    invalid('wrong_schema_version', lambda d: d.update(schema_version='0.1'))
    invalid('unknown_material_type', lambda d: d['material_type'].update(material_type='unknown'))
    invalid('long_summary', lambda d: d.update(summary='x' * 121))
    invalid('two_sentence_summary', lambda d: d.update(summary='첫 문장입니다. 두 번째입니다.'))
    invalid('no_analysis_content', lambda d: d.update(sections=[]))
    invalid('broken_section_pointer', lambda d: d['sections'][0].update(content_refs=['/practice/999']))
    invalid('duplicate_section_ids', lambda d: d['sections'][1].update(id=d['sections'][0]['id']))
    invalid('duplicate_reference_ids', lambda d: d['references'].append(copy.deepcopy(d['references'][0])))
    invalid('two_comments_in_a_section', lambda d: d['sections'][-1].update(comment=[d['sections'][-1]['comment']] * 2))
    invalid('missing_comment_reference', lambda d: d['sections'][-1]['comment'].update(reference_ids=['missing']))
    invalid('no_comment_source', lambda d: d['sections'][-1]['comment'].update(reference_ids=[]))
    invalid('unverified_comment_source', lambda d: d['references'][0].update(verification_status='unverified'))
    invalid('checked_source_without_date', lambda d: d['references'][0].pop('checked_on'))
    invalid('invalid_check_date', lambda d: d['references'][0].update(checked_on='2026-02-30'))
    invalid('invalid_source_url', lambda d: d['references'][0].update(url='not-a-url'))
    invalid('multiline_comment', lambda d: d['sections'][-1]['comment'].update(text='첫 줄\n다음 줄'))
    invalid('two_sentence_comment', lambda d: d['sections'][-1]['comment'].update(text='첫 문장입니다. 두 번째입니다.'))
    invalid('wrong_original_hash', lambda d: d['source'].update(material_id='0' * 64))
    invalid('invented_quote', lambda d: d['practice'][0].update(evidence='원문에 없는 인용입니다.'))
    invalid('broken_concept_link', lambda d: d['relationships'][0].update(to='없는 개념'))
    invalid('duplicate_concept_name', lambda d: d['concepts'][1].update(name=d['concepts'][0]['name']))

    original = read_json(ROOT / 'archive/analysis_samples/analysis(2).json')
    quotes_before = [x['evidence'] for x in original['practice']] + [x['evidence'] for x in original['theory']['definitions']]
    quotes_after = [x['evidence'] for x in example['practice']] + [x['evidence'] for x in example['theory']['definitions']]
    preservation = quotes_before == quotes_after and original['source'] == example['source']
    coverage = {ref for section in example['sections'] for ref in section['content_refs']}
    expected = {f'/{kind}/{i}' for kind in ('concepts', 'relationships', 'practice')
                for i in range(len(example.get(kind, [])))}
    expected.update(f'/theory/{kind}/{i}' for kind, items in example.get('theory', {}).items()
                    for i in range(len(items)))
    report = {
        'schema': str(SCHEMA.relative_to(ROOT)), 'example': str(EXAMPLE.relative_to(ROOT)),
        'actual_ai_call': False, 'schema_self_check': 'PASS',
        'example_validation': 'PASS' if not baseline else 'FAIL', 'example_errors': baseline,
        'source_and_seven_quotes_unchanged': preservation,
        'example_section_content_coverage': expected <= coverage,
        'section_count': len(example['sections']),
        'comment_count': sum('comment' in s for s in example['sections']),
        'passed_cases': sum(c['pass'] for c in cases), 'total_cases': len(cases),
        'checks': cases,
        'limitations': [
            'Draft has not been integrated into the v0.5 Analyzer or API response schema.',
            'Technical accuracy, usefulness, single-topic grouping, and citation support require content review.',
            'source_checked is a recorded review result, not proof supplied by schema validation.',
            'The cited Cisco CLI page was read during this conversation; this validator makes no web requests.',
            'Sentence punctuation checks are heuristic; no new fixed character limit for comments was specified.',
            'Content references use document-local JSON Pointers; reordering arrays requires updating references.',
        ],
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    ok = not baseline and preservation and expected <= coverage and all(c['pass'] for c in cases)
    print(f"Schema: PASS; example: {report['example_validation']}; cases: {report['passed_cases']}/{len(cases)}")
    print(f"Sections: {report['section_count']}; comments: {report['comment_count']}; source/quotes preserved: {preservation}")
    print('Report: output/v0.2_draft_validation_report.json')
    raise SystemExit(0 if ok else 1)


if __name__ == '__main__':
    main()
