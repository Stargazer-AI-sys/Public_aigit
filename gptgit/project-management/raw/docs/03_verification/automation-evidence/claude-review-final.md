# Claude 수정 후 교차 검토

세션: 6cb41c4f-41b0-4bf8-a739-39edd5e0f69f
범위: 로컬 엔진 정적 검토 및 가이드 기획 사전 검토. 실제 시험은 별도 로그 참조.

```json
{
  "scope": "소스 수정 없음, 정적 읽기 검토. 셸 도구가 없어 시험을 직접 재실행하지 못했다.",
  "local_engine": {
    "verdict": "PASS (로컬 오프라인 원장 범위에 한정)",
    "remaining_required_defects": [],
    "prior_findings": {
      "B1": "해결. workflow.py:264-269에서 QA 검토자가 dev 현재·보관 라운드의 제작·검토 세션과 같으면 거부한다. test_qa_reviewer_cannot_be_developer로 확인된다.",
      "B2": "해결. :143에서 증거 본문을 검사하고 :141에서 20MB 상한을 둔다. 거부 시 스냅샷을 쓰지 않으며 test_secret_evidence_is_not_copied가 이를 확인한다.",
      "B3": "해결. :242-243에서 재시작 전에 submission과 review를 revision_rounds에 보관한다. summary에 previous_limitations가 추가됐고 verify의 스냅샷 순회 대상에도 들어간다.",
      "B4": "해결(대기 단계 차단). :304에서 waiting을 허용하고 resume 시 waiting으로 복귀한다. 사유 분류는 자유 문구라 test는 'tool_missing:' 접두 관례만 쓴다. 필수 결함은 아니다.",
      "B6": "해결. 재생 경로(:223)에서 verify를 먼저 수행하고, test_replayed_operation_detects_artifact_drift가 이를 확인한다. 잠금 복구는 workflow_packets.md의 PID 확인 후 수동 제거 정책으로 처리한다.",
      "B7": "코드상 해결. reopen이 attempt, reviews, defects를 이월한다(:317). 반복 결함 재평가 중에는 reopen을 거부한다(:310). 이 동작을 직접 검증하는 테스트는 없다(아래 U-a).",
      "B9": "해결. clean_packet이 객체인지 검사하고(:80), scenarios 항목과 defects 항목의 dict 여부도 검사한다.",
      "B10": "해결. TRANSITIONS를 삭제했고 일본어 문구도 한국어로 바꿨다.",
      "B5": "보고된 한계로 수용한다. 시작기 경로만 보호하고, 환경 변수 목록이 확장됐으며 doctor는 api_fallback_checked=false로 바뀌었다."
    },
    "tests": "unit-tests.txt는 24건 OK이고, 테스트 이름이 현재 test_workflow.py의 24개와 일치한다. 실행 명령·시각·소스 해시가 로그에 없어서 현재 소스로 돌린 결과인지는 로그만으로 증명되지 않는다."
  },
  "residual_nonblocking": [
    {
      "id": "R1", "severity": "low",
      "location": "workflow.py:237, :266-268",
      "note": "QA 독립성 제외 목록에 dev의 revision_rounds와 history에 있는 이전 수정 회차 세션이 빠져 있다. 예를 들어 dev 1차 제작 세션이나 1차 실패 검토 세션이 QA 검토자가 될 수 있다. 세션 ID는 어차피 자기 신고라 차단 결함으로 보지 않는다. 고친다면 제외 목록에 r['submission']['session']과 history의 session을 더하면 된다."
    },
    {
      "id": "R2", "severity": "low",
      "location": "workflow.py:104 (locked), :219",
      "note": "존재하지 않거나 오타가 난 --id로 act·timeline을 실행하면 빈 docs/workflows/<id>/ 폴더가 남는다. 상태에는 영향이 없다."
    },
    {
      "id": "R3", "severity": "low",
      "location": "docs/02_design/automation_workflow.md 변경 이력",
      "note": "§7이 크게 바뀌었는데(reopen·20MB·재평가 정책) 버전 0.1과 이력 한 줄이 그대로다. AGENTS의 '의미 있는 변경은 버전·이력 반영' 규칙과 어긋난다."
    }
  ],
  "unresolved_verification_not_bugs": [
    "U-a: 테스트가 없는 분기: reopen의 카운터 이월, 재평가 중 reopen 거부, 네 번째 pass 차단, PID 잠금 정책, CLI 종료 코드(main).",
    "U-b: 신고된 세션·제공자·마스터 역할·passed 값의 진위, state.json 직접 편집 탐지(해시 체인 없음), QA와 dev 산출물 버전 직접 결속은 여전히 미검증이거나 설계 한계다.",
    "U-c: start_master.ps1의 HERDR_ENV=='1' 가정, forced_login_method 키의 유효성, codex login status 출력 문구는 실행 확인이 없다.",
    "U-d: Docker(compose) 실행, herdr 완주, Claude·Hermes 실제 연결, GUI 사용자 검토는 모두 미검증이다. 위 PASS를 '전체 자동화 통과'로 읽으면 안 된다."
  ],
  "guide_planning": {
    "target": "docs/workflows/guide-prototype/00-request/request.json + 01-planning/plan.md",
    "verdict": "FAIL (필수 수정 1건 후 PASS 가능)",
    "passes": [
      "R1~R4가 Phase 1의 Task에 하나씩 대응한다.",
      "request.json의 out_of_scope를 위반하지 않는다(API 비용, Slack, 클라우드 없음).",
      "herdr·Docker·Hermes 미검증과 사용자 시각 검토 미수행을 계획에 명시했다.",
      "approval.md가 승인 범위와 미승인 범위를 구분한다."
    ],
    "required_defects": [
      {
        "id": "G1", "severity": "medium",
        "location": "plan.md:22 (최종 파일), :7-9 (대표 한 페이지 먼저 보여주고 확인 뒤 제작)",
        "problem": "산출물로 지정한 guide_docs/AI_작업_요청과_재개_가이드.html이 이미 존재한다. state.json에서는 01-planning부터 04-wiki까지 모두 waiting이고 start·submit도 없다. 즉 이 파일은 원장 밖에서 만들어졌고, '대표 페이지 확인 후 제작' 순서와도 맞지 않는다. 계획이 이 파일을 초안으로 보고 개정할지, 덮어쓸지, 무효로 볼지 밝히지 않는다. 덮어쓰기 전 대상 확인 원칙과도 충돌한다.",
        "reproduction": "guide_docs/ 목록에 해당 파일이 있고, state.json의 모든 단계가 waiting이다.",
        "fix": "plan.md에 한 줄을 추가한다. 예: '기존 파일은 원장 밖 선행 초안이며 QA 대상이 아니다. 이를 02-development의 입력으로 개정하거나 새로 대체한다.' 기존 파일은 그대로 보존하고, 제출 시 산출물 해시로 고정한다."
      }
    ],
    "gate_status_not_a_content_bug": "plan.md는 아직 start·submit되지 않았고, 01-planning의 지정 검토자인 Claude의 원장 검토도 없다. 그래서 '승인된 계획'이 아니다. 이 문서의 판정은 사전 교차검토 의견이며 원장의 pass 검토로 기록된 것이 아니다.",
    "optional_suggestions": [
      "R3에 '같은 작업ID로 재시도'와 '완료된 단계는 다시 실행하지 않음'을 한 줄로 넣으면 중복 방지 절차가 더 분명해진다.",
      "R4의 '실제 가능한 명령'은 status, report, doctor 정도로 목록을 고정해 두면 QA 대조가 쉬워진다."
    ]
  },
  "overall": "로컬 원장 엔진은 PASS이고 남은 필수 결함은 없다. 가이드 기획은 G1을 고치기 전까지 FAIL이다. herdr 완주, Docker, Hermes, GUI 사용자 검토가 모두 미검증이라 전체 자동화는 통과로 선언할 수 없다."
}
```