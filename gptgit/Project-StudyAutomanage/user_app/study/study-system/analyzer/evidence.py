"""Resolve numbered source spans; final evidence always contains verbatim source."""
import copy
from .core import AnalysisError


def numbered_source(text):
    return '\n'.join(f'[L{i}] {line.rstrip(chr(13)+chr(10))}' for i,line in enumerate(text.splitlines(keepends=True),1))


def resolve_reference(ref,text):
    lines=text.splitlines(keepends=True)
    if not isinstance(ref,dict) or set(ref)!={'start_line','end_line'}:
        raise AnalysisError('EVIDENCE_REFERENCE_ERROR','근거 줄 범위 형식이 잘못되었습니다.')
    start,end=ref['start_line'],ref['end_line']
    if any(not isinstance(n,int) or isinstance(n,bool) for n in (start,end)) or not 1<=start<=end<=len(lines):
        raise AnalysisError('EVIDENCE_REFERENCE_ERROR','근거 줄 번호가 원문 범위를 벗어나거나 역순입니다.')
    quote=''.join(lines[start-1:end]).rstrip('\r\n')
    if not quote.strip():raise AnalysisError('EVIDENCE_REFERENCE_ERROR','빈 줄만 근거로 선택할 수 없습니다.')
    return quote


def restore_legacy_quote(quote,text):
    """Restore only unique exact line anchors in source order, never fuzzy matching."""
    if not isinstance(quote,str) or quote in text:return None
    anchors=[line for line in quote.splitlines() if line.strip()]
    if len(anchors)<2:return None
    lines=text.splitlines(keepends=True);located=[];cursor=0
    for line in lines:
        located.append((cursor,line.rstrip('\r\n')));cursor+=len(line)
    matches=[]
    for anchor in anchors:
        exact=[(i,offset,offset+len(anchor)) for i,(offset,line) in enumerate(located,1) if line==anchor]
        candidates=exact or [(i,offset+pos,offset+pos+len(anchor)) for i,(offset,line) in enumerate(located,1)
                              for pos in range(len(line)-len(anchor)+1) if line.startswith(anchor,pos)]
        if len(candidates)!=1:return None
        matches.append(candidates[0])
    if any(a[2]>b[1] for a,b in zip(matches,matches[1:])):return None
    start,end=matches[0][1],matches[-1][2]
    return text[start:end],{'start_line':matches[0][0],'end_line':matches[-1][0],'source_start':start,'source_end':end}


def resolve_evidence(data,text,*,allow_legacy_recovery=False):
    data=copy.deepcopy(data);report=[]
    def visit(value,path):
        if isinstance(value,dict):
            if 'evidence' in value:
                evidence=value['evidence']
                if isinstance(evidence,dict):
                    value['evidence']=resolve_reference(evidence,text)
                    report.append({'path':path+'/evidence','method':'source_line_reference','reference':evidence})
                elif allow_legacy_recovery:
                    restored=restore_legacy_quote(evidence,text)
                    if restored:
                        quote,span=restored;value['evidence']=quote
                        report.append({'path':path+'/evidence','method':'unique_exact_anchor_span_recovery','before':evidence,'after':quote,**span})
            for key,child in value.items():visit(child,path+'/'+key)
        elif isinstance(value,list):
            for i,child in enumerate(value):visit(child,path+'/'+str(i))
    visit(data,'')
    return data,report
