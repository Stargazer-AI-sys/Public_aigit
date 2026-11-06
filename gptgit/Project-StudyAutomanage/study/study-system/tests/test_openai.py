import copy,io,json,os,unittest,urllib.error
from pathlib import Path
from unittest.mock import patch
from jsonschema import Draft202012Validator
from analyzer.core import analyze,from_collector,load_schema
from analyzer.openai_provider import OpenAIProvider,response_schema
from collector.main import process_file
ROOT=Path(__file__).resolve().parent.parent
class Response:
    headers={'x-request-id':'req_test'}
    def __init__(self,body):self.body=body
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self):return json.dumps(self.body).encode()
class APITests(unittest.TestCase):
    def setUp(self):
        self.schema=load_schema(ROOT/'output/study_material_analysis_schema_v0.1.json')
        self.data=from_collector(process_file(ROOT.parent/'sourcefile/12일차.docx'))
        self.analysis=json.loads((ROOT/'fixtures/12_day_mock_response.json').read_text())
        def fill(value,node):
            if '$ref' in node:node=self.schema['$defs'][node['$ref'].rsplit('/',1)[1]]
            if isinstance(value,dict):return {k:fill(value[k],child) if k in value else None for k,child in node.get('properties',{}).items() if k!='source'}
            if isinstance(value,list):return [fill(x,node.get('items',{})) for x in value]
            return value
        from analyzer.evidence import resolve_reference
        def evidence_refs(value):
            if isinstance(value,dict):
                for key,child in value.items():
                    if key=='evidence':
                        text=self.data['extracted_text'];pos=text.index(child)
                        ref={'start_line':text[:pos].count('\n')+1,'end_line':text[:pos+len(child)-1].count('\n')+1}
                        value[key]=resolve_reference(ref,text)
                    else:evidence_refs(child)
            elif isinstance(value,list):
                for child in value:evidence_refs(child)
        evidence_refs(self.analysis)
        self.wire=fill(self.analysis,self.schema)
        def wire_refs(value):
            if isinstance(value,dict):
                for key,child in value.items():
                    if key=='evidence':
                        text=self.data['extracted_text'];pos=text.index(child)
                        value[key]={'start_line':text[:pos].count('\n')+1,'end_line':text[:pos+len(child)-1].count('\n')+1}
                    else:wire_refs(child)
            elif isinstance(value,list):
                for child in value:wire_refs(child)
        wire_refs(self.wire)
        self.body={'id':'resp_test','status':'completed','model':'gpt-6-luna','usage':{'input_tokens':100,'output_tokens':200,'total_tokens':300,'output_tokens_details':{'reasoning_tokens':50}},'output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(self.wire)}]}]}
    def test_wire_roundtrip_and_request(self):
        original=copy.deepcopy(self.schema);sent=[]
        def transport(req,timeout):sent.append((req,timeout));return Response(self.body)
        p=OpenAIProvider(self.schema,api_key='test-private-key',transport=transport)
        Draft202012Validator.check_schema(p.transport_schema);Draft202012Validator(p.transport_schema).validate(self.wire)
        result,audit=analyze(self.data,p,self.schema)
        self.assertEqual(result['status'],'SUCCESS');self.assertEqual({k:v for k,v in result['analysis'].items() if k!='source'},self.analysis)
        self.assertEqual(self.schema,original)
        payload=json.loads(sent[0][0].data)
        self.assertEqual(payload['model'],'gpt-6-luna');self.assertFalse(payload['store']);self.assertEqual(payload['max_output_tokens'],6000)
        self.assertEqual(payload['service_tier'],'default');self.assertEqual(sent[0][0].full_url,'https://api.openai.com/v1/responses');self.assertEqual(len(sent),1)
        self.assertEqual(audit['trace']['usage']['output_tokens'],200);self.assertFalse(audit['trace']['actual_ai_call'])
        self.assertNotIn('test-private-key',json.dumps(audit));self.assertNotIn('Authorization',json.dumps(audit))
    def test_null_conversion(self):
        self.wire['topics']=[{'name':'Routing','children':None}];self.wire['practice']=None
        p=OpenAIProvider(self.schema,api_key='test-key',transport=lambda *a,**k:Response(self.body))
        self.body['output'][0]['content'][0]['text']=json.dumps(self.wire)
        result,_=analyze(self.data,p,self.schema)
        self.assertEqual(result['status'],'SUCCESS');self.assertNotIn('practice',result['analysis']);self.assertNotIn('children',result['analysis']['topics'][0])
        self.wire['summary']=None;self.body['output'][0]['content'][0]['text']=json.dumps(self.wire)
        result,_=analyze(self.data,p,self.schema);self.assertEqual(result['error']['code'],'SCHEMA_VALIDATION_ERROR')
    def test_refusal_incomplete_empty(self):
        for status,content in [('incomplete',[]),('completed',[{'type':'refusal','refusal':'test'}]),('completed',[])]:
            body=dict(self.body,status=status,output=[{'type':'message','content':content}])
            p=OpenAIProvider(self.schema,api_key='test-key',transport=lambda *a,**k:Response(body))
            result,audit=analyze(self.data,p,self.schema);self.assertEqual(result['error']['code'],'AI_CALL_ERROR');self.assertIsNotNone(audit['trace']['usage'])
    def test_http_timeout_no_retry_and_no_secret(self):
        for error in [urllib.error.HTTPError('https://api.openai.com',401,'secret-test-key',{},io.BytesIO(b'secret-test-key')),TimeoutError('secret-test-key')]:
            calls=[]
            def transport(*a,**k):calls.append(1);raise error
            p=OpenAIProvider(self.schema,api_key='secret-test-key',transport=transport)
            result,audit=analyze(self.data,p,self.schema);self.assertEqual(result['error']['code'],'AI_CALL_ERROR');self.assertEqual(len(calls),1)
            self.assertNotIn('secret-test-key',json.dumps([result,audit]))
    def test_missing_key_and_invalid_input(self):
        with patch.dict(os.environ,{},clear=True):
            p=OpenAIProvider(self.schema,transport=lambda *a,**k:self.fail('must not send'))
            result,audit=analyze(self.data,p,self.schema);self.assertEqual(result['error']['code'],'AI_CALL_ERROR');self.assertFalse(audit['trace']['api_request_attempted'])
            result,_=analyze(dict(self.data,material_id='bad'),p,self.schema);self.assertEqual(result['error']['code'],'SOURCE_METADATA_ERROR')
    def test_all_fields_required(self):
        wire=response_schema(self.schema)
        def visit(node):
            if isinstance(node,dict):
                if node.get('type')=='object':self.assertEqual(set(node['required']),set(node['properties']))
                self.assertNotIn('minProperties',node)
                for value in node.values():visit(value)
            elif isinstance(node,list):
                for value in node:visit(value)
        visit(wire);self.assertNotIn('source',wire['properties'])
