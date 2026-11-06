# Claude 최초 교차 검토

세션: 6cb41c4f-41b0-4bf8-a739-39edd5e0f69f
구독: Pro 로그인 확인 후 실행. 정적 읽기 검토이며 실행 시험이 아님.

정적 검토 결과입니다. 이 세션에는 셸 도구가 없어서 `test_workflow.py`와 `compose.yaml`은 실행하지 못했습니다. 아래는 모두 코드를 읽고 추론한 내용입니다. 다섯 파일 외에는 읽지 않았고 수정도 하지 않았습니다.

```json
{
  "review": "Claude → GPT 구현 교차검토 (오프라인 원장 범위, 정적 읽기)",
  "bugs": [
    {
      "id": "B1", "severity": "high", "area": "완료 게이트·독립성",
      "location": "tools/workflow.py:255 (review 세션 검사), :231 (QA start 검사)",
      "problem": "QA 단계 검토자(REVIEWERS 03-qa = gpt|claude)는 '자기 QA 제작 세션과 다름'만 검사한다. 02-development 제작 세션과 같아도 통과한다. QA start에만 dev 세션 배제가 있고 review에는 없다.",
      "reproduction": "01·02 완료 후 QA 세션 'qa-1'로 start·submit. dev 제작 세션 '02-development'(provider claude)로 provider=claude, session='02-development'인 pass review를 제출하면 거부되지 않는다.",
      "fix": "stage_name=='03-qa'의 review에서도 session이 dev owner·dev review 세션(과거 라운드 포함)과 다르면 거부한다."
    },
    {
      "id": "B2", "severity": "high", "area": "보존·비밀정보",
      "location": "tools/workflow.py:133-145 (evidence), :82-89 (clean_packet)",
      "problem": "비밀정보 검사는 packet JSON에만 적용된다. 증거 파일 본문(LLM CLI 로그 등)은 검사 없이 evidence/ 스냅샷으로 영구 복사된다. verify가 스냅샷 해시를 요구하므로 나중에 지우면 원장이 깨진다. 문서(§4)의 '인증정보는 수집 단계에서 제외'와 어긋난다.",
      "reproduction": "'sk-'+32자 문자열이 든 log 파일을 submit의 artifacts로 제출하면 통과하고 evidence/<sha>.log에 그대로 보존된다.",
      "fix": "evidence()에서 파일 본문(크기 상한 포함)에 같은 패턴을 적용해 거부한다. 거부 시 스냅샷을 쓰지 않는다. 키 이름 목록에 client_secret, token, authorization도 추가한다."
    },
    {
      "id": "B3", "severity": "medium", "area": "실패 증거",
      "location": "tools/workflow.py:236-237 (start가 submission·review를 pop), :273-275",
      "problem": "수정 라운드에서 start하면 이전 submission이 보관 없이 삭제된다. 실패한 QA의 시나리오(expected/actual/passed), self_test, limitations가 state에서 사라진다. history에는 review(packet + artifacts)만 남는다. 원문은 raw/*-submit.json에만 있다. status의 limitations·evidence도 revision 동안 비어 보인다.",
      "reproduction": "test_failed_qa_is_recorded_but_cannot_pass 이후 start를 하면 state['stages']['03-qa']에서 scenarios가 사라진다. 이어서 status를 보면 limitations와 evidence가 빈 값이다.",
      "fix": "pop 전에 submission을 stage['rounds']나 history에 보관한다. summary는 최신 라운드가 없으면 직전 라운드의 한계를 표시한다."
    },
    {
      "id": "B4", "severity": "medium", "area": "실패 증거·차단",
      "location": "tools/workflow.py:289 (block 허용 상태), :291",
      "problem": "waiting 상태에서는 block이 불가능하다. 문서가 정한 차단 사유(로그인 실패, 도구 부재, 한도 소진)는 start 전에 발생하는 경우가 많은데 원장에 기록할 수 없다. 또 block은 free-text reason만 받고 사유 분류와 증거 파일이 없어서 '구분한다'(§3)를 구현하지 않는다.",
      "reproduction": "start 전에 block --stage 01-planning을 실행하면 '현재 단계는 차단할 수 없습니다'로 거부된다.",
      "fix": "waiting 허용(blocked_from='waiting', resume 시 waiting 복귀). category enum(login|tool_missing|quota|exec_failed|verification_mismatch)을 필수로 하고 evidence는 선택 허용한다."
    },
    {
      "id": "B5", "severity": "medium", "area": "비용 가드",
      "location": "tools/workflow.py:355 (doctor), tools/start_master.ps1:15-21",
      "problem": "(a) doctor의 'api_fallback': False는 상수다. 환경 변수도 설정도 검사하지 않는데 '대체 없음'이 확인된 것처럼 보인다. (b) 가드는 start_master.ps1로 띄운 Codex에만 적용된다. Claude는 구독 로그인을 확인하지 않고(-LoginClaude 경로만 있음), 이후 pane에서 실행되는 claude는 시작 시점 검사 밖이다. ANTHROPIC_API_KEY가 나중에 설정되거나 settings.json의 env·apiKeyHelper로 주입되면 막지 못한다. (c) 검사 목록에 OPENAI_API_BASE, CLAUDE_CODE_USE_BEDROCK, CLAUDE_CODE_USE_VERTEX 등이 없다.",
      "reproduction": "ANTHROPIC_API_KEY를 설정한 뒤 doctor를 실행하면 api_fallback=false가 나온다. Claude pane에서 CLAUDE_CODE_USE_BEDROCK=1을 설정해도 가드는 반응하지 않는다.",
      "fix": "doctor의 필드를 'api_fallback_checked': false로 바꾸거나, 위 변수 이름의 존재 여부(값은 제외)를 실제로 보고한다. 시작 스크립트에서 claude auth status를 확인하고 목록에 BEDROCK·VERTEX 변수를 추가한다."
    },
    {
      "id": "B6", "severity": "medium", "area": "멱등성·복구",
      "location": "tools/workflow.py:100-113 (locked), :216-218 (op 재생)",
      "problem": "(a) 크래시로 .lock이 남으면 복구 명령이 없다. 오류 메시지는 '잠금을 복구하세요'라고 하지만 문서는 직접 수정을 금지하고 방법을 안내하지 않는다. 저장된 PID도 사용하지 않는다. (b) op 재생이 packet JSON의 지문만 비교하고 참조 파일 내용은 비교하지 않는다. 같은 op로 재시도하기 전에 artifact를 고쳤다면 새 내용은 기록되지 않았는데도 성공으로 반환된다. (c) 잘못된 --id로 act나 timeline을 실행하면 docs/workflows/<오타>/와 .lock 디렉터리가 남는다.",
      "reproduction": "(a) .lock을 만든 뒤 어떤 변경 명령을 실행하면 영구 거부된다. (b) submit 성공 후 artifact를 수정하고 같은 op·packet으로 재실행하면 exit 0이다. 이때 verify는 act 안에서 재생 반환 뒤에 일어나므로 이 호출에서는 보이지 않고, 이어지는 summary에서만 무결성 문제가 드러난다.",
      "fix": "(a) PID 생존 확인이나 'unlock --confirm' 명령, 또는 문서에 수동 절차를 둔다. (b) 지문에 참조 파일 sha256을 포함하거나 재생 시 verify를 먼저 수행한다. (c) load 성공 뒤에 mkdir하거나 state.json이 없으면 디렉터리를 만들지 않는다."
    },
    {
      "id": "B7", "severity": "low", "area": "재작업",
      "location": "tools/workflow.py:295-299 (reopen)",
      "problem": "reopen이 defects·reviews 카운터를 0으로 초기화한다. 같은 결함이 reopen을 반복해도 반복 결함 에스컬레이션이 걸리지 않는다. 또 waiting 상태인 하위 단계의 빈 라운드도 archived_rounds에 쌓인다. reopen은 문서 §7 명령 목록(init…reassess)에도 없다.",
      "reproduction": "test_reopen_invalidates_downstream_and_keeps_history를 같은 reopen 사유로 3회 반복하면 stage['defects']가 매번 {}가 된다.",
      "fix": "누적 결함 수를 archived_rounds에서 합산해 임계값을 적용한다. waiting 단계는 archive하지 않는다. §7에 reopen을 추가한다."
    },
    {
      "id": "B8", "severity": "low", "area": "완료 게이트",
      "location": "tools/workflow.py:276-280",
      "problem": "4번째 검토는 verdict=pass여도 blocked가 된다. 의도된 규칙일 수 있으나 통과한 검토를 마스터 재평가로 강제 보낸다. 문서는 '재평가 없이 세 차례 검토 초과'라고만 적고 pass 케이스를 명시하지 않는다.",
      "reproduction": "fail 검토를 3회 한 뒤 4번째에 pass를 제출하면 blocked가 된다. 같은 결함 ID가 3회가 아니라 서로 다른 ID여도 마찬가지다.",
      "fix": "의도라면 문서에 명시한다. 아니라면 fail일 때만 reviews 초과를 적용한다."
    },
    {
      "id": "B9", "severity": "low", "area": "입력 처리",
      "location": "tools/workflow.py:226 이후 packet.get, :322 (scenario.get), :391 (except 절)",
      "problem": "packet이나 scenarios 항목이 dict가 아니면 AttributeError가 발생한다. main은 이를 잡지 않아 exit 2의 JSON 오류 대신 트레이스백이 출력된다.",
      "reproduction": "packet 파일 내용이 [] 이거나 scenarios:['x']이면 AttributeError가 난다.",
      "fix": "act·init 진입부에서 isinstance(packet, dict)를 검사하고, 시나리오 항목도 dict인지 확인한다."
    },
    {
      "id": "B10", "severity": "low", "area": "정리·일관성",
      "location": "tools/workflow.py:25 (TRANSITIONS), :344-345; tests: import copy/main",
      "problem": "TRANSITIONS는 정의만 되고 쓰이지 않아 실제 전이는 act 안에 흩어져 있으며 표와 구현이 어긋날 수 있다. identity_limit·automation_limit 문자열이 일본어다(나머지는 한국어). test_workflow.py는 main과 copy를 import만 하고 사용하지 않는다.",
      "reproduction": "status를 실행하면 일본어 문구가 출력된다.",
      "fix": "TRANSITIONS를 삭제하거나 act에서 실제로 사용한다. 문구를 한국어로 바꾼다. 사용하지 않는 import를 제거한다."
    }
  ],
  "unresolved_verification_not_bugs": [
    {"id": "U1", "item": "자체 선언 한계", "note": "session·provider·role=master·passed·approval 파일의 진위는 도구가 인증하지 않는다. docstring과 summary가 이 점을 밝히므로 결함이 아니라 한계다. 위 B1은 선언값 사이의 규칙 누락이라 별개다."},
    {"id": "U2", "item": "state.json 무결성", "note": "events의 raw 해시는 state와 같은 파일 안에 있고 해시 체인이 없다. state.json을 직접 고쳐 status를 complete로 바꾸고 artifact 해시만 맞추면 verify가 통과한다. 이벤트 재생 검증은 구현되지 않았다. 문서가 직접 수정을 금지할 뿐 탐지는 하지 않는다."},
    {"id": "U3", "item": "QA 대상 버전 연결", "note": "문서 §3은 '대상 버전'을 기록하라고 하는데 QA submission에는 dev 산출물 해시가 묶여 있지 않다. 현재는 dev 완료 단계의 verify가 간접적으로 막는다. 직접 연결이 없어서 'QA가 어느 버전을 시험했는지' 증거는 약하다."},
    {"id": "U4", "item": "실행 미확인", "note": "단위 시험과 compose verify를 실제로 실행해 보지 못했다. 통과 여부는 미검증이다. compose는 python:3.14-slim이 태그만 고정돼 있고 digest는 없다. Windows 바인드 마운트에서 uid 65534가 읽는 것도 미확인이다."},
    {"id": "U5", "item": "start_master.ps1 가정", "note": "HERDR_ENV=='1'이 herdr pane 안에서 실제로 설정되는지, -c forced_login_method='chatgpt'가 유효한 Codex 설정 키인지, 'Logged in using ChatGPT' 문구가 실제 출력과 일치하는지는 확인하지 못했다. pwsh 7에서 2>&1과 $ErrorActionPreference='Stop' 조합이 문제없는지도 미확인이다. HERDR_ENV 가정이 틀리면 herdr가 중첩 실행될 수 있다."},
    {"id": "U6", "item": "OneDrive 경로", "note": "프로젝트가 OneDrive 동기화 폴더 안에 있다. os.replace나 O_EXCL 잠금이 동기화 중 PermissionError(OSError → exit 2)를 낼 가능성은 실제로 확인하지 않았다."},
    {"id": "U7", "item": "테스트 공백", "note": "QA 검토자=dev 제작 세션(B1), 증거 본문 비밀(B2), 수정 라운드 후 실패 시나리오 보존(B3), waiting에서 block(B4), 같은 op 재생 후 파일 변경(B6), CLI 종료 코드(main)를 다루는 테스트가 없다."}
  ],
  "ok_confirmed_by_reading": [
    "완료는 pass 검토 + 마스터 선언 + 아티팩트·증거 해시 재확인을 모두 요구한다.",
    "경로 탈출·절대경로·심볼릭 링크를 거부한다.",
    "상태 저장은 원자적 replace를 쓴다.",
    "같은 op는 같은 지문일 때만 무변경 재생된다.",
    "init은 요구사항이 같으면 no-op이고 다르면 거부한다.",
    "reopen은 하위 단계를 archive해 스냅샷을 보존한다.",
    "compose는 network none·read_only·cap_drop ALL·비루트·tools 읽기 전용이라 자격 증명과 소켓 접근이 없다."
  ]
}
```

우선순위는 B1(QA 독립성 구멍)과 B2(증거에 비밀이 영구 보존됨), 그다음 B5·B3·B4·B6 순을 권합니다. 파일 수정은 요청이 있을 때만 하겠습니다.