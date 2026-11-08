// Home 화면 문구. 값은 prototype/portfolio-mockup.html 310-423줄(#home, #how, #projects)에서 그대로 가져온다.
// 표기 규칙: <br> 줄바꿈은 문자열 안의 "\n"으로 표현하고 렌더링 쪽에서 나눈다.
// 따옴표(“ ”)와 화살표(→)는 문자 그대로 쓴다. HTML 엔티티는 쓰지 않는다.

export type Cta = { label: string; href: string };

export type HomeHero = {
  title: string; // "\n" = <br>
  actions: Cta[];
  hello: string;
  lead: string;
  sub: string; // "\n" = <br>
};

export type ProofItem = { value: string; label: string; href?: string };

export type SplitItem = { title: string; text: string };

export type Principle = {
  n: string;
  title: string;
  onSite: string; // 운영에서
  withAi: string; // AI와 함께
  link: Cta; // href는 Home 안의 카드 id(#p-case1 등)
};

export type CaseFlow = { problem: string; judgment: string; result: string };

export type CaseCard = {
  id: string; // 카드 id (p-case1 ...)
  tag: string;
  state: string;
  title: string;
  summary: string;
  flow: CaseFlow;
  learn: string;
  detailLabel: string;
  detailHref: string; // /cases/case-0N
  techTags: string[];
  image: {
    src: string; // 카드에 표시하는 이미지
    fullSrc: string; // 클릭 시 열리는 큰 이미지
    alt: string;
  };
};

export type TimelineItem = {
  time: string;
  title: string;
  text: string;
  evidence: Cta; // href는 Home 안의 카드 id
};

export type ReflectionCard = {
  id: string;
  tag: string;
  state: string;
  title: string;
  summary: string;
  timeline: TimelineItem[];
  current: SplitItem;
  next: SplitItem;
  learn: string;
};

export type HomeContent = {
  hero: HomeHero;
  proof: ProofItem[];
  how: {
    eyebrow: string;
    title: string;
    lead: string; // "\n" = <br>
    split: { me: SplitItem; ai: SplitItem };
    principles: Principle[];
  };
  projects: {
    eyebrow: string;
    title: string;
    lead: string; // "\n" = <br>
    cases: CaseCard[];
    reflection: ReflectionCard;
  };
};

export const home: HomeContent = {
  hero: {
    title: "AI가 만들고,\n기준은 제가 세웁니다",
    actions: [
      { label: "Working Style 보기", href: "#how" },
      { label: "AI Workflows 보기", href: "#projects" },
    ],
    hello: "안녕하세요, 유승철입니다",
    lead: "금융거래 플랫폼을 8년간 운영하며 익힌 확인과 기록의 습관으로 AI의 결과를 검토합니다.",
    sub: "퇴사 후 클라우드·네트워크 과정을 수강하며 진행하는 개인 학습입니다.\n이 프로젝트는 AI로 운영 프로세스를 강화하려고 제작했습니다.",
  },
  proof: [
    { value: "8년", label: "금융거래 플랫폼 서비스 운영" },
    {
      value: "4가지 기준",
      label: "AI Workflows에서 중요한 4가지 기준 →",
      href: "#how",
    },
    { value: "2026.09~", label: "간단한 프롬프트에서 시작해 진행 중" },
  ],
  how: {
    eyebrow: "Working Style",
    title: "운영에서 익힌 방식을 AI에게도 그대로 적용합니다",
    lead: "장애를 확인하고 기록할 때 처리하던 방식이 AI의 결과를 검토하는 기준이 됐습니다.\n각 방식을 실제 경험과 사례로 보여드립니다.",
    split: {
      me: {
        title: "제가 맡은 일",
        text: "프로세스 이슈 발견, 목표와 우선순위 설정, 결과 사용 및 검토, 변경 승인",
      },
      ai: {
        title: "AI가 맡은 일",
        text: "코드 작성·수정, 테스트 실행, 원인 분석, 문서 초안 작성",
      },
    },
    principles: [
      {
        n: "01",
        title: "완료는 보고가 아니라 근거로 판단합니다",
        onSite:
          "고객이 말한 문제를 프로세스, API 통신, 로그로 직접 좁혔고 주문 이슈는 서버 시세와 API 수신 데이터를 대조해 검증했습니다.",
        withAi:
          "게시 성공 보고에도 자료를 찾을 수 없어 완료 기준을 “홈에서 본문까지 읽기”로 바꿨고 가이드 작성은 검사 결과를 근거로 마무리하게 했습니다.",
        link: { label: "CASE 01 사용자 관점의 완료 기준 →", href: "#p-case1" },
      },
      {
        n: "02",
        title: "만드는 쪽과 검증하는 쪽을 나눕니다",
        onSite:
          "QA와 운영을 거치며 요구사항 확인, 테스트, 오류 전달, 수정 재검증, 릴리즈까지의 검증 과정을 맡았습니다.",
        withAi:
          "마스터 AI가 작성과 검토를 다른 담당에게 나눠 맡기고, 검토 담당은 원본을 고치지 않게 했습니다. 근거와 대조해 잘못 적힌 초안을 반려한 사례도 있습니다.",
        link: { label: "CASE 02 프로젝트 구조와 협업 방식 →", href: "#p-case2" },
      },
      {
        n: "03",
        title: "처리 기준을 정해 규칙과 도구로 바꿉니다",
        onSite:
          "주문 처리 큐 누적과 데이터 유실 장애가 반복되었을 때 확인 기준이 잘못되어 잘못 처리된 경험이 있었습니다. 우선 확인 항목과 대응 절차를 정리해 팀에 공유했습니다.",
        withAi:
          "제가 다시 지시한 내용을 살펴보니 처리 규칙이 모호했습니다. 처리 규칙을 분명히 정했고, 담당 AI의 모델을 매번 확인하던 일은 시작 전 검사와 훅으로 바꿔 해결했습니다.",
        link: { label: "CASE 03 비용과 검증 범위의 조정 →", href: "#p-case3" },
      },
      {
        n: "04",
        title: "기록하되, 확인한 것과 아닌 것을 나눕니다",
        onSite:
          "장애 내용과 해결 과정을 Telegram과 Wiki에 남겼고 고객에게는 확실하게 확인된 상황만 전달하고 조치 범위를 쉬운 말로 설명했습니다.",
        withAi:
          "새 세션이 작업기록만으로 이어받게 하고 보고에서는 확인과 미검증을 구분하게 했습니다.",
        link: {
          label: "REFLECTION 현재 위치와 다음 단계 →",
          href: "#p-reflection",
        },
      },
    ],
  },
  projects: {
    eyebrow: "AI 활용 개인 프로젝트",
    title: "AI에게 일을 맡기는 방식을 고쳐 온 기록",
    lead: "학습 자동화와 프로세스 개선 프로젝트에서 겪은 일을 세 가지 사례로 나눴습니다.\n완성된 서비스 소개가 아니라, 직접 쓰면서 이슈를 발견하고 AI의 결과를 검토한 과정입니다.",
    cases: [
      {
        id: "p-case1",
        tag: "CASE 01 · 사용자 관점의 완료 기준",
        state: "학습 자동화 · 2026.11.06 기준",
        title: "“올라갔는데, 왜 찾을 수 없을까?”",
        summary:
          "흩어진 학습 메모를 AI로 분석·분류하고 제가 확인한 뒤 Notion 지식베이스에 올리는 자동화입니다.",
        flow: {
          problem:
            "게시 성공 보고를 받았지만 홈과 해당 분야에서 자료를 찾을 수 없었습니다.",
          judgment:
            "완료 기준을 “홈 → 분야 → 본문 읽기”로 바꾸고 실제 동선까지 확인하게 했습니다.",
          result:
            "홈의 분야별 자료 수, 자료별 정리, 개념 찾아보기에서 본문까지 이어집니다.",
        },
        learn:
          "저장에 성공했는지보다 사용자가 실제로 찾아 읽을 수 있는지를 먼저 확인합니다.",
        detailLabel: "근거와 상세 내용 보기 →",
        detailHref: "/cases/case-01",
        techTags: ["Python", "Notion", "LLM 분석"],
        image: {
          src: "/img/case01-notion-home.png",
          fullSrc: "/img/case01-notion-home.png",
          alt: "Notion 홈 화면. 학습 분야 6개와 분야별 자료 수, 최근 학습자료 목록이 보인다.",
        },
      },
      {
        id: "p-case2",
        tag: "CASE 02 · 프로젝트 구조와 협업 방식",
        state: "프로세스 개선 · 2026.11.06 기준",
        title: "더 나은 구조에서, 더 나은 작업이 이어지도록",
        summary:
          "여러 AI가 함께 일할 때 누가 무엇을 맡고 결과를 어디에 남기는지 구조부터 나눈 사례입니다.",
        flow: {
          problem:
            "프롬프트와 결과를 제가 AI 사이에서 복사해 옮겼고, 개선할 곳과 시험할 곳의 기록이 섞이기 시작했습니다.",
          judgment:
            "개선 원본과 독립 시험 프로젝트를 나누고, 마스터 AI가 담당에게 전달하고 회수하도록 역할을 정했습니다.",
          result:
            "마스터 1개가 담당 6개에게 위키 작성과 검토를 나눠 맡긴 소규모 시험을 통과했습니다. 위키는 6개 분류로 다시 정리했습니다.",
        },
        learn: "맡을 사람과 기록할 곳이 정해져야 AI를 늘려도 일이 섞이지 않습니다.",
        detailLabel: "근거와 상세 내용 보기 →",
        detailHref: "/cases/case-02",
        techTags: ["Codex", "Claude Code", "Hermes", "herdr", "Obsidian", "Python"],
        image: {
          src: "/img/case02-herdr-parallel.png",
          fullSrc: "/img/case02-herdr-parallel.png",
          alt: "herdr 한 화면에 마스터 1개와 담당 6개의 터미널이 3열로 배치된 모습",
        },
      },
      {
        id: "p-case3",
        tag: "CASE 03 · 비용과 검증 범위의 조정",
        state: "프로세스 개선 · 2026.11.06 기준",
        title: "처리 기준을 먼저 세웠습니다",
        summary:
          "여러 AI에게 일을 맡기며 실행과 사용량이 늘어날 때, 무엇을 사람이 정하고 무엇을 규칙으로 처리할지 기준을 세운 사례입니다.",
        flow: {
          problem:
            "제가 같은 지시를 31번 다시 했고, 여러 AI 시험에서는 담당 6개가 모두 마스터용 모델로 실행됐습니다. 두 경우 모두 AI가 일을 어떻게 처리할지 기준이 모호했습니다.",
          judgment:
            "다시 지시한 내용을 살펴보니 처리 규칙이 모호했습니다. 비용·범위·공개 결정은 사람이 남기고, 나머지는 처리 규칙을 분명히 정하기로 했습니다.",
          result:
            "역할별 모델 규칙과 시작 전 검사를 적용해 담당 모델을 매번 확인하던 일을 없앴습니다. 마스터용 모델로 담당을 시작하면 훅이 실행 전에 막습니다.",
        },
        learn:
          "처리 기준이 분명하면 같은 지시를 반복하지 않아도 되고, 검증은 줄이지 않습니다.",
        detailLabel: "근거와 상세 내용 보기 →",
        detailHref: "/cases/case-03",
        techTags: ["모델 배분", "컨텍스트 관리", "훅", "작업 효율 리뷰"],
        image: {
          src: "/img/case03-card.png",
          fullSrc: "/img/case03-question-full.png",
          alt: "herdr 6담당 시험 결과 보고 뒤, 모든 모델을 Astra로 한 이유를 묻는 질문과 AI의 답변",
        },
      },
    ],
    reflection: {
      id: "p-reflection",
      tag: "REFLECTION · 현재 위치와 다음 단계",
      state: "2026.11.06 기준",
      title: "운영 경험을, 더 나은 질문과 검토로 연결합니다",
      summary:
        "세 사례 모두 AI의 보고를 그대로 받지 않고 던진 질문에서 방향이 바뀌었습니다. 그 질문들과 지금 위치를 정리했습니다.",
      timeline: [
        {
          time: "10.19",
          title: "게시가 끝났다는데, 왜 홈에서 찾을 수 없을까",
          text: "저장 성공만 검사하고 있었습니다. 완료 기준을 홈 → 분야 → 본문까지 읽기로 바꿨습니다.",
          evidence: { label: "CASE 01", href: "#p-case1" },
        },
        {
          time: "10.29",
          title: "제가 같은 말을 몇 번이나 반복하고 있을까",
          text: "코드 품질 대신 제 결정 지점과 비용을 기준으로 점검했습니다. 짧은 재지시 31건 중 약 16건은 규칙으로 없앨 수 있다고 봤습니다.",
          evidence: { label: "CASE 03", href: "#p-case3" },
        },
        {
          time: "11.04",
          title: "개선은 어디서 하고, 시험은 어디서 할까",
          text: "AI가 개선 위치를 시험 프로젝트로 옮긴다고 기록한 것을 바로잡고 두 프로젝트의 역할을 나눴습니다.",
          evidence: { label: "CASE 02", href: "#p-case2" },
        },
        {
          time: "11.06",
          title:
            "“현재 테스트이기때문에 모든 모델을 아스트라로 한거야? 아니면 정식 프로세스를 탔는데 아스트라로 작업지시한거야?”",
          text: "모델을 지정하지 않아 기본 설정을 이어받은 것이었습니다. 시험 결과를 바로잡아 기록하고 역할별 모델을 규칙과 시작 전 검사로 강제했습니다.",
          evidence: { label: "CASE 03", href: "#p-case3" },
        },
      ],
      current: {
        title: "현재 위치",
        text: "역할, 검증, 기록 위치를 나눈 구조와 담당 시작 검사를 갖췄습니다. 요구사항부터 문서화까지 한 번에 완주한 시험과 Claude·Hermes 실제 연결은 아직입니다.",
      },
      next: {
        title: "다음 단계",
        text: "독립 시험 프로젝트에서 작은 신규 명세 하나로 전체 과정을 완주하고, 막힌 곳은 개선 원본으로 가져와 고칩니다. 학습 자동화는 나머지 자료를 분석·게시합니다.",
      },
      learn:
        "더 나은 결과는 더 긴 프롬프트보다 완료 기준, 역할, 검증 근거를 먼저 물을 때 나왔습니다.",
    },
  },
};
