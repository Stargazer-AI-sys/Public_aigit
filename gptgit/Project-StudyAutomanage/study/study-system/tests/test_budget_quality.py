import copy
import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from analyzer.budget import Budget,estimate_usage,reservation
from analyzer.core import AnalysisError,analyze
from analyzer.quality import quality_errors
from analyzer.openai_provider import OpenAIProvider
import test_openai as fixtures

class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'budget.sqlite3'
        self.budget=Budget(self.path)
    def test_persistent_hundred_attempts_unknown_usage(self):
        for _ in range(100):
            ticket=self.budget.reserve('gpt-6-luna',1000000)
            self.budget.finish(ticket,'gpt-6-luna',None)
        restored=Budget(self.path)
        self.assertEqual(restored.status()['call_limit'],100)
        self.assertEqual(restored.status()['budget_usd'],2)
        self.assertEqual(restored.status()['calls_used'],100)
        self.assertEqual(restored.status()['estimated_or_reserved_usd'],.1)
        with self.assertRaises(AnalysisError) as caught:restored.reserve('gpt-6-luna',1)
        self.assertEqual(caught.exception.code,'BUDGET_LIMIT_ERROR')
        self.assertIn('100회 또는 $2',str(caught.exception))
    def test_existing_policy_and_history_are_not_automatically_reset(self):
        ticket=self.budget.reserve('gpt-6-luna',1000000)
        self.budget.finish(ticket,'gpt-6-luna',None)
        db=self.budget.connect()
        try:db.execute('UPDATE policy SET max_calls=5,max_nano=1000000000 WHERE id=1')
        finally:db.close()
        restored=Budget(self.path).status()
        self.assertEqual(restored['call_limit'],5)
        self.assertEqual(restored['budget_usd'],1)
        self.assertEqual(restored['calls_used'],1)
        self.assertEqual(restored['estimated_or_reserved_usd'],.001)
    def test_dollar_guard_before_attempt(self):
        self.budget.reserve('gpt-6-luna',1900000000)
        with self.assertRaises(AnalysisError):self.budget.reserve('gpt-6-luna',100000001)
        self.assertEqual(self.budget.status()['calls_used'],1)
    def test_concurrent_reservations(self):
        def attempt(_):
            try:Budget(self.path).reserve('gpt-6-luna',1000);return True
            except AnalysisError:return False
        self.budget.status()
        with ThreadPoolExecutor(max_workers=8) as pool:outcomes=list(pool.map(attempt,range(108)))
        self.assertEqual(sum(outcomes),100)
        self.assertEqual(self.budget.status()['calls_used'],100)
    def test_corrupt_ledger_blocks(self):
        self.path.write_bytes(b'not a sqlite database')
        with self.assertRaises(AnalysisError) as caught:self.budget.reserve('gpt-6-luna',10)
        self.assertEqual(caught.exception.code,'BUDGET_STORAGE_ERROR')
    def test_usage_pricing_no_reasoning_double_count(self):
        usage={'input_tokens':1000,'output_tokens':200,'input_tokens_details':{'cached_tokens':100,'cache_write_tokens':200},'output_tokens_details':{'reasoning_tokens':50}}
        self.assertEqual(estimate_usage('gpt-6-luna',usage),196000)
        self.assertIsNone(estimate_usage('gpt-6-luna',{'input_tokens':True,'output_tokens':1}))
        self.assertIsNone(estimate_usage('gpt-6-luna',{'input_tokens':10,'output_tokens':1,'input_tokens_details':{'cached_tokens':11}}))
        self.assertGreater(reservation('gpt-6-luna',10000,6000),estimate_usage('gpt-6-luna',{'input_tokens':10000,'output_tokens':6000}))
    def test_usage_replaces_reservation(self):
        ticket=self.budget.reserve('gpt-6-luna',10000000)
        self.budget.finish(ticket,'gpt-6-luna',{'input_tokens':1000,'output_tokens':200})
        self.assertEqual(self.budget.status()['calls_used'],1)
        self.assertEqual(self.budget.status()['estimated_or_reserved_usd'],.0002)
    def test_provider_timeout_counted_and_blocked_before_transport(self):
        fixture=fixtures.APITests();fixture.setUp();calls=[]
        def transport(*a,**k):calls.append(1);raise TimeoutError()
        for _ in range(101):
            provider=OpenAIProvider(fixture.schema,api_key='test-key',transport=transport,budget=self.budget)
            result,audit=analyze(fixture.data,provider,fixture.schema)
        self.assertEqual(len(calls),100)
        self.assertEqual(result['error']['code'],'BUDGET_LIMIT_ERROR')
        self.assertFalse(audit['trace']['api_request_attempted'])
        self.assertEqual(self.budget.status()['calls_used'],100)
    def test_cache_reuse_free_and_force_counted(self):
        from analyzer.cache import run_with_cache
        fixture=fixtures.APITests();fixture.setUp();calls=[]
        def transport(*a,**k):calls.append(1);return fixtures.Response(fixture.body)
        def provider():return OpenAIProvider(fixture.schema,api_key='test-key',transport=transport,budget=self.budget)
        cache=Path(self.tmp.name)/'cache';history=Path(self.tmp.name)/'history'
        first,_=run_with_cache(fixture.data,provider(),fixture.schema,cache,history)
        second,audit=run_with_cache(fixture.data,provider(),fixture.schema,cache,history)
        self.assertEqual(first,second);self.assertTrue(audit['trace']['result_reused'])
        self.assertEqual(self.budget.status()['calls_used'],1)
        forced,_=run_with_cache(fixture.data,provider(),fixture.schema,cache,history,force=True)
        self.assertEqual(forced['status'],'SUCCESS');self.assertEqual(len(calls),2)
        self.assertEqual(self.budget.status()['calls_used'],2)
    def test_success_is_accounted_even_if_quality_fails(self):
        fixture=fixtures.APITests();fixture.setUp()
        fixture.wire['summary']='가'*121
        fixture.body['output'][0]['content'][0]['text']=json.dumps(fixture.wire)
        provider=OpenAIProvider(fixture.schema,api_key='test-key',transport=lambda *a,**k:fixtures.Response(fixture.body),budget=self.budget)
        result,audit=analyze(fixture.data,provider,fixture.schema)
        self.assertEqual(result['error']['code'],'QUALITY_VALIDATION_ERROR')
        self.assertEqual(self.budget.status()['calls_used'],1)
        self.assertEqual(audit['trace']['budget']['calls_used'],1)

class QualityTests(unittest.TestCase):
    def setUp(self):
        fixture=fixtures.APITests();fixture.setUp()
        self.analysis=fixture.analysis;self.text=fixture.data['extracted_text']
    def test_valid_fixture(self):self.assertEqual(quality_errors(self.analysis,self.text),[])
    def test_summary_boundary_type_and_duplicate(self):
        self.analysis['summary']='가'*120
        self.assertEqual(quality_errors(self.analysis,self.text),[])
        self.analysis['summary']='가'*121
        self.analysis['material_type']['material_type']='긴 자유 분류명'
        self.analysis['concepts'].append(copy.deepcopy(self.analysis['concepts'][0]))
        paths={x['path'] for x in quality_errors(self.analysis,self.text)}
        self.assertTrue({'/summary','/material_type/material_type','/concepts'}<=paths)
    def test_reference_and_literal_evidence(self):
        self.analysis['relationships'][0]['from']='없는 개념'
        self.analysis['theory']['definitions'][0]['evidence']='원문에 없는 인용'
        errors=quality_errors(self.analysis,self.text)
        self.assertTrue(any(x['path'].endswith('/from') for x in errors))
        self.assertTrue(any(x['path'].endswith('/evidence') for x in errors))
    def test_recovered_luna_response_passes(self):
        from analyzer.core import FileResponseProvider
        fixture=fixtures.APITests();fixture.setUp()
        path=Path(__file__).resolve().parent.parent/'fixtures/12_day_luna_recovered_response.json'
        result,audit=analyze(fixture.data,FileResponseProvider(path),fixture.schema)
        self.assertEqual(result['status'],'SUCCESS')
        self.assertFalse(audit['trace']['actual_ai_call'])
    def test_joined_source_lines_rejected(self):
        self.analysis['theory']['definitions'][0]['evidence']='IGP 하나의 AS에서..\nEGP 서로 다른 AS에서...'
        self.assertTrue(any(x['path'].endswith('/evidence') for x in quality_errors(self.analysis,self.text)))
    def test_multisentence_rejected(self):
        self.analysis['summary']='첫 문장입니다. 둘째 문장입니다.'
        self.assertTrue(quality_errors(self.analysis,self.text))
