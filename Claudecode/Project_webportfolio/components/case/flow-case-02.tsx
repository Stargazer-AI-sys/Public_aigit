// CASE 02 프로세스 순서도. 목업 prototype/portfolio-mockup.html 679-705줄의 인라인 SVG를 옮긴 것.
// 칸·글자 클래스(.box .me .t .s .me-t .me-s .lb)는 case-sections.tsx가 색을 입힌다.
export function FlowCase02() {
  return (
    <svg
      viewBox="0 0 960 268"
      role="img"
      aria-label="요구사항 승인에서 완료 판정까지 여섯 단계. 기획과 개발에는 각각 검토와 독립 QA 반복이 있고, 같은 결함이 반복되면 마스터가 재평가한다."
    >
      <defs>
        <marker
          id="arrow-p"
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
        <rect className="box me" x="4" y="28" width="134" height="88" rx="14" />
        <text className="me-t" x="71" y="60">요구사항 승인</text>
        <text className="me-s" x="71" y="81">사용자</text>
        <text className="me-s" x="71" y="98">범위·완료 기준</text>
        <rect className="box" x="168" y="28" width="134" height="88" rx="14" />
        <text className="t" x="235" y="60">기획</text>
        <text className="s" x="235" y="81">Codex 작성</text>
        <text className="s" x="235" y="98">Claude 검토</text>
        <rect className="box" x="332" y="28" width="134" height="88" rx="14" />
        <text className="t" x="399" y="60">개발</text>
        <text className="s" x="399" y="81">Claude 제작</text>
        <text className="s" x="399" y="98">자체 시험</text>
        <rect className="box" x="496" y="28" width="134" height="88" rx="14" />
        <text className="t" x="563" y="60">독립 QA</text>
        <text className="s" x="563" y="81">별도 세션</text>
        <text className="s" x="563" y="98">실제 사용 시험</text>
        <rect className="box" x="660" y="28" width="134" height="88" rx="14" />
        <text className="t" x="727" y="60">문서화</text>
        <text className="s" x="727" y="81">Hermes 초안</text>
        <text className="s" x="727" y="98">마스터 근거 대조</text>
        <rect className="box me" x="824" y="28" width="132" height="88" rx="14" />
        <text className="me-t" x="890" y="60">완료 판정</text>
        <text className="me-s" x="890" y="81">마스터 보고</text>
        <text className="me-s" x="890" y="98">사용자 확인</text>
      </g>
      <g fill="none" stroke="currentColor" strokeWidth="1.6">
        <path d="M138 72H166" markerEnd="url(#arrow-p)" />
        <path d="M302 72H330" markerEnd="url(#arrow-p)" />
        <path d="M466 72H494" markerEnd="url(#arrow-p)" />
        <path d="M630 72H658" markerEnd="url(#arrow-p)" />
        <path d="M794 72H822" markerEnd="url(#arrow-p)" />
        <path d="M563 116V150H399V118" markerEnd="url(#arrow-p)" />
        <path d="M481 150V190" strokeDasharray="5 4" markerEnd="url(#arrow-p)" />
      </g>
      <text className="lb" x="481" y="142" textAnchor="middle">결함이면 수정 후 재검증</text>
      <text className="lb" x="727" y="138" textAnchor="middle">내용 불일치면 반려·수정</text>
      <rect className="box" x="331" y="192" width="300" height="60" rx="14" />
      <text className="t" x="481" y="216">마스터 재평가</text>
      <text className="s" x="481" y="238">같은 결함이 2회 수정 후 반복되거나 검토 3회 초과</text>
    </svg>
  );
}
