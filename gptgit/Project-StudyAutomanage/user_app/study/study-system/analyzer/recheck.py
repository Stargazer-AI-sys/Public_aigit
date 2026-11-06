"""Offline validation of saved responses. No key, transport, ledger or live cache."""
import json
from pathlib import Path
from .core import analyze,strict_json,validate_input
from .evidence import resolve_evidence
from .openai_provider import omit_optional_nulls


class SavedResponseProvider:
    name='saved-response'
    def __init__(self,schema,text,raw):
        self.schema,self.text,self.raw=schema,text,raw
        self.evidence_report=[]
        self.trace={'actual_ai_call':False,'api_request_attempted':False,'automatic_retries':0,
                    'offline_revalidation':True,'content_review_required':True,
                    'usage':{'input_tokens':0,'output_tokens':0,'total_tokens':0}}
    def generate(self,messages):return self.raw
    def normalize(self,data):
        data=omit_optional_nulls(data,self.schema,self.schema)
        data,self.evidence_report=resolve_evidence(data,self.text,allow_legacy_recovery=True)
        return data


def recheck_run(directory,schema,reference_context=None,reference_context_warning=False):
    directory=Path(directory)
    data=validate_input(strict_json((directory/'analyzer_input.json').read_text(encoding='utf-8-sig')))
    raw=strict_json((directory/'raw_response.json').read_text(encoding='utf-8-sig'))
    if not isinstance(raw,str):raw=json.dumps(raw,ensure_ascii=False,allow_nan=False)
    provider=SavedResponseProvider(schema,data['extracted_text'],raw)
    provider.reference_context=reference_context or []
    provider.reference_context_warning=reference_context_warning
    result,audit=analyze(data,provider,schema)
    audit['trace']['origin_run_directory']=str(directory.resolve())
    return data,result,audit
