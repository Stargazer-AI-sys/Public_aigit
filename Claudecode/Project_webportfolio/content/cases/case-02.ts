import { FlowCase02 } from "@/components/case/flow-case-02";

import type { CaseData } from "./types";

export const case02: CaseData = {
  slug: "case-02",
  head: {
    back: { label: "← AI Workflows로 돌아가기", href: "/#p-case2" },
    eyebrow:
      "CASE 02 · 프로젝트 구조와 협업 방식 · project-management · project-prototype",
    title: "맡을 사람과 기록할 곳부터 나눴습니다",
    lead: "여러 AI가 함께 일하려면 누가 무엇을 맡고 결과를 어디에 남기는지가 먼저 정해져야 했습니다.\n개선하는 곳과 시험하는 곳을 나누고, 마스터 AI가 담당에게 일을 나눠 맡기는 구조를 만들어 시험했습니다.",
    toc: [
      { id: "c2-overview", label: "개요" },
      { id: "c2-plan", label: "분석 및 계획" },
      { id: "c2-tree", label: "폴더 구조" },
      { id: "c2-flow", label: "프로세스" },
      { id: "c2-screens", label: "실제 화면" },
      { id: "c2-issue", label: "발생한 문제" },
      { id: "c2-next", label: "개선할 내용" },
    ],
    legend: [
      { badge: "확인", text: "파일과 실행 기록에서 직접 봄" },
      {
        text: "수치 출처: 점검 보고서(2026.10.29), 작업기록·위임 보고·시험 보고(~2026.11.06)",
      },
    ],
  },
  sections: [
    {
      id: "c2-overview",
      title: "개요",
      blocks: [
        {
          type: "paragraph",
          text: "2026년 10월 13일 역할 정의에서 시작한 개인 학습 프로젝트입니다.\n11.04에 개선 원본과 시험 프로젝트를 나눴고, 11.06에는 herdr에서 마스터 1개와 담당 6개로 소규모 시험을 했습니다.",
        },
        {
          type: "tiles",
          items: [
            {
              value: "2개",
              label: "개선 원본(project-management)과 독립 시험(project-prototype)",
            },
            { value: "1 + 6", label: "11.06 herdr 시험의 마스터와 담당 pane" },
            { value: "20개", label: "11.05 내용별로 다시 정리한 위키 문서" },
            { value: "6분류", label: "기능, 구조, 결정, 운영, 이력, 탐색" },
          ],
        },
        {
          type: "split",
          items: [
            {
              title: "제가 맡은 일",
              text: "프로젝트 역할 결정과 정정, 시험 조건 제시(6개 이상 pane을 눈으로 확인), 실행 범위와 훅 신뢰 승인",
              highlight: true,
            },
            {
              title: "AI가 맡은 일",
              text: "마스터의 분담·전달·회수·통합, 담당별 작성과 독립 검토, 형식 검사, 위키 재구성",
            },
          ],
        },
      ],
    },
    {
      id: "c2-plan",
      title: "분석 및 계획",
      blocks: [
        {
          type: "paragraph",
          text: "10.29 점검에서 사람이 AI 사이를 손으로 잇는 구간과, 실행 방식에 따라 지침이 빠지는 문제를 확인했습니다.\n담당을 늘리기 전에 프로젝트와 역할, 기록 위치부터 정하기로 했습니다.",
        },
        { type: "heading", text: "두 프로젝트의 역할" },
        {
          type: "table",
          columns: ["위치", "역할", "넣지 않는 것"],
          rowHeader: true,
          rows: [
            [
              "공통(gptgit)",
              "공통 AI 규칙, 공유 위임 스킬, 모델 검사 도구",
              "프로젝트별 역할과 상세 기록",
            ],
            [
              "project-management",
              "프로세스 개선의 논의, 설계, 검증, 작업기록 원본",
              "개별 프로젝트의 소스와 상세 실행 기록",
            ],
            [
              "project-prototype",
              "개선된 프로세스를 독립적으로 적용하는 시험",
              "관리 작업의 이력, 보류, 세션, 설치 경로",
            ],
          ],
        },
        { type: "heading", text: "역할 분담(project-prototype 기준)" },
        {
          type: "table",
          columns: ["역할", "책임", "금지"],
          rowHeader: true,
          rows: [
            [
              "마스터",
              "사용자 창구, 담당 전달·회수, 근거 대조와 통과 판정",
              "근거 없는 완료 판정, 범위와 비용 임의 확대",
            ],
            [
              "Codex 기획",
              "요구사항을 설계, Task, 시험 조건에 연결",
              "승인 없는 요구사항 변경",
            ],
            [
              "Claude 기획 검토",
              "고정된 기획서의 누락, 충돌, 실행 가능성 지적",
              "원본 직접 수정",
            ],
            ["Claude 개발", "승인된 Task 제작과 자체 시험", "자기 결과 최종 승인"],
            [
              "독립 QA",
              "제작자와 다른 세션에서 실제 사용 시험",
              "제작자의 성공 보고로 시험 대체",
            ],
            [
              "Hermes 문서화",
              "검증된 결과로 작업기록·위키 초안 작성",
              "근거 밖 사실과 완료 상태 추가",
            ],
          ],
        },
        { type: "heading", text: "협업 규칙" },
        {
          type: "steps",
          items: [
            {
              title: "1 소유권",
              text: "한 파일에는 한 시점에 한 작성자만 둡니다. 검토 담당은 제작 파일을 고치지 않습니다.",
            },
            {
              title: "2 최소 입력",
              text: "담당은 자기 Task와 필요한 원본만 받습니다. 작업기록 탐색은 마스터가 맡습니다.",
            },
            {
              title: "3 전용 탭",
              text: "마스터 탭은 나누지 않고 담당은 새 탭에서 시작합니다(11.06).",
            },
            {
              title: "4 기록 위치",
              text: "실행별 상태와 근거는 실행 기록에, 짧은 최신 인계는 작업기록에, 설명은 위키에 둡니다.",
              highlight: true,
            },
          ],
        },
      ],
    },
    {
      id: "c2-tree",
      title: "폴더 구조",
      blocks: [
        {
          type: "paragraph",
          text: "구조와 협업에 관련된 폴더만 추렸습니다.\n시험 프로젝트에는 관리 작업의 이력과 PC 경로를 넣지 않습니다.",
        },
        {
          type: "tree",
          lines: [
            [{ bold: "gptgit/" }],
            ["├─ AGENTS.md                         ", { note: "# 공통 규칙: 역할별 모델, 위임 기준" }],
            ["├─ skills/delegation-reporting/      ", { note: "# 담당 위임과 보고 공유 스킬" }],
            ["├─ tools/"],
            ["│  ├─ check_agent_model.py           ", { note: "# 역할별 허용 모델 검사" }],
            ["│  ├─ start_managed_agent.py         ", { note: "# 담당 시작" }],
            ["│  └─ agent_model_hook.py            ", { note: "# 금지 모델 시작 명령 차단 훅" }],
            ["│"],
            ["├─ ", { bold: "project-management/" }, "              ", { note: "# 개선 원본" }],
            ["│  ├─ docs/04_records/management_log.md  ", { note: "# 최신 인계와 남은 업무" }],
            ["│  ├─ report_docs/                   ", { note: "# 날짜별 위임 보고" }],
            ["│  ├─ tests_result/                  ", { note: "# 시험 결과(11.06 herdr 6담당)" }],
            ["│  ├─ skills/wiki-editor/            ", { note: "# 위키 편집 기준·스키마·검사기" }],
            ["│  ├─ wiki/                          ", { note: "# features · architecture · decisions" }],
            ["│  │                                 ", { note: "#   operations · log · index" }],
            ["│  └─ raw/                           ", { note: "# 과거 원문 보관(수정 안 함)" }],
            ["│"],
            ["└─ ", { bold: "project-prototype/" }, "               ", { note: "# 독립 시험" }],
            ["   ├─ docs/workflow.md               ", { note: "# 기획 검토·개발 QA·문서화 순서" }],
            ["   ├─ docs/context-and-agents.md     ", { note: "# 최소 입력·병렬 작업·인계" }],
            ["   ├─ docs/records/work_log.md       ", { note: "# 자체 작업의 최신 인계" }],
            ["   ├─ templates/                     ", { note: "# 작업명세서 · 개발기획서 · Task 입력" }],
            ["   ├─ tools/                         ", { note: "# 역할 시작기 · 전달 도구 · 상태 원장" }],
            ["   └─ wiki/                          ", { note: "# 같은 6분류 위키" }],
          ],
        },
      ],
    },
    {
      id: "c2-flow",
      title: "프로세스 순서도",
      blocks: [
        {
          type: "diagram",
          Flow: FlowCase02,
          caption:
            "어두운 칸은 사용자가 결정하는 지점입니다. 단계별로 일부 시험은 했지만, 요구사항부터 문서화까지 한 번에 완주한 기록은 아직 없습니다.",
        },
        { type: "heading", text: "11.06 herdr 6담당 시험", ev: true },
        {
          type: "table",
          columns: ["담당", "맡은 일과 회수 결과"],
          rowHeader: true,
          rows: [
            ["마스터", "배치, 담당 시작, 작업 전달, 원문 대조, 샘플 작성, 검사와 최종 통합"],
            ["wiki-plan", "목적, 포함·제외, 수락 기준 3개 제안"],
            ["wiki-sources", "주장별 근거 연결, 출처 경로, 상태 보존 기준"],
            ["wiki-draft", "원문 보관과 설명의 차이, 내용 합성에 관한 초안"],
            ["wiki-ops", "작성 → 형식 검사 → 내용 검토 흐름과 검사 한계"],
            ["wiki-format", "필수 검사 5개, 샘플 형식 검사 실행(오류 0)"],
            ["wiki-review", "독립 검토 기준 4개, 샘플과 원문 3개 대조(필수 결함 0)"],
          ],
        },
        { type: "heading", text: "11.02 역할 분담 시험", ev: true },
        {
          type: "paragraph",
          text: "Claude가 만든 작은 함수를 GPT가 별도로 실행해 같은 결과를 확인했습니다.",
        },
        {
          type: "table",
          columns: ["입력", "예상값", "Claude 자체 실행", "GPT 별도 실행", "판정"],
          rowHeader: true,
          rows: [
            ["[1, 2, 3, 4]", "6", "6", "6", "통과"],
            ["[]", "0", "0", "0", "통과"],
            ["[-4, -3, -2, 1, 2]", "-4", "-4", "-4", "통과"],
          ],
        },
      ],
    },
    {
      id: "c2-screens",
      title: "실제 화면",
      blocks: [
        {
          type: "paragraph",
          text: "2026년 11월 6일에 캡처한 herdr와 Obsidian 화면입니다.\n이미지를 누르면 화면 가운데에 크게 열립니다.",
        },
        {
          type: "shots",
          items: [
            {
              src: "/img/case02-herdr-dispatch.png",
              alt: "herdr 화면. 왼쪽 위 마스터가 담당 6개에게 각각 다른 작업을 전달한 모습",
              caption:
                "마스터(왼쪽 위)가 담당 6개에게 기획, 출처, 본문, 운영, 형식, 검토를 나눠 전달했습니다.",
              wide: true,
            },
            {
              src: "/img/case02-herdr-parallel.png",
              alt: "herdr 화면. 담당들이 각자 결과를 반환하고 마스터가 진행 상황을 보고하는 모습",
              caption:
                "각 담당의 결과를 회수해 하나의 샘플로 합친 뒤, 형식 담당과 독립 내용 검토 담당에게 다시 보냈습니다.",
              wide: true,
            },
            {
              src: "/img/case02-obsidian-wiki.png",
              alt: "Obsidian에서 위키 문서를 연 화면. 왼쪽에 6분류 폴더, 본문에 구조 도식",
              caption:
                "6분류로 다시 정리한 위키를 Obsidian에서 읽는 화면입니다. 구조 도식이 본문과 함께 표시됩니다.",
            },
            {
              src: "/img/case02-obsidian-graph.png",
              alt: "Obsidian 그래프 뷰. 위키 문서들이 서로 연결된 모습",
              caption:
                "그래프 뷰: README, AGENTS, 작업기록과 위키 문서가 서로 어떻게 연결되는지 봅니다.",
            },
          ],
        },
      ],
    },
    {
      id: "c2-issue",
      title: "발생한 문제",
      blocks: [
        {
          type: "issues",
          items: [
            {
              title: "사람이 AI 사이를 손으로 이었습니다",
              rows: [
                {
                  label: "근거",
                  text: "외부 Codex와 herdr 안의 GPT가 모두 마스터처럼 움직였고 프롬프트와 결과를 제가 복사해 옮겼습니다. 창구를 하나로 정한 10.28 이후에도 외부에서 작업이 이어졌습니다.",
                  ev: true,
                },
                {
                  label: "조치",
                  text: "담당 실행, 전달, 회수를 마스터가 맡도록 정했습니다. 11.06 시험에서는 사용자 창 조작 없이 마스터가 담당 6개에게 전달하고 결과를 회수했습니다.",
                },
              ],
            },
            {
              title: "개선할 위치를 잘못 기록했습니다",
              rows: [
                {
                  label: "근거",
                  text: "AI가 프로세스 개선 위치를 시험 프로젝트로 옮긴다고 기록했고, 제가 바로잡았습니다(11.04). 잘못된 해석으로 문서와 기록을 다시 쓰는 비용도 생겼습니다.",
                  ev: true,
                },
                {
                  label: "조치",
                  text: "개선 원본은 project-management로 유지하고, 시험 프로젝트에서 관리 이력과 PC 경로 참조를 지웠습니다. 정리 후 관리 프로젝트명과 개인 PC 경로 참조 0건을 확인했습니다.",
                },
              ],
            },
            {
              title: "실행 방식에 따라 AI 지침이 빠졌습니다",
              rows: [
                {
                  label: "근거",
                  text: "전용 시작기 대신 claude를 직접 실행한 세션에는 역할 지침과 보류 자료 읽기 차단이 적용되지 않았습니다.",
                  ev: true,
                },
                {
                  label: "위험",
                  text: "지침이 없는 상태로 반복 실행을 자동화하면 보류한 자료를 읽는 일을 막을 수 없습니다.",
                },
              ],
            },
            {
              title: "AI 문서 초안이 담당자를 잘못 적었습니다",
              rows: [
                {
                  label: "근거",
                  text: "11.02 Hermes 초안이 실제 실행 담당을 Hermes로 적었습니다. GPT가 근거와 대조해 반려했고 수정본을 다시 대조했습니다.",
                  ev: true,
                },
                {
                  label: "의미",
                  text: "만드는 쪽과 검증하는 쪽을 나눈 구조가 실제 오류를 잡은 사례입니다. 다만 Hermes도 GPT 계열이라 이 검토는 제공자 간 교차 검증이 아니라 별도 세션 검토입니다.",
                },
              ],
            },
            {
              title: "좁은 pane에서 긴 응답을 회수하지 못했습니다",
              rows: [
                {
                  label: "근거",
                  text: "11.06 시험에서 처음에는 오른쪽 pane 폭이 29~30칸이라 긴 응답의 앞부분이 회수되지 않았습니다.",
                  ev: true,
                },
                {
                  label: "조치",
                  text: "분할 비율을 조정하고, 검토 담당에게 자기 결과 파일 하나만 쓰도록 허용했습니다. 샘플 원본을 고칠 권한은 주지 않았습니다.",
                },
              ],
            },
          ],
        },
      ],
    },
    {
      id: "c2-next",
      title: "개선할 내용",
      blocks: [
        {
          type: "paragraph",
          text: "구조와 규칙은 갖췄지만 실제 모델을 연결한 전체 완주는 아직입니다.\n남은 작업은 시험 프로젝트에서 실행하고, 막히면 개선 원본으로 가져와 고칩니다.",
        },
        {
          type: "table",
          columns: ["상태", "개선 내용", "결과 또는 완료 기준"],
          rowHeader: false,
          rows: [
            [
              { status: "완료", tone: "done" },
              "개선 원본과 독립 시험 프로젝트 분리(11.04)",
              "시험 프로젝트에서 관리 프로젝트명·PC 경로 참조 0건. 모의 시험 46개 중 45개 통과(symlink 권한 부재 1개 제외)",
            ],
            [
              { status: "완료", tone: "done" },
              "위키를 내용별로 다시 정리(11.05)",
              "20개 문서, 원문 40개 항목 대응, 상대 링크 271개 누락 0. Obsidian 표시는 화면 캡처로 확인",
            ],
            [
              { status: "완료", tone: "done" },
              "herdr 마스터 1 + 담당 6 소규모 시험(11.06)",
              "실제 응답 회수, 형식 검사 오류 0, 독립 내용 검토 필수 결함 0. 같은 모델의 별도 세션 검토",
            ],
            [
              { status: "완료", tone: "done" },
              "시험 프로젝트에 위키 기준·스킬·위임 규칙 적용(11.06)",
              "위키 검사기 회귀 17건 통과, 기존 도구·시험 13개 파일 변경 없음(SHA-256 일치)",
            ],
            [
              { status: "다음", tone: "part" },
              "담당 제어 실검증: 명시 모델 → 새 탭 시작 → 최소 Task 전달",
              "시험 프로젝트 전달 도구의 실제 전달은 아직 실행하지 않음",
            ],
            [
              { status: "다음", tone: "part" },
              "기획 작성↔검토, 개발↔독립 QA 반복 검증",
              "별도 세션에서 실제 시험, 결함 반환, 수정, 재시험까지의 근거",
            ],
            [
              { status: "이후", tone: "plain" },
              "Hermes 문서화 연결과 전체 프로세스 완주",
              "작은 신규 명세 하나로 요구사항부터 문서화까지 단계별 근거 확보",
            ],
          ],
        },
      ],
    },
  ],
  footerLinks: [
    { label: "← CASE 01 상세 보기", href: "/cases/case-01" },
    { label: "CASE 03 상세 보기 →", href: "/cases/case-03", primary: true },
  ],
};
