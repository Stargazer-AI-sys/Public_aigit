# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 목적
(2026-11-13 변경) 역할별 Hermes 인스턴스를 만들고 관리하며 여러 서버에 배포하는 프로세스를 구축한다.
이전 목적은 hermes 유용성 평가였고, 그 기록은 WORK_LOG.md에 이력으로 남아 있다.
산출물은 `deploy/`의 스크립트·템플릿(`hermes-agent.sh`, `compose.yaml`, `bootstrap.sh`)과 `agents/`·`targets/` 예시 설정이다.

## 구조 원칙
- 인스턴스 1개 = 컨테이너 1개 + 데이터 폴더 1개 + 봇 토큰 1개. 인스턴스끼리 데이터 폴더나 봇 토큰을 공유하지 않는다.
- 비밀값(봇 토큰, 로그인, 백업 파일)은 repo에 두지 않는다. `agents/*.env`, `targets/*.env`, `backups/`는 gitignore 대상이다.
- 서버 기준은 Ubuntu 24.04 + SSH 접속 가능이다. 서버 생성 자동화(IaC)는 범위 밖이다.

## 기록 원칙
- 스크립트·절차는 직접 실행해 확인한 사실로만 기록한다. 실행하지 않은 것은 "미확인"으로 구분한다.
- 이 프로젝트의 설치·실행 결과를 다른 프로젝트나 PC의 사실로 일반화하지 않는다.

## 실행 환경
- hermes 설치 명령(Windows PowerShell): `iex (irm https://hermes-agent.nousresearch.com/install.ps1)`
- 실행: `hermes`
- 모델: gpt-6-luna. ChatGPT 구독 방식으로 연결했고, 2026-11-11 사용량이 구독에서 차감되는 것을 사용자가 확인했다.
- 웹 검색: 별도 설정 없이 동작했다. 날씨·뉴스 3건을 출처 링크와 함께 받았다(2026-11-11).

## 작업 규칙
- 유료 API 호출, 외부 서비스 전송, commit·push는 사용자 요청이 있을 때만 한다.
- 작업기록은 `work-log` 스킬로 작업 종료 시 한 번에 정리한다.
