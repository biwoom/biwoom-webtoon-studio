# Biwoom Studio P0: local synthetic prototype

설계서 v1.2의 전체 구현이 아닌 **합성 2컷 승인 게이트 실험용** Python 표준 라이브러리 뼈대입니다. 실제 이미지 생성·렌더링·교학 검수·실사용자 승인·G4 릴리스는 구현하지 않았습니다. 네트워크, API, 라이브 모드, 설치가 없습니다.

## 실행
Studio 루트에서 Python 3.9 이상으로 실행합니다. 설계의 목표 환경은 3.12+이며 이 작은 프로토타입은 3.9+ 문법만 사용합니다.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m biwoom_studio demo
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -v
```

첫 명령 하나로 새 합성 후보 → 미승인 검토 미리보기 → **테스트용 모의 승인** → 로컬 JSON 모의 조판을 재현합니다. 실행마다 고유 `output/mock-runs/mock-*` 경로를 출력하며 기존 실행 파일을 덮어쓰거나 지우지 않습니다. 테스트 결과물도 보존하므로 디스크 사용량은 실행 수에 따라 늘어납니다.

## 역할별 위치 (각 실행 폴더 내부)
- `source/storyboard.json`: 합성 대사·콘티. `expected.json`: 독립 필수 컷/출처 원장 설명 사본. 실제 검증 기준은 코드의 고정 합성 원장입니다.
- `candidates/*.marker`: 이미지가 아닌 합성 이미지 마커 바이트.
- `approvals/*.json`: 컷 ID·현재 마커 파일 SHA256·대사 SHA256·테스트 주체·UTC 시각. 실제 사용자의 G3.5 승인이 아닙니다.
- `preview/review.json`: 미승인 항목을 포함하고 그 상태를 표시한 검토 전용 결과. demo에서는 승인 이전 스냅샷을 보존합니다.
- `export/mock-layout.json`: 승인 바인딩 재검증을 통과한 경우만 생성하는 JSON. 실제 이미지나 최종 회차 릴리스가 아닙니다.

모의 자동 승인은 코드에 고정된 정확한 합성 2컷과 마커만 허용합니다. 임의 프로젝트를 읽거나 승인하는 CLI는 없습니다. 조판 직전에 현재 파일 바이트와 대사를 다시 해시하므로 대사/이미지 변경은 해당 컷만 무효화합니다. 대사 수정은 이미지 변경을 일으키지 않습니다. 자동 QA와 사용자 승인, G3.5와 G4는 향후 실제 구현에서도 별개여야 합니다.

경로는 지정 루트 내부만 허용하고 `..`, 절대경로, 심볼릭 링크를 거부합니다. 이는 앱 수준 검사이며 운영체제 샌드박스나 동시 악의적 파일 교체 방어를 대신하지 않습니다. 라이브러리 내부 함수는 신뢰된 로컬 테스트용이며 보안 경계가 아닙니다.

`docs/`와 이전 `qa-spike/`는 변경하지 않습니다. `output/`은 로컬 생성물로 Git에서 제외합니다. 과거 `.studio-runs/`와 `qa-spike/`는 변경 없이 보존합니다. 커밋·푸시는 별도 승인 전 수행하지 않습니다.

## P0 설계 경로 정리

- `src/biwoom_studio/cli.py`: 실제 CLI, `__main__.py`: 모듈 실행 진입점. 루트는 `core.py`에서 `parents[2]`로 고정하며 외부 루트·경로 이탈·심볼릭 링크를 거부합니다.
- `tests/integration/`: 기존 9개 게이트 테스트, `tests/unit/`: 루트·경로 3개 테스트. 재귀 discovery를 위한 `__init__.py`가 있습니다.
- `tests/fixtures/`: 합성 fixture 설명. 현재 고정 fixture 상수는 core.py에 있고 실제 테스트 데이터는 실행별로 생성됩니다.
- `AGENTS.md`, `.agents/context/`: 범위·현재 상태·결정·작업 기록. `.agents/logs/`: 로컬 감사 증거(생성 로그는 Git 제외).
- 새로운 합성 실행만 `output/mock-runs/`에 둡니다. 그 아래 source/candidates/approvals/preview/export 구분은 테스트용 대응이며, 실제 작품의 `stories/ST-001/` 구조가 아닙니다.
- 기존 실행 산출물은 이동·삭제하지 않았습니다. `.env.example`, config, assets, stories, 세분화된 엔진 모듈, acceptance 테스트는 관련 기능 구현 시 추가합니다. 빈 미래 폴더로 구현을 가장하지 않습니다.
- pyproject의 `studio` entry point는 설치 시 사용할 선언입니다. 현재 검증된 실행은 위 PYTHONPATH 명령이며 설치·패키징 검증은 하지 않았습니다.
