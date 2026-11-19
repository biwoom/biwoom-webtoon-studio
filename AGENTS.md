# Biwoom Webtoon Studio 작업 규칙

## 경계와 소유권
유일한 작업 루트는 이 `AGENTS.md`가 위치한 `biwoom-webtoon-studio/` 디렉터리이다. 실행 시 이 위치의 실제 절대 경로를 확인하고 해당 루트 내부로 한정한다.
루트 밖 프로젝트와 기존 홈페이지 `biwoom/`는 탐색·읽기·수정하지 않는다. 경로 이탈과 심볼릭 링크를 통한 우회도 금지한다. 사용자 변경을 보존하고 변경 전에 상태를 확인한다.
사용자가 창작 총감독이며 교학 의미·대본·미술·G3.5 컷별 이미지/대사·G4 최종 회차 승인권을 갖는다. Dot은 기획·위임·검수 조정, Codex/엔진은 승인된 기술 실행을 맡는다.

## 승인과 보안
외부 공개, GitHub push, 삭제, 권한 확대, 유료 API·서비스는 해당 작업의 명시적 승인을 먼저 받는다. 과거 푸시 승인은 새 푸시의 포괄 승인이 아니다. 홈페이지 연동은 별도 요청 전 범위 밖이다.
API 비용 예산은 현재 미설정이며 이 P0에는 live/API 모드가 없다. 키·비밀·미공개 원고를 로그나 원격 저장소에 포함하지 않는다. 설치·네트워크 의존성을 임의 추가하지 않는다.
자동 QA나 합성 모의 승인은 사용자 승인이 아니다. 이미지/대사 변경은 영향받은 컷만 재승인 대상으로 삼고, 대사 변경만으로 이미지를 재생성하지 않는다. 미승인 미리보기와 최종 출력을 구분한다.

## 읽을 문서와 실행
먼저 설계서 v1.2, README, `.agents/context/current-state.md`를 읽는다. 설계 목표와 구현 상태를 구분한다.
루트에서 설치 없이:
```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m biwoom_studio --help
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m biwoom_studio demo
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -v
```
새 실행은 `output/mock-runs/` 내부 합성 자료만 생성하며 실제 작품은 입력받지 않는다. `qa-spike/`와 과거 `.studio-runs/` 산출물을 임의로 삭제·변경하지 않는다.
검증 시 실제 종료 코드·테스트 수·파일 재읽기·Git diff 범위를 확인한다. 작업 결과와 미구현 사항은 context에 기록하고 비밀 없는 실행 증거는 `.agents/logs/`에 둔다. 앱 경로 검사를 운영체제 전체 접근 격리로 과장하지 않는다.

## 제작 인계 보강
대본 뒤·원화 전 실제 시각 콘티를 만들고 기존 G3 승인을 받는다. YAML만으로 대신하지 않는다. `docs/workflow.md`와 해당 작품의 로컬 감사/연속성 기록(있는 경우)을 함께 확인한다. 로컬 절차 `.agents/skills/production-handoff/SKILL.md`는 권한 부여나 자동 연동 완료를 뜻하지 않는다.
G3.5는 정확한 이미지+대사 버전 조합의 인간 승인이고 G4는 회차 승인이다. 영향 컷만 재검토하며 이전 파일/승인 기록을 보존한다. 교학·미술 판단은 사용자에게 남긴다. status/preflight는 읽기 전용이고 차단 상태를 보여 줄 뿐 생성·릴리스를 허용하지 않는다. 파일럿 시험 종료 동의를 G4로 확대하지 않는다.
