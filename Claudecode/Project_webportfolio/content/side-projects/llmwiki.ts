import { FlowSideLlmwiki } from "@/components/case/flow-side-llmwiki";
import type { CaseData } from "@/content/cases/types";

// 문구 출처: prototype/portfolio-mockup.html 968-1139줄(#side1-detail)
export const llmwiki: CaseData = {
  slug: "llmwiki",
  head: {
    back: { label: "← Side Projects로 돌아가기", href: "/#p-side1" },
    eyebrow: "SIDE 01 · llmwiki 작업용 Slack 봇 · Hermes · llmwiki · qmd",
    title: "역할과 권한을 나눈 위키 봇을 만들었습니다",
    lead: "Slack에서 자료를 보내고 질문하면 서버의 에이전트가 저장하고, 정리하고, 찾아 답합니다.\n에이전트마다 맡는 일과 쓸 수 있는 권한을 나누고, 서버 메모리 안에서 검색까지 돌아가게 구성했습니다.",
    toc: [
      { id: "s1-overview", label: "개요" },
      { id: "s1-plan", label: "분석 및 계획" },
      { id: "s1-tree", label: "저장소 구조" },
      { id: "s1-flow", label: "프로세스" },
      { id: "s1-screens", label: "실제 화면" },
      { id: "s1-issue", label: "발생한 문제" },
      { id: "s1-next", label: "개선할 내용" },
    ],
    legend: [
      { badge: "확인", text: "서버 로그와 실행 기록에서 직접 봄" },
      { text: "수치 출처: project_hermes_test 작업기록(2026.11.11~11.18)" },
    ],
  },
  sections: [
    {
      id: "s1-overview",
      title: "개요",
      blocks: [
        {
          type: "paragraph",
          text: "자료를 모으고 다시 찾아 쓰는 일을 지시만으로 맡길 수 있는 개인 지식 창고가 필요해 시작했습니다.\n2026년 11월 11일 Hermes 에이전트 시험으로 출발해 11월 17일 서버 구성을 마쳤고, 11월 18일 위키 검색(qmd)을 붙였습니다.",
        },
        {
          type: "tiles",
          items: [
            { value: "3개", label: "역할별 에이전트(수집·리서치·정리)" },
            { value: "3개", label: "서버 컨테이너(에이전트, 위키 색인, 검색)" },
            { value: "10분", label: "에이전트가 커밋한 내용을 서버가 GitHub에 올리는 주기" },
            { value: "약 25초", label: "Slack 질문부터 위키 근거를 연 답변까지(11.18, 1건)" },
          ],
        },
        {
          type: "split",
          items: [
            {
              title: "제가 맡은 일",
              text: "목적과 역할 결정, 권한 경계(쓰기 담당·push 위치) 결정, 서버·Slack·GitHub 설정 실행, 결과를 서버 기록으로 다시 확인",
              highlight: true,
            },
            {
              title: "AI가 맡은 일",
              text: "Hermes 에이전트: 자료 저장, 위키 정리, 검색 후 답변 / Claude Code: 문서 조사, 구성 설계안, 스크립트 작성, 서버 시험",
            },
          ],
        },
      ],
    },
    {
      id: "s1-plan",
      title: "분석 및 계획",
      blocks: [
        {
          type: "paragraph",
          text: "첫 에이전트 하나로 Slack 연동 테스트를 시작했고, 자료를 모으는 일과 정리하는 일은 필요한 권한과 작업 범위를 세분화하는 것으로 가닥을 잡았습니다.\n그다음 위키를 바꿀 수 있는 담당과 GitHub에 올리는 주체를 정했습니다.",
        },
        { type: "heading", text: "구축 단계" },
        {
          type: "table",
          columns: ["날짜", "단계", "한 일"],
          rowHeader: true,
          rows: [
            ["11.11~12", "에이전트 시험", "Hermes를 설치해 메신저 대화와 웹 검색을 확인하고, 클라우드 서버(Docker)로 옮겼습니다."],
            ["11.13", "Slack 연동", "서버의 에이전트를 Slack에 연결하고, 목적을 역할별 에이전트 운영으로 정했습니다."],
            ["11.16", "역할 분리", "수집·리서치·정리 세 역할을 정하고, llmwiki를 PC에서 먼저 시험했습니다."],
            ["11.17", "서버 구성", "에이전트 3개, 위키 정리(llmwiki MCP), 자동 GitHub 반영을 서버에 올리고 첫 자료를 위키까지 반영했습니다."],
            ["11.18", "검색 강화", "한국어 임베딩 모델로 qmd 검색을 붙여, Slack 질문에 위키 근거로 답하는 것까지 확인했습니다."],
          ],
        },
        { type: "heading", text: "에이전트 역할" },
        {
          type: "table",
          columns: ["담당", "하는 일", "위키 권한", "스킬"],
          rowHeader: true,
          rows: [
            ["수집", "Slack으로 받은 URL의 원문을 raw로 저장", "없음", "raw-save, config-propose"],
            ["리서치", "모인 자료로 리서치와 인사이트 정리", "읽기", "wiki-search, config-propose"],
            ["정리", "raw를 위키 페이지로 정리, 주간 점검", "읽기·쓰기", "wiki-ingest, wiki-lint-weekly, wiki-search, config-propose"],
          ],
        },
        { type: "heading", text: "정한 기준" },
        {
          type: "table",
          columns: ["기준", "이유"],
          rowHeader: true,
          rows: [
            ["컨테이너 1개에 에이전트 프로필 3개", "Hermes 문서가 한 컨테이너에서 모든 프로필을 돌리도록 권장하고, 2GB 서버 메모리를 아낄 수 있습니다."],
            ["에이전트는 커밋까지만, push는 서버가 10분마다", "저장소 키는 브랜치를 제한할 수 없어, 키를 에이전트에게 주면 기준 브랜치(main)를 바꿀 수 있습니다."],
            ["설정 변경은 제안 브랜치로만", "에이전트가 자기 지침을 고치더라도 제가 검토하고 병합한 것만 서버에 반영됩니다."],
            ["검색은 별도 컨테이너의 qmd + KURE-v1", "위키 기본 검색은 조사가 붙은 한국어를 놓쳤고, 같은 조건에서 KURE-v1이 비교 모델보다 빨랐습니다."],
            ["색인 갱신은 하루 한 번 새벽", "색인하는 동안 검색이 멈추고 메모리를 많이 쓰기 때문에, 바뀐 문서가 있을 때만 돌립니다."],
          ],
        },
      ],
    },
    {
      id: "s1-tree",
      title: "저장소 구조",
      blocks: [
        {
          type: "paragraph",
          text: "자료와 설정을 저장소 두 개로 나눴습니다. 자료는 에이전트가 쌓고, 설정은 제가 검토한 것만 서버로 내려갑니다.",
        },
        {
          type: "tree",
          lines: [
            [{ bold: "llmwiki/" }, "                ", { note: "# 자료 저장소" }],
            ["├─ ", { bold: "raw/" }, "                 ", { note: "# 수집 담당이 저장한 원문" }],
            ["└─ ", { bold: "wiki/" }, "                ", { note: "# 정리 담당만 쓰는 위키 페이지(검색 대상)" }],
            [""],
            [{ bold: "agent-config/" }, "           ", { note: "# 봇 설정 저장소" }],
            ["├─ ", { bold: "souls/" }, "               ", { note: "# 에이전트별 정체성·경계·안전 규칙" }],
            ["├─ ", { bold: "skills/" }, "              ", { note: "# raw-save · wiki-ingest · wiki-lint-weekly" }],
            ["│                       ", { note: "#   wiki-search · config-propose" }],
            ["└─ ", { bold: "common/" }, "              ", { note: "# 형식 규약(서버에는 배치하지 않음)" }],
          ],
        },
      ],
    },
    {
      id: "s1-flow",
      title: "프로세스 순서도",
      blocks: [
        {
          type: "diagram",
          Flow: FlowSideLlmwiki,
          caption:
            "어두운 칸은 사용자입니다. 에이전트는 서버 안에서 커밋까지만 하고, GitHub에 올리는 일은 에이전트가 볼 수 없는 서버 쪽 작업이 맡습니다. 검색은 리서치·정리 담당이 씁니다.",
        },
        { type: "heading", text: "처리 순서" },
        {
          type: "steps",
          items: [
            { title: "1 자료 보내기", text: "Slack 수집 채널에 URL을 보내면 수집 담당이 원문을 raw로 저장하고 커밋합니다." },
            { title: "2 위키로 정리", text: "정리 담당이 새 raw를 읽고 위키 페이지를 만들거나 고친 뒤 커밋합니다." },
            { title: "3 자동 반영", text: "서버가 10분마다 새 커밋을 GitHub에 올립니다." },
            { title: "4 검색 후 답변", text: "질문을 받으면 qmd로 위키를 검색하고, 찾은 문서를 직접 열어 근거와 함께 답합니다.", highlight: true },
          ],
        },
      ],
    },
    {
      id: "s1-screens",
      title: "실제 화면",
      blocks: [
        { type: "paragraph", text: "이미지를 누르면 화면 가운데에 크게 열립니다." },
        {
          type: "shots",
          items: [
            {
              src: "/img/side01-url-ingest.png",
              alt: "Slack 스레드. URL을 보내자 수집 담당이 원문 저장 위치, 자료 ID, 커밋을 답한다",
              caption:
                "수집: Slack에 URL을 보내면 수집 담당이 원문을 저장하고 저장 위치, 자료 ID, 커밋을 답합니다.",
            },
            {
              src: "/img/side01-wiki-ingest.png",
              alt: "Slack 스레드. 주제 반영을 지시하자 정리 담당이 원문 대조 결과, 미반영 항목, Lint 결과, 커밋을 보고한다",
              caption:
                "정리: 주제를 지정해 위키 반영을 맡기면 정리 담당이 원문과 대조한 결과와 반영하지 못한 항목, Lint 결과, 커밋을 함께 보고합니다.",
            },
            {
              src: "/img/side01-obsidian-wiki.png",
              alt: "Obsidian에서 연 llmwiki 저장소. raw·wiki 폴더 구조와 정리된 EIGRP·OSPF·RIP 재분배 문서",
              caption:
                "결과: 정리된 위키 문서를 Obsidian에서 연 화면입니다. 원문(raw)과 정리본(wiki)을 나눠 두고, 문서마다 속성과 원문 출처를 남깁니다.",
              wide: true,
            },
          ],
        },
      ],
    },
    {
      id: "s1-issue",
      title: "발생한 문제",
      blocks: [
        {
          type: "issues",
          items: [
            {
              title: "봇 두 개가 갑자기 답하지 않았습니다",
              rows: [
                { label: "근거", text: "서버 로그에 토큰 만료 오류(token_expired)가 재시작 전까지 664건 반복됐습니다.", ev: true },
                { label: "원인", text: "Slack 앱 토큰이 12시간마다 만료되는 회전형이었고, 회전은 한 번 켜면 끌 수 없었습니다." },
                { label: "조치", text: "회전 없는 앱을 새로 만들어 토큰을 바꿨고, 이후 연결 오류는 0건이었습니다." },
                { label: "영향", text: "어느 봇에도 토큰 회전을 켜지 않는다는 운영 규칙을 남겼습니다." },
              ],
            },
            {
              title: "한국어로 검색하면 문서를 찾지 못했습니다",
              rows: [
                { label: "근거", text: "위키 기본 검색에서 “샌드박스”는 0건이고 “샌드박스가”처럼 조사가 붙은 원문 형태만 찾았습니다.", ev: true },
                { label: "원인", text: "위키 기본 검색 색인이 영어 기준으로 단어를 나눴습니다." },
                { label: "조치", text: "한국어 임베딩 모델을 쓰는 qmd를 붙여 키워드 검색과 의미 검색을 함께 쓰게 했습니다. 시험 질의 12개 중 키워드 검색은 11개에서 정답 문서를 찾았고, 의미 검색은 12개 모두 정답을 상위 3개 안에 넣었습니다." },
                { label: "한계", text: "위키 문서가 4개뿐인 상태의 시험이라 검색 순위 품질은 아직 판단할 수 없습니다." },
              ],
            },
            {
              title: "검색 모델이 서버 메모리를 밀어냈습니다",
              rows: [
                { label: "근거", text: "2GB 서버에서 첫 임베딩 시험 중 스왑이 316MB에서 586MB로 늘고, 에이전트 컨테이너 메모리가 밀려났습니다.", ev: true },
                { label: "원인", text: "임베딩 모델을 처음 올릴 때 메모리를 한 번에 많이 썼습니다." },
                { label: "조치", text: "중단 기준을 둔 별도 컨테이너에서 두 모델을 비교하고, 검색 서버는 700MB 한도로 상시 실행, 색인은 새벽에 1GB 일회용 컨테이너로 돌리며 여유 메모리가 900MB 미만이면 건너뛰게 했습니다." },
              ],
            },
            {
              title: "에이전트가 기준 브랜치를 직접 바꿀 수 있었습니다",
              rows: [
                { label: "근거", text: "저장소 키는 브랜치를 제한할 수 없고, 비공개 저장소에서는 GitHub 브랜치 보호 규칙도 적용되지 않았습니다.", ev: true },
                { label: "원인", text: "처음 계획은 에이전트 컨테이너에 저장소 키를 연결하는 것이었습니다." },
                { label: "조치", text: "키를 컨테이너 밖에 두고 서버 계정이 push하게 바꿨습니다. 컨테이너 안에서 push가 실패하는 것까지 확인했습니다." },
              ],
            },
          ],
        },
      ],
    },
    {
      id: "s1-next",
      title: "개선할 내용",
      blocks: [
        {
          type: "steps",
          items: [
            { title: "서버 메모리", text: "2GB 서버에 에이전트와 검색 서버가 함께 있어 빠듯합니다. 4GB 이상으로 늘릴지 검토합니다." },
            { title: "검색 품질", text: "위키 문서가 늘어난 뒤 검색 순위와 색인 시간을 다시 측정합니다." },
            { title: "자료 반영", text: "Notion에서 내보낸 문서를 위키 형식으로 옮기는 변환 스크립트를 만들고 소량부터 시험합니다." },
            { title: "수집 경로", text: "URL 저장에서 질문형 웹 검색, RSS 순서로 수집 경로를 넓히고, 최종적으로는 수집을 위한 자동화 파이프라인을 구축합니다.", highlight: true },
          ],
        },
      ],
    },
  ],
  footerLinks: [
    { label: "← Side Projects로 돌아가기", href: "/#p-side1" },
    { label: "AI Workflows 보기 →", href: "/#projects", primary: true },
  ],
};
