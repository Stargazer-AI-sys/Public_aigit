import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from analyzer.cache import run_with_cache,context_for,digest
from analyzer.core import FileResponseProvider,from_collector,load_schema
from analyzer.openai_provider import OpenAIProvider
from collector.main import process_file
ROOT=Path(__file__).resolve().parent.parent

class CacheTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name)
  self.cache=self.base/'cache';self.history=self.base/'runs'
  self.schema=load_schema(ROOT/'output/study_material_analysis_schema_v0.1.json')
  self.data=from_collector(process_file(ROOT.parent/'sourcefile/12일차.docx'))
  self.file=self.base/'response.json';self.file.write_bytes((ROOT/'fixtures/12_day_mock_response.json').read_bytes())
  self.provider=FileResponseProvider(self.file)
 def tearDown(self):self.temp.cleanup()
 def run_cache(self,**kwargs):
  return run_with_cache(self.data,self.provider,self.schema,self.cache,self.history,**kwargs)
 def test_second_run_never_generates_and_no_usage(self):
  first,_=self.run_cache()
  with patch.object(self.provider,'generate',side_effect=AssertionError('must not call')):
   second,audit=self.run_cache()
  self.assertEqual(first,second);self.assertTrue(audit['trace']['result_reused'])
  self.assertFalse(audit['trace']['actual_ai_call']);self.assertEqual(audit['trace']['usage']['total_tokens'],0)
 def test_force_calls_again(self):
  self.run_cache()
  with patch.object(self.provider,'generate',wraps=self.provider.generate) as generate:
   result,audit=self.run_cache(force=True)
  self.assertEqual(generate.call_count,1);self.assertEqual(result['status'],'SUCCESS')
  self.assertTrue(audit['trace']['force_reanalysis'])
 def test_reuse_only_miss_never_calls(self):
  with patch.object(self.provider,'generate',side_effect=AssertionError('must not call')):
   result,audit=self.run_cache(reuse_only=True)
  self.assertEqual(result['error']['code'],'CACHE_MISS');self.assertFalse(audit['trace']['actual_ai_call'])
 def test_changes_invalidate(self):
  self.run_cache()
  for field,value in [('extracted_text','changed'),('material_id','a'*64),('filename','renamed.docx')]:
   data=dict(self.data,**{field:value})
   result,_=run_with_cache(data,self.provider,self.schema,self.cache,self.history,reuse_only=True)
   self.assertEqual(result['error']['code'],'CACHE_MISS')
  self.file.write_text('{"summary":"changed"}')
  result,_=self.run_cache(reuse_only=True);self.assertEqual(result['error']['code'],'CACHE_MISS')
 def test_schema_and_prompt_invalidate(self):
  self.run_cache();schema=copy.deepcopy(self.schema);schema['title']='changed'
  result,_=run_with_cache(self.data,self.provider,schema,self.cache,self.history,reuse_only=True)
  self.assertEqual(result['error']['code'],'CACHE_MISS')
  with patch('analyzer.cache.build_prompt',return_value=[{'role':'user','content':'different prompt'}]):
   result,_=self.run_cache(reuse_only=True)
  self.assertEqual(result['error']['code'],'CACHE_MISS')
 def test_failed_result_not_cached(self):
  self.file.write_text('invalid JSON');result,_=self.run_cache()
  self.assertEqual(result['status'],'FAILED');self.assertFalse(list(self.cache.glob('*.json')))
 def test_corruption_blocks_request(self):
  self.run_cache();file=next(self.cache.glob('*.json'));entry=json.loads(file.read_text())
  entry['analysis']['summary']='edited';file.write_text(json.dumps(entry))
  with patch.object(self.provider,'generate',side_effect=AssertionError('must not call')):
   result,_=self.run_cache()
  self.assertEqual(result['error']['code'],'CACHE_ERROR')
 def test_invalid_source_even_with_matching_integrity_rejected(self):
  self.run_cache();file=next(self.cache.glob('*.json'));entry=json.loads(file.read_text())
  entry['analysis']['source']['material_id']='a'*64;entry['analysis_sha256']=digest(entry['analysis']);file.write_text(json.dumps(entry))
  result,_=self.run_cache();self.assertEqual(result['error']['code'],'CACHE_ERROR')
 def test_lock_blocks_concurrent_force(self):
  context,_=context_for(self.data,self.provider,self.schema);self.cache.mkdir()
  (self.cache/(digest(context)+'.lock')).write_text('active')
  with patch.object(self.provider,'generate',side_effect=AssertionError('must not call')):
   result,_=self.run_cache(force=True)
  self.assertEqual(result['error']['code'],'CACHE_LOCKED')
 def test_key_timeout_excluded_output_setting_included(self):
  a=OpenAIProvider(self.schema,api_key='fake-A');b=OpenAIProvider(self.schema,api_key='fake-B',timeout=120)
  ca,_=context_for(self.data,a,self.schema);cb,_=context_for(self.data,b,self.schema);self.assertEqual(ca,cb)
  b.trace['max_output_tokens']=5000;cc,_=context_for(self.data,b,self.schema);self.assertNotEqual(ca,cc)
  b.trace['model']='different';cd,_=context_for(self.data,b,self.schema);self.assertNotEqual(cc,cd)
  self.assertNotIn('fake-A',json.dumps(ca))
 def legacy_run(self,mutate=None):
  p=OpenAIProvider(self.schema,api_key='fake-key');_,messages=context_for(self.data,p,self.schema)
  analysis=json.loads(self.file.read_text());analysis['source']={k:self.data[k] for k in ['material_id','filename','extension']}
  trace={'provider':'openai','actual_ai_call':True,'response_received':True,'response_status':'completed','completed_stages':['schema_validation'],'model':'gpt-6.1-sol','response_model':'gpt-6.1-sol','reasoning_effort':'low','max_output_tokens':6000}
  if mutate:mutate(trace)
  run=self.history/'previous';(run/'success').mkdir(parents=True)
  for rel,value in [('success/analysis.json',analysis),('success/result.json',{'status':'SUCCESS','material_id':self.data['material_id'],'analysis':analysis}),('trace.json',trace),('analyzer_input.json',self.data),('prompt.json',messages)]:
   (run/rel).write_text(json.dumps(value))
  return p
 def test_previous_sol_run_not_adopted_for_luna(self):
  p=self.legacy_run()
  with patch.object(p,'generate',side_effect=AssertionError('must not call')):
   result,audit=run_with_cache(self.data,p,self.schema,self.cache,self.history,reuse_only=True)
  self.assertEqual(result['error']['code'],'CACHE_MISS');self.assertFalse(audit['trace']['actual_ai_call'])
 def test_old_mock_or_incomplete_not_adopted(self):
  p=self.legacy_run(lambda t:t.update(actual_ai_call=False))
  with patch.object(p,'generate',side_effect=AssertionError('must not call')):
   result,_=run_with_cache(self.data,p,self.schema,self.cache,self.history,reuse_only=True)
  self.assertEqual(result['error']['code'],'CACHE_MISS')
