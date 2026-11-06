import copy
import json
import os
import time
import urllib.error
import urllib.request
from .core import AnalysisError


def response_schema(schema):
    result = copy.deepcopy(schema)
    result.pop('$schema', None)
    result.pop('$id', None)
    result['properties'].pop('source')
    result['required'].remove('source')
    from .knowledge import is_v02
    if is_v02(schema):
        from .comment_review import CANDIDATES
        result['properties']['review_candidates'] = copy.deepcopy(CANDIDATES)
        result['properties'].pop('references', None)
        result['$defs'].pop('external_reference', None)
    def visit(node):
        if not isinstance(node, dict):return
        node.pop('minProperties', None)
        # Strict response schemas support a subset. Canonical validation still
        # enforces these constraints after response normalization.
        for keyword in ('allOf', 'if', 'then', 'else', 'uniqueItems'):
            node.pop(keyword, None)
        if 'const' in node:
            node['enum'] = [node.pop('const')]
            if isinstance(node['enum'][0], str):node.setdefault('type', 'string')
        for definition in node.get('$defs', {}).values():visit(definition)
        if node.get('type') == 'object':
            required = set(node.get('required', []))
            for key, child in list(node.get('properties', {}).items()):
                if key == 'evidence':
                    child = {'type':'object','properties':{'start_line':{'type':'integer','minimum':1},'end_line':{'type':'integer','minimum':1}},'required':['start_line','end_line'],'additionalProperties':False}
                    node['properties'][key] = child
                visit(child)
                if key not in required:
                    node['properties'][key] = {'anyOf': [child, {'type': 'null'}]}
            node['required'] = list(node.get('properties', {}))
            node['additionalProperties'] = False
        if 'items' in node:visit(node['items'])
    visit(result)
    return result


def omit_optional_nulls(value, schema, root):
    if '$ref' in schema:schema = root['$defs'][schema['$ref'].rsplit('/', 1)[1]]
    if isinstance(value, dict):
        required = set(schema.get('required', []))
        properties = schema.get('properties', {})
        result = {}
        for key, child in value.items():
            optional = key in properties and key not in required
            if optional and child is None:
                continue
            normalized = omit_optional_nulls(child, properties.get(key, {}), root)
            # Strict API responses represent absent optional descendants as
            # null. If removing only those descendants empties an optional
            # container, omit it too. Explicit empty objects/arrays, unknown
            # fields and required containers still reach canonical validation.
            if optional and isinstance(child, dict) and child and normalized == {}:
                continue
            result[key] = normalized
        return result
    if isinstance(value, list):
        return [omit_optional_nulls(child, schema.get('items', {}), root) for child in value]
    return value


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):return None


class OpenAIProvider:
    name = 'openai'
    def __init__(self, schema, *, api_key=None, ask_api_key=False, timeout=90, max_output_tokens=6000, transport=None, model="gpt-6-luna", budget=None):
        if not 1 <= timeout <= 300 or not 256 <= max_output_tokens <= 16000:
            raise ValueError('timeout은 1~300초, max-output-tokens는 256~16000 범위입니다.')
        if model not in {'gpt-6-luna','gpt-6.1-sol'}:raise ValueError('지원하지 않는 모델입니다.')
        from .budget import Budget
        self.model=model
        self.budget=budget if budget is not None else (None if transport is not None else Budget())
        self.schema, self.transport_schema = schema, response_schema(schema)
        self.source_text = None
        self.evidence_report = []
        self.key = api_key or os.environ.get('OPENAI_API_KEY', '')
        self.ask_api_key = ask_api_key
        self.transport = transport or urllib.request.build_opener(NoRedirect()).open
        self.injected_transport = transport is not None
        self.timeout, self.max_output_tokens = timeout, max_output_tokens
        self.trace = {'evidence_mode':'source_line_ranges', 'model':self.model, 'reasoning_effort':'low', 'timeout_seconds':timeout,
                      'max_output_tokens':max_output_tokens, 'actual_ai_call':False,
                      'api_request_attempted':False, 'response_received':False, 'automatic_retries':0,
                      'usage':None, 'response_id':None, 'response_status':None}

    def prepare_messages(self, messages):
        messages = copy.deepcopy(messages)
        from .evidence import numbered_source
        material = json.loads(messages[1]['content'].split('[MATERIAL]\n',1)[1])
        self.source_text = material['content']
        material['content'] = numbered_source(self.source_text)
        messages[1]['content'] = '[MATERIAL]\n' + json.dumps(material,ensure_ascii=False)
        rules = messages[0]['content'].split('[OUTPUT RULES]', 1)[0]
        rules = '\n'.join(line for line in rules.splitlines() if not (
            line.startswith('- theory와 practice의 evidence') or line.startswith('- evidence 안의')
            or line.startswith('theory와 practice의 evidence에는')))
        rules += ('\n[EVIDENCE REFERENCES]\n원문은 [L1], [L2]처럼 줄 번호가 붙어 있습니다. 번호 표시는 원문 내용이 아닙니다.\n'
                  '모든 evidence는 인용 문자열 대신 {"start_line": 시작줄번호, "end_line": 끝줄번호} 객체로 작성하세요.\n'
                  '시작과 끝은 포함 범위이고, 중간 줄을 생략할 수 없습니다. 현재 세부 주제의 각 주장을 충분히 뒷받침하는 연속 줄 범위를 선택하세요.\n'
                  '같은 학습 목적의 관련 설정·장비별 비교·관찰 조건은 함께 인용할 수 있습니다. 길이만으로 자르지 말고, 무관한 주제가 끼면 theory/practice 항목을 나눠 각각 연속 범위를 지정하세요.\n'
                  '빈 줄만 선택하거나 줄 번호를 추측하지 마세요. 프로그램이 최종 evidence를 실제 원문에서 가져옵니다.\n')
        messages[0]['content'] = rules + (
            '[OUTPUT RULES]\nJSON 객체만 출력하세요. source·설명문·코드펜스는 금지합니다.\n'
            'API 전용 응답에서는 모든 항목을 반환하되 원문에 없는 선택 항목은 null로 반환하세요.\n'
            '빈 목록·빈 객체로 채우지 마세요. null 선택 항목은 프로그램이 최종 결과에서 생략합니다.\n'
            + json.dumps(self.transport_schema, ensure_ascii=False))
        return messages

    def normalize(self, data):
        from .core import schema_errors
        from .evidence import resolve_evidence
        from .knowledge import is_v02
        from .auxiliary import core_schema
        validation_schema = core_schema(self.transport_schema) if is_v02(self.schema) else self.transport_schema
        errors = schema_errors(data,validation_schema)
        if errors:raise AnalysisError('SCHEMA_VALIDATION_ERROR',json.dumps(errors,ensure_ascii=False))
        if self.source_text is None:raise AnalysisError('EVIDENCE_REFERENCE_ERROR','근거를 확인할 원문이 없습니다.')
        data = omit_optional_nulls(data,self.schema,self.schema)
        data,self.evidence_report = resolve_evidence(data,self.source_text)
        return data

    def generate(self, messages):
        if not self.key and self.ask_api_key:
            import getpass, sys, warnings
            if not sys.stdin.isatty():raise AnalysisError('AI_CALL_ERROR', 'Key 입력에는 대화형 터미널이 필요합니다.')
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter('error', getpass.GetPassWarning)
                    self.key = getpass.getpass('OpenAI API Key 입력 (화면 표시·파일 저장 없음): ').strip()
            except getpass.GetPassWarning:
                raise AnalysisError('AI_CALL_ERROR', '비표시 입력이 지원되지 않습니다. Windows CMD 터미널을 사용하세요.') from None
        if not self.key:raise AnalysisError('AI_CALL_ERROR', 'OPENAI_API_KEY가 없습니다. --ask-api-key로 입력하세요.')
        if any(ord(char) < 33 or ord(char) > 126 for char in self.key):
            raise AnalysisError('AI_CALL_ERROR', 'API Key 형식을 확인하세요.')
        payload = {'model':self.model, 'input':messages, 'store':False,
                   'reasoning':{'effort':'low'}, 'service_tier':'default', 'max_output_tokens':self.max_output_tokens,
                   'text':{'format':{'type':'json_schema', 'name':'study_analysis_v02' if 'schema_version' in self.schema['properties'] else 'study_analysis_v01', 'strict':True, 'schema':self.transport_schema}}}
        request = urllib.request.Request('https://api.openai.com/v1/responses',
            data=json.dumps(payload,ensure_ascii=False,allow_nan=False).encode('utf-8'),
            headers={'Authorization':'Bearer '+self.key, 'Content-Type':'application/json'},method='POST')
        ticket=None
        if self.budget is not None:
            from .budget import reservation
            ticket=self.budget.reserve(self.model,reservation(self.model,len(request.data),self.max_output_tokens))
            self.trace['budget_reservation_id']=ticket
        self.trace.update(api_request_attempted=True, actual_ai_call=not self.injected_transport)
        start = time.monotonic()
        try:
            with self.transport(request, timeout=self.timeout) as response:
                self.trace['response_received'] = True
                self.trace['request_id'] = response.headers.get('x-request-id')
                body = json.loads(response.read().decode('utf-8'))
            if not isinstance(body, dict):raise AnalysisError('AI_CALL_ERROR','API 응답의 최상위 형식이 잘못되었습니다.')
            self.trace.update(response_id=body.get('id'), response_model=body.get('model'),
                              response_status=body.get('status'), usage=body.get('usage'))
            if body.get('status') != 'completed':
                raise AnalysisError('AI_CALL_ERROR','API 응답이 완료되지 않았습니다. trace의 상태를 확인하세요.')
            texts = []
            for output in body.get('output', []):
                if output.get('type') != 'message':continue
                for content in output.get('content', []):
                    if content.get('type') == 'refusal':raise AnalysisError('AI_CALL_ERROR','AI가 분석 요청을 거절했습니다.')
                    if content.get('type') == 'output_text':texts.append(content['text'])
            if not texts:raise AnalysisError('AI_CALL_ERROR','API 응답에 분석 본문이 없습니다.')
            return ''.join(texts)
        except AnalysisError:raise
        except urllib.error.HTTPError as error:
            self.trace.update(http_status=error.code, request_id=error.headers.get('x-request-id'))
            hint = {401:'인증 Key',403:'모델 접근 권한',429:'잔액·사용량 한도'}.get(error.code,'요청 설정·API 상태')
            raise AnalysisError('AI_CALL_ERROR',f'OpenAI HTTP {error.code}: {hint}를 확인하세요. 자동 재시도하지 않았습니다.') from None
        except Exception:
            raise AnalysisError('AI_CALL_ERROR','OpenAI 연결·시간 초과·API 응답 형식 오류. 자동 재시도하지 않았습니다.') from None
        finally:
            self.trace['elapsed_seconds'] = round(time.monotonic()-start,3)
            if self.budget is not None and ticket is not None:
                try:
                    self.budget.finish(ticket,self.model,self.trace.get('usage'))
                    self.trace['budget']=self.budget.status()
                except Exception:
                    self.trace['budget_update_warning']='예산 정산 기록 실패. 예약 금액과 호출 횟수는 유지됩니다.'
