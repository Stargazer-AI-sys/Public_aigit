// SIDE 01(llmwiki) 프로세스 순서도. prototype/portfolio-mockup.html 1049-1085줄의 인라인 SVG를 옮겼다.
// 색은 case-sections.tsx가 클래스 이름(.box .on .me .t .s .me-t .me-s .lbh .lb)에 입힌다.
export function FlowSideLlmwiki() {
  return (
    <svg
      viewBox="0 0 960 280"
      role="img"
      aria-label="Slack 요청이 Hermes 컨테이너의 수집·리서치·정리 담당에게 가고, 수집은 raw에, 정리는 wiki에 커밋한다. 리서치와 정리는 qmd로 위키를 검색한다. 서버가 10분마다 커밋을 GitHub에 올린다."
    >
      <defs>
        <marker
          id="arrow-l"
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
      <rect className="box me" x="4" y="96" width="120" height="88" rx="14" />
      <text className="me-t" x="64" y="132">Slack</text>
      <text className="me-s" x="64" y="153">URL 전달 · 질문</text>
      <rect className="box" x="160" y="16" width="250" height="248" rx="18" />
      <text className="lbh" x="180" y="42">Hermes 컨테이너</text>
      <rect className="box" x="180" y="56" width="210" height="54" rx="12" />
      <text className="t" x="285" y="79">수집 담당</text>
      <text className="s" x="285" y="98">원문을 raw로 저장</text>
      <rect className="box" x="180" y="124" width="210" height="54" rx="12" />
      <text className="t" x="285" y="147">리서치 담당</text>
      <text className="s" x="285" y="166">리서치 · 인사이트</text>
      <rect className="box" x="180" y="192" width="210" height="54" rx="12" />
      <text className="t" x="285" y="215">정리 담당</text>
      <text className="s" x="285" y="234">위키 정리 · 주간 점검</text>
      <text className="lbh" x="480" y="42">llmwiki 저장소 · 검색</text>
      <rect className="box" x="480" y="56" width="150" height="54" rx="12" />
      <text className="t" x="555" y="79">raw/</text>
      <text className="s" x="555" y="98">수집 원문</text>
      <rect className="box on" x="480" y="124" width="150" height="54" rx="12" />
      <text className="t" x="555" y="147">qmd 검색</text>
      <text className="s" x="555" y="166">KURE-v1 · 읽기 전용</text>
      <rect className="box" x="480" y="192" width="150" height="54" rx="12" />
      <text className="t" x="555" y="215">wiki/</text>
      <text className="s" x="555" y="234">정리된 페이지</text>
      <rect className="box on" x="676" y="96" width="132" height="88" rx="14" />
      <text className="t" x="742" y="132">서버 자동 push</text>
      <text className="s" x="742" y="153">10분마다 · 에이전트 밖</text>
      <rect className="box" x="840" y="96" width="116" height="88" rx="14" />
      <text className="t" x="898" y="132">GitHub</text>
      <text className="s" x="898" y="153">자료 저장소</text>
      <g fill="none" stroke="currentColor" strokeWidth="1.6">
        <path d="M124 140H158" markerEnd="url(#arrow-l)" />
        <path d="M390 83H478" markerEnd="url(#arrow-l)" />
        <path d="M390 219H478" markerEnd="url(#arrow-l)" />
        <path d="M410 151H478" strokeDasharray="5 4" markerEnd="url(#arrow-l)" />
        <path d="M555 192V180" strokeDasharray="5 4" markerEnd="url(#arrow-l)" />
        <path d="M630 83H652V219H630M652 140H674" markerEnd="url(#arrow-l)" />
        <path d="M808 140H838" markerEnd="url(#arrow-l)" />
      </g>
      <text className="lb" x="420" y="76">커밋</text>
      <text className="lb" x="420" y="143">검색</text>
      <text className="lb" x="406" y="212">커밋(MCP)</text>
      <text className="lb" x="566" y="191">색인</text>
    </svg>
  );
}
