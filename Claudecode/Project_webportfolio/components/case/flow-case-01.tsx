// CASE 01 프로세스 순서도. prototype/portfolio-mockup.html 497-528줄의 인라인 SVG를 옮긴 것.
// 클래스 이름(.box .on .me .todo .t .s .me-t .me-s .lb .lbh)은 목업 그대로 두고, 색은 case-sections.tsx가 입힌다.
export function FlowCase01() {
  return (
    <svg
      viewBox="0 0 960 300"
      role="img"
      aria-label="기존 프로그램은 수집, 분석, 분류, 승인, 게시 준비, 게시, 화면 확인의 일곱 단계이고, 재설계는 승인 단계를 없애 미리보기 확인으로 대신한다."
    >
      <defs>
        <marker
          id="arrow-s"
          viewBox="0 0 10 10"
          refX="9"
          refY="5"
          markerWidth="7"
          markerHeight="7"
          orient="auto-start-reverse"
        >
          <path d="M0 0 10 5 0 10z" fill="currentColor" />
        </marker>
      </defs>
      <text className="lbh" x="4" y="18">
        기준 프로그램 (Project-StudyAutomanage)
      </text>
      <g>
        <rect className="box" x="4" y="30" width="118" height="74" rx="12" />
        <text className="t" x="63" y="60">원본 수집</text>
        <text className="s" x="63" y="82">해시로 변경 감지</text>
        <rect className="box" x="142" y="30" width="118" height="74" rx="12" />
        <text className="t" x="201" y="60">AI 분석</text>
        <text className="s" x="201" y="82">형식·근거 검사</text>
        <rect className="box" x="280" y="30" width="118" height="74" rx="12" />
        <text className="t" x="339" y="60">학습 분류</text>
        <text className="s" x="339" y="82">CCNA 6분야</text>
        <rect className="box me" x="418" y="30" width="118" height="74" rx="12" />
        <text className="me-t" x="477" y="60">사용자 승인</text>
        <text className="me-s" x="477" y="82">승인 또는 보류</text>
        <rect className="box" x="556" y="30" width="118" height="74" rx="12" />
        <text className="t" x="615" y="60">게시 준비</text>
        <text className="s" x="615" y="82">변경분·미리보기</text>
        <rect className="box" x="694" y="30" width="118" height="74" rx="12" />
        <text className="t" x="753" y="60">Notion 게시</text>
        <text className="s" x="753" y="82">채팅 AI가 중계</text>
        <rect className="box on" x="832" y="30" width="124" height="74" rx="12" />
        <text className="t" x="894" y="60">화면 확인</text>
        <text className="s" x="894" y="82">홈→분야→본문</text>
      </g>
      <g fill="none" stroke="currentColor" strokeWidth="1.6">
        <path d="M122 67H140" markerEnd="url(#arrow-s)" />
        <path d="M260 67H278" markerEnd="url(#arrow-s)" />
        <path d="M398 67H416" markerEnd="url(#arrow-s)" />
        <path d="M536 67H554" markerEnd="url(#arrow-s)" />
        <path d="M674 67H692" markerEnd="url(#arrow-s)" />
        <path d="M812 67H830" markerEnd="url(#arrow-s)" />
      </g>
      <text className="lbh" x="4" y="150">
        간소화 재설계 (Project_Refactor, 시험 중)
      </text>
      <g>
        <rect className="box" x="4" y="162" width="118" height="74" rx="12" />
        <text className="t" x="63" y="192">자료 선택</text>
        <text className="s" x="63" y="214">해시로 상태 판정</text>
        <rect className="box" x="142" y="162" width="118" height="74" rx="12" />
        <text className="t" x="201" y="192">AI 분석 1회</text>
        <text className="s" x="201" y="214">자동 재시도 없음</text>
        <rect className="box" x="280" y="162" width="118" height="74" rx="12" />
        <text className="t" x="339" y="192">분류 포함</text>
        <text className="s" x="339" y="214">분류표에서 선택</text>
        <rect className="box todo" x="418" y="162" width="118" height="74" rx="12" />
        <text className="s" x="477" y="192">승인 단계</text>
        <text className="s" x="477" y="214">제거</text>
        <rect className="box me" x="556" y="162" width="118" height="74" rx="12" />
        <text className="me-t" x="615" y="192">미리보기 확인</text>
        <text className="me-s" x="615" y="214">사용자</text>
        <rect className="box" x="694" y="162" width="118" height="74" rx="12" />
        <text className="t" x="753" y="192">Notion 게시</text>
        <text className="s" x="753" y="214">파일명으로 갱신</text>
        <rect className="box on" x="832" y="162" width="124" height="74" rx="12" />
        <text className="t" x="894" y="192">결과 기록</text>
        <text className="s" x="894" y="214">중복 페이지 없음</text>
      </g>
      <g fill="none" stroke="currentColor" strokeWidth="1.6">
        <path d="M122 199H140" markerEnd="url(#arrow-s)" />
        <path d="M260 199H278" markerEnd="url(#arrow-s)" />
        <path d="M398 199H408V262H546V199H554" markerEnd="url(#arrow-s)" />
        <path d="M674 199H692" markerEnd="url(#arrow-s)" />
        <path d="M812 199H830" markerEnd="url(#arrow-s)" />
      </g>
      <text className="lb" x="477" y="282" textAnchor="middle">
        승인 대신 미리보기로 바로 이동
      </text>
    </svg>
  );
}
