// CASE 03 프로세스 순서도. prototype/portfolio-mockup.html 861-883줄의 인라인 SVG를 옮겼다.
// 색은 case-sections.tsx가 클래스 이름(.box .on .me .t .s .me-t .me-s .lb)에 입힌다.
export function FlowCase03() {
  return (
    <svg
      viewBox="0 0 960 250"
      role="img"
      aria-label="작업 승인, 모델 명시, 시작 전 검사, 새 탭에서 시작, Task 전달의 다섯 단계. 훅이 금지된 모델의 담당 시작 명령을 실행 전에 막는다."
    >
      <defs>
        <marker
          id="arrow-c"
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
      <g>
        <rect className="box me" x="4" y="28" width="170" height="88" rx="14" />
        <text className="me-t" x="89" y="60">작업 승인</text>
        <text className="me-s" x="89" y="81">사용자</text>
        <text className="me-s" x="89" y="98">범위·비용</text>
        <rect className="box" x="196" y="28" width="170" height="88" rx="14" />
        <text className="t" x="281" y="60">모델 명시</text>
        <text className="s" x="281" y="81">마스터가 지정</text>
        <text className="s" x="281" y="98">Luna 또는 Terra</text>
        <rect className="box on" x="388" y="28" width="170" height="88" rx="14" />
        <text className="t" x="473" y="60">시작 전 검사</text>
        <text className="s" x="473" y="81">누락·금지 모델</text>
        <text className="s" x="473" y="98">시작 거부</text>
        <rect className="box" x="580" y="28" width="170" height="88" rx="14" />
        <text className="t" x="665" y="60">새 탭에서 시작</text>
        <text className="s" x="665" y="81">담당 전용 탭</text>
        <text className="s" x="665" y="98">실제 모델·권한 확인</text>
        <rect className="box" x="772" y="28" width="184" height="88" rx="14" />
        <text className="t" x="864" y="60">Task 전달</text>
        <text className="s" x="864" y="81">확인 뒤에만</text>
        <text className="s" x="864" y="98">필요한 입력만</text>
      </g>
      <g fill="none" stroke="currentColor" strokeWidth="1.6">
        <path d="M174 72H194" markerEnd="url(#arrow-c)" />
        <path d="M366 72H386" markerEnd="url(#arrow-c)" />
        <path d="M558 72H578" markerEnd="url(#arrow-c)" />
        <path d="M750 72H770" markerEnd="url(#arrow-c)" />
        <path d="M665 170V120" strokeDasharray="5 4" markerEnd="url(#arrow-c)" />
      </g>
      <rect className="box on" x="480" y="172" width="370" height="60" rx="14" />
      <text className="t" x="665" y="196">PreToolUse 훅</text>
      <text className="s" x="665" y="218">금지된 모델의 담당 시작 명령을 실행 전에 차단</text>
      <text className="lb" x="466" y="207" textAnchor="end">보조 장치: 모든 우회를 막지는 않음</text>
    </svg>
  );
}
