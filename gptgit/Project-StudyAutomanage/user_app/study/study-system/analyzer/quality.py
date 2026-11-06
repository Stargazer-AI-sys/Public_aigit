import re
import unicodedata
TYPES=('개념','참고자료','실습','프로젝트','문제/예제','기타')
VERSION='quality-v0.4'
RULES='''[QUALITY RULES]
- summary는 한 문장, 공백 포함 120자 이내로 작성하고 줄바꿈하지 마세요.
- material_type.material_type은 개념/참고자료/실습/프로젝트/문제/예제/기타 중 하나입니다. 문제/예제는 한 분류명입니다. 혼합 자료는 중심 목적에 따라 하나를 고르고 reason에 혼합 성격을 설명하세요.
- 주 유형은 문서의 학습 목적, 설명 구조, 수행·확인 과제의 흐름으로 판단하세요. 명령어가 많다는 이유만으로 실습으로 분류하지 마세요.
- 분류 기준: 개념은 정의·원리·비교의 이해가 중심, 실습은 설정·수행·확인 절차가 중심(성공 기록이 없어도 가능), 참고자료는 빠른 조회가 중심, 프로젝트는 통합 목표·산출물 구현이 중심, 문제/예제는 질문 풀이·해설이 중심, 기타는 앞의 기준에 해당하지 않는 자료입니다.
- 혼합 자료의 reason에는 주 목적, 함께 포함된 설명·설정 명령·관찰 기록을 구분해 서술하세요. 일부 항목의 실행 결과가 없다는 이유로 자료 전체에 관찰 기록이 없다고 단정하지 마세요. 주 목적이 불명확하면 confidence를 낮추고 불확실성을 설명하세요.
- 핵심 개념을 빠뜨리지 말고 concepts.name은 일관된 이름을 사용하세요. 이름 중복은 금지합니다.
- relationships의 from/to와 모든 related_concepts의 이름은 concepts.name에 존재해야 하며 정확하게 일치해야 합니다.
- 먼저 원문에 근거한 concepts 목록을 확정하고, 관계의 양쪽 대상 개념을 반드시 이 목록에 포함하세요. 관계·related_concepts에는 목록의 이름을 그대로 복사하세요.
- JSON 출력 직전에 모든 from/to 및 related_concepts를 concepts.name 목록과 대조하여 누락 참조가 없는지 자체 점검하세요. VLAN과 VLAN 액세스 포트처럼 범위가 다른 이름을 같은 개념으로 간주하지 마세요.
- 참조 대상 개념을 원문으로 설명할 수 없다면 참조를 맞추려고 임의 개념을 추가하지 말고 근거 없는 관계·참조를 생성하지 마세요. 외부 지식으로 빈 개념을 채우지 마세요.
- theory와 practice의 evidence는 원문에서 그대로 찾을 수 있는 하나의 연속 구절로 작성하세요.
- evidence 안의 단어·숫자·명령 예시·줄바꿈·중간 문장을 생략하거나 고쳐 쓰지 마세요. 떨어진 문장을 붙여 하나의 인용으로 만들지 마세요. 여러 줄을 인용할 때는 중간 줄도 모두 포함하세요.
- 인용은 현재 세부 주제의 설명을 뒷받침하는 연속 구간으로 선택하세요. 같은 학습 목적의 관련 설정·장비별 비교·관찰 조건은 함께 포함할 수 있으며 길이만으로 줄이지 마세요. 멀리 떨어진 근거를 포괄하느라 무관한 세부 주제가 섞이면 theory/practice 항목을 나눠 각각 충분한 연속 근거를 연결하세요. 원문은 자르거나 수정하지 마세요.
- concepts/theory/practice의 설명은 자료에 무엇이 있다는 소개에 머물지 말고, 원문에 명시된 핵심 내용·설정값·대상 장비와 인터페이스·관찰 조건을 해당 주제에 필요한 만큼 정리하세요. 민감한 인증값을 설명에 반복하지 말고, 원문에 없는 정의·설정 목적·장비 간 연결·실행 결과는 추측하지 마세요.
- 명령 예시, 수행·확인 지시, 원문에 적힌 관찰 기록, 성공 여부 미확인을 구분하세요. 명령어만 있는 자료를 실습 성공으로 표현하지 마세요.
- 핑 성공·타임아웃·라우팅 테이블 출력이 원문에 있으면 관련 theory/practice 설명에 관찰 기록으로 반영하세요. 어떤 설정·장비에서 발생했는지 연결 근거가 없으면 원인이나 설정 성공을 확정하지 마세요. 핑 명령만 있으면 성공 여부 미확인입니다.
- practice.description의 설정·삭제·관찰 등 각 주장에는 해당 evidence가 충분한 근거가 되어야 합니다. 근거 구절이 설정 명령뿐이면 삭제나 관찰까지 뒷받침한다고 취급하지 마세요.
- 원문의 주요 설명·설정·관찰 구간을 검토해 누락을 줄이세요. 불완전한 계산·질문·메모는 불완전함을 밝히거나 근거가 부족하면 생략하고, 완성된 결과를 추측하지 마세요.
- 관계는 주어·관계·대상 사이의 연결이 원문에 명확할 때만 만드세요. 같은 문단에 언급되었다는 이유만으로 연결하지 말고, 핑 예시를 VLAN 간 라우팅의 검증으로 단정하지 마세요.
- concepts.description에서도 설정·확인 지시를 실제 수행으로 바꾸지 마세요. 결과가 없으면 '설정 예시', '확인하도록 안내'처럼 표현하세요.
- 불완전한 문장은 용어 이름을 알고 있어도 외부 지식으로 완성하지 말고, 원문에서 확인되는 내용과 설명이 미완성인 부분을 구분하세요.
- 원문의 단순화나 의심스러운 단정은 '자료에서는 ...로 설명한다'처럼 원문 설명임을 표시하세요. 제공된 외부 검증 근거가 없으면 검증된 사실로 주장하지 마세요.
- 원문에 없는 내용은 만들지 마세요. 내용이 없는 선택 항목은 생략하며 API 전용 구조에서는 null로 반환하세요.
'''


def quality_errors(analysis,text):
    errors=[]
    def error(path,message):errors.append({'path':path,'message':message})
    summary=analysis.get('summary','')
    if not summary.strip() or len(summary)>120 or '\n' in summary or '\r' in summary:
        error('/summary','요약은 한 문장·공백 포함 120자 이내여야 합니다.')
    if len(re.findall(r'[.!?。！？]+(?=\s|$)',summary))>1:
        error('/summary','요약에 여러 문장이 있습니다.')
    if analysis.get('material_type',{}).get('material_type') not in TYPES:
        error('/material_type/material_type','확정된 6개 자료 유형 중 하나여야 합니다.')
    names=[item['name'] for item in analysis.get('concepts',[])]
    normalized=[re.sub(r'\s+','',unicodedata.normalize('NFKC',name)).casefold() for name in names]
    if any(not name.strip() for name in names) or len(normalized)!=len(set(normalized)):
        error('/concepts','비어 있거나 중복된 개념 이름이 있습니다.')
    available=set(names)
    for index,relation in enumerate(analysis.get('relationships',[])):
        for key in ['from','to']:
            if relation[key] not in available:error(f'/relationships/{index}/{key}','관계 대상이 concepts.name에 없습니다.')
    def visit(value,path):
        if isinstance(value,dict):
            if 'related_concepts' in value:
                for i,name in enumerate(value['related_concepts']):
                    if name not in available:error(path+f'/related_concepts/{i}','참조 개념이 concepts.name에 없습니다.')
            if 'evidence' in value and (not value['evidence'].strip() or value['evidence'] not in text):
                error(path+'/evidence','근거 구절이 원문에 그대로 존재하지 않습니다.')
            for key,child in value.items():visit(child,path+'/'+key)
        elif isinstance(value,list):
            for i,child in enumerate(value):visit(child,path+'/'+str(i))
    visit(analysis,'')
    from .schemas import V02_VERSIONS
    if analysis.get('schema_version') in V02_VERSIONS:
        from .knowledge import knowledge_errors
        errors.extend(knowledge_errors(analysis))
    return errors


def review_report():
    return {'mechanical_checks':'PASS','policy_version':VERSION,'content_review_required':True,
            'review_items':['혼합 자료의 주 목적과 분류 근거','명령·관찰 기록·성공 여부 미확인의 구분','주요 구간 및 불완전한 메모 누락','근거가 설명을 충분히 뒷받침하는지','명령 예시와 실제 실습 성공의 구분','원문 단정 및 기술적 사실성','동일 개념의 의미상 명칭 일관성']}
