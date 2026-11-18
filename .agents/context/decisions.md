# P0 결정 기록 — 2026-11-18

- 사용자 승인: §5에 맞는 P0 기반 정리. 커밋·푸시·라이브 API는 이번 승인 범위 아님.
- 기존 stdlib 모의 구현을 폐기하지 않고 `src/biwoom_studio/`로 이동. 설치 없는 PYTHONPATH 실행 유지.
- 새 mock 실행은 `output/mock-runs/`로 분리; 기존 `.studio-runs/`와 qa-spike, 설계서는 그대로 보존.
- 실제 작품 데이터/P1, live 생성, 렌더링, 사용자 승인 UI, G4 릴리스는 미구현. 미래 폴더를 모두 빈 상태로 만들지 않음.
- 승인 해시는 현재 marker 바이트·대사에 묶이며 테스트 주체는 SYNTHETIC_TEST_NOT_USER. 실제 사용자 승인 아님.
