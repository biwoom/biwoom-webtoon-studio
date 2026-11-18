# 현재 상태 — 2026-11-18

P0 기반 경로 정리 완료. `src/biwoom_studio/cli.py`, AGENTS.md, context/logs, tests/integration·unit·fixtures가 존재한다. 설치 없이 CLI help, 합성 2컷 demo, 기존 9개와 루트 경계 3개를 포함한 12개 테스트가 실제 통과했다.
검증 증거: `.agents/logs/p0-foundation-verification.json`.
설계서와 qa-spike·과거 .studio-runs 파일/링크 해시·대상은 변경 전후 동일 확인. 이 작업은 커밋/푸시하지 않았다.

## 실제 가능한 것
고정 합성 marker 후보 → 미승인 검토 JSON → 명시적 mock-only 승인 기록 → 해시 재검증 후 mock layout JSON. 경로·누락 컷·출처 역할·승인 누락/스테일 검증. 앱 수준 경로 검사이며 OS 샌드박스 보장은 아님.

## 아직 계획인 것
P1의 실제 10컷/출전/YAML 스키마, config·assets·stories, 세부 엔진 모듈, 실제 이미지 API·비용/권리 게이트, 시각/교학 QA, 실제 G3.5 사용자 승인·G4, 렌더링·PNG/WebP/HTML/ZIP, 중단 재개·실제 자동 감독 연동. 현재 합성 실험을 해당 기능 완료로 표시하지 않는다.
환경 권한은 작업별 확인이 필요하며 CLI 성공이 Dot→Codex 자동 위임 전체 검증을 뜻하지 않는다.
