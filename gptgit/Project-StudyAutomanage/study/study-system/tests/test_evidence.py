import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import test_openai as fixtures
from analyzer.core import AnalysisError,analyze
from analyzer.evidence import numbered_source,resolve_reference,restore_legacy_quote
from analyzer.recheck import recheck_run
from analyzer.openai_provider import OpenAIProvider

class EvidenceTests(unittest.TestCase):
    def test_crlf_blank_lines_and_end_of_file(self):
        source='처음\r\n\r\n\t중간  \r\n마지막'
        self.assertEqual(numbered_source(source),'[L1] 처음\n[L2] \n[L3] \t중간  \n[L4] 마지막')
        self.assertEqual(resolve_reference({'start_line':1,'end_line':3},source),'처음\r\n\r\n\t중간  ')
        self.assertEqual(resolve_reference({'start_line':4,'end_line':4},source),'마지막')
    def test_invalid_ranges_and_empty_quotes(self):
        for ref in [{'start_line':0,'end_line':1},{'start_line':2,'end_line':1},{'start_line':1,'end_line':4},{'start_line':True,'end_line':1},{'start_line':1.0,'end_line':1},{'start_line':1},{'start_line':2,'end_line':2},{'start_line':1,'end_line':1,'extra':1}]:
            with self.assertRaises(AnalysisError):resolve_reference(ref,'첫줄\n\n마지막')
    def test_old_omitted_lines_restored_and_auditable(self):
        restored=restore_legacy_quote('첫 구절\n끝 구절','첫 구절\n생략되었던 관찰\n끝 구절')
        self.assertEqual(restored[0],'첫 구절\n생략되었던 관찰\n끝 구절')
        self.assertEqual(restored[1]['end_line'],3)
    def test_ambiguity_reorder_and_paraphrase_never_repaired(self):
        for quote,source in [('같은줄\n끝','같은줄\n같은줄\n끝'),('끝\n처음','처음\n중간\n끝'),('고친 문장\n끝','다른 문장\n끝'),('없는 구절','처음\n끝')]:
            self.assertIsNone(restore_legacy_quote(quote,source))
    def test_reference_schema_request_and_exact_reconstruction(self):
        fixture=fixtures.APITests();fixture.setUp();requests=[]
        def transport(request,**kwargs):requests.append(json.loads(request.data));return fixtures.Response(fixture.body)
        provider=OpenAIProvider(fixture.schema,api_key='test-key',transport=transport)
        result,audit=analyze(fixture.data,provider,fixture.schema)
        self.assertEqual(result['status'],'SUCCESS')
        material=json.loads(requests[0]['input'][1]['content'].split('[MATERIAL]\n')[1])
        self.assertIn('[L1] ',material['content'])
        self.assertIn('evidence_resolution',audit)
        self.assertTrue(all(x['method']=='source_line_reference' for x in audit['evidence_resolution']))
        self.assertFalse(audit['trace']['actual_ai_call'])
    def test_invalid_model_reference_rejected_without_retry(self):
        fixture=fixtures.APITests();fixture.setUp();calls=[]
        fixture.wire['theory']['definitions'][0]['evidence']={'start_line':9999,'end_line':9999}
        fixture.body['output'][0]['content'][0]['text']=json.dumps(fixture.wire)
        def transport(*a,**k):calls.append(1);return fixtures.Response(fixture.body)
        result,_=analyze(fixture.data,OpenAIProvider(fixture.schema,api_key='test-key',transport=transport),fixture.schema)
        self.assertEqual(result['error']['code'],'EVIDENCE_REFERENCE_ERROR');self.assertEqual(len(calls),1)
    def test_old_raw_string_rejected_in_new_api_contract(self):
        fixture=fixtures.APITests();fixture.setUp()
        fixture.wire['theory']['definitions'][0]['evidence']='원문'
        fixture.body['output'][0]['content'][0]['text']=json.dumps(fixture.wire)
        result,_=analyze(fixture.data,OpenAIProvider(fixture.schema,api_key='test-key',transport=lambda *a,**k:fixtures.Response(fixture.body)),fixture.schema)
        self.assertEqual(result['error']['code'],'SCHEMA_VALIDATION_ERROR')
    def test_offline_recheck_legacy_and_new_format(self):
        fixture=fixtures.APITests();fixture.setUp()
        for raw in [json.dumps(fixture.analysis),json.dumps(fixture.wire)]:
            with tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp)
                (path/'analyzer_input.json').write_text(json.dumps(fixture.data))
                (path/'raw_response.json').write_text(json.dumps(raw))
                original={p.name:p.read_bytes() for p in path.iterdir()}
                with patch('analyzer.openai_provider.urllib.request.build_opener',side_effect=AssertionError('no transport')):
                    _,result,audit=recheck_run(path,fixture.schema)
                self.assertEqual(result['status'],'SUCCESS')
                self.assertFalse(audit['trace']['api_request_attempted'])
                self.assertEqual(audit['trace']['usage']['total_tokens'],0)
                self.assertEqual(original,{p.name:p.read_bytes() for p in path.iterdir()})
    def test_offline_ambiguity_stays_failed(self):
        fixture=fixtures.APITests();fixture.setUp()
        fixture.analysis['theory']['definitions'][0]['evidence']='없는 인용\n다른 인용'
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)
            (path/'analyzer_input.json').write_text(json.dumps(fixture.data))
            (path/'raw_response.json').write_text(json.dumps(json.dumps(fixture.analysis)))
            _,result,audit=recheck_run(path,fixture.schema)
            self.assertEqual(result['error']['code'],'QUALITY_VALIDATION_ERROR')
            self.assertNotIn('evidence_resolution',audit)
