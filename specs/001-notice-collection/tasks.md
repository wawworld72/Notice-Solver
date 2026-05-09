---
description: "Task list for 전체 공지사항 수집 시스템"
---

# Tasks: 전체 공지사항 수집 시스템

**Input**: `specs/001-notice-collection/` (plan.md, spec.md, data-model.md, contracts/cli.md)
**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ contracts/ ✅

**⚠️ TDD REQUIRED (헌법 원칙 III — NON-NEGOTIABLE)**
각 User Story 구현 태스크 전 테스트를 먼저 작성하고 RED 확인 후 구현합니다.

**Organization**: US1→US2→US3 순서로 각 스토리가 독립적으로 테스트 가능합니다.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: 병렬 실행 가능 (다른 파일, 의존성 없음)
- **[Story]**: 해당 User Story ([US1]~[US6])
- 모든 태스크에 정확한 파일 경로 포함

## Path Conventions

- 소스: `src/notice_solver/`
- 테스트: `tests/unit/`, `tests/integration/`, `tests/contract/`

---

## Phase 1: Setup (프로젝트 초기화)

**Purpose**: Python 패키지 구조 및 기본 설정 파일 생성

- [ ] T001 `pyproject.toml` 생성 — 의존성(httpx, beautifulsoup4, lxml, easyocr, pdfplumber, python-docx, openpyxl, ghapi, python-frontmatter, typer[all], pydantic-settings, tenacity), CLI entrypoint(`notice-solver = "notice_solver.cli.main:app"`), dev 의존성(pytest, pytest-asyncio, respx), hatchling 빌드 백엔드
- [ ] T002 [P] 소스 디렉토리 구조 생성 — `src/notice_solver/{cli,crawlers,parsers,ocr,github,models,cache}/__init__.py` 전체
- [ ] T003 [P] `tests/` 디렉토리 구조 생성 — `tests/{unit,integration,contract}/__init__.py` 전체
- [ ] T004 [P] `.env.example` 생성 — `GITHUB_TOKEN`, `GITHUB_REPO_OWNER`, `GITHUB_REPO_NAME`, `DEFAULT_BOARD_ID`, `RETRY_COUNT=3`, `REQUEST_DELAY_SEC=1.0`, `OCR_BATCH_LIMIT=50`, `OCR_CONFIDENCE_THRESHOLD=0.5`, `LOG_DIR=./logs`, `CACHE_DIR=./.cache`
- [ ] T005 [P] `.gitignore` 생성 — `.env`, `.cache/`, `logs/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `dist/`, `*.egg-info/`

---

## Phase 2: Foundational (공통 인프라 — 모든 User Story의 전제)

**Purpose**: 모든 User Story가 공유하는 모델·캐시·GitHub 연동 레이어
**⚠️ CRITICAL**: 이 단계 완료 전 어떤 User Story도 시작할 수 없음

- [ ] T006 `src/notice_solver/config.py` 구현 — `pydantic-settings` 기반 `Settings` 클래스: github_token, github_repo_owner, github_repo_name, default_board_id, retry_count(=3), request_delay_sec(=1.0), ocr_batch_limit(=50), ocr_confidence_threshold(=0.5), log_dir, cache_dir; `.env` 자동 로딩
- [ ] T007 [P] `src/notice_solver/models/notice.py` 구현 — `Notice` 데이터클래스: source_id, board_id, notice_id, title, body_text, source_url, published_at, crawled_at, author, image_urls(list), attachments(list[AttachmentRef]), github_issue_number, phase; `AttachmentRef` 데이터클래스: url, filename, mime_type
- [ ] T008 [P] `src/notice_solver/models/asset.py` 구현 — `Asset` 데이터클래스: asset_id, parent_notice_id, parent_issue_number, type(Literal["image","attachment"]), sequence, total_in_notice, src_url, full_url, filename, mime_type, ocr_status(="raw"), ocr_text, ocr_confidence, ocr_processed_at, github_issue_number
- [ ] T009 [P] `src/notice_solver/models/crawl_run.py` 구현 — `CrawlRun` 데이터클래스: run_id, pipeline, board_id, started_at, finished_at, processed, skipped, failed, errors(list[dict]); `to_json()`·`report()` 메서드 (파이프라인별 완료 통계 출력)
- [ ] T010 `src/notice_solver/cache/index.py` 구현 — `NoticeIndex`, `AssetIndex` 클래스: JSON 파일 기반 O(1) 중복 확인; `exists(id)`, `add(id, issue_number)`, `load()`, `save()` 메서드; `.cache/notice-index.json`, `.cache/asset-index.json` 경로
- [ ] T011 `src/notice_solver/github/frontmatter.py` 구현 — `parse_notice_meta(body: str) -> dict`, `render_notice_body(notice: Notice) -> str`, `parse_asset_meta(body: str) -> dict`, `render_asset_body(asset: Asset) -> str`; HTML 주석 블록(`<!-- NOTICE_META ... -->`) 형식
- [ ] T012 `src/notice_solver/github/labels.py` 구현 — `LABEL_DEFINITIONS` 상수(phase:*, type:asset, asset:*, status:*, board:*, category:*, year:*, semester:*, has:* 전체 레이블 색상 포함); `ensure_labels(api, owner, repo)` — 누락된 레이블 일괄 생성
- [ ] T013 `src/notice_solver/github/issues.py` 구현 — `GitHubIssues` 클래스: `create_notice_issue(notice)`, `update_notice_issue(number, body, labels)`, `create_asset_issue(asset)`, `update_asset_issue(number, ocr_text, status)`, `list_issues(labels, state, limit)`, `get_issue(number)`; `ghapi` 사용, rate limit 대응(429 시 자동 대기)
- [ ] T014 `tests/conftest.py` 구현 — pytest 픽스처: `cli_runner`(typer CliRunner), `mock_settings`(테스트용 Settings), `mock_github_api`(ghapi mock), `sample_notice`(Notice 픽스처), `sample_asset`(Asset 픽스처), `tmp_cache_dir`(임시 .cache 디렉토리)

**Checkpoint**: 공통 인프라 완료 — User Story 구현 시작 가능

---

## Phase 3: User Story 1 - 공지 텍스트 수집 (Priority: P1) 🎯 MVP

**Goal**: 게시판 크롤링 → 공지 텍스트 추출 → GitHub Issue 생성 (이미지·첨부는 URL 기록만)
**Independent Test**: `notice-solver collect --dry-run` 실행 시 수집 예정 공지 목록 출력, `notice-solver collect` 실행 시 `phase:collection` 레이블 GitHub Issue 생성

### ⚠️ 테스트 먼저 (RED 확인 후 구현)

- [ ] T015 [P] [US1] `tests/unit/test_parsers.py` 작성 — `parse_notice_html()` 테스트: 제목·본문·날짜·작성자 추출, `<img>` URL 목록 추출, 첨부 링크 추출, HTML→Markdown 변환 규칙(헤딩·굵게·링크·표·목록), `fn_viewData('ID')` 패턴 파싱
- [ ] T016 [P] [US1] `tests/unit/test_models.py` 작성 — `Notice` 생성·필드 검증, `notice_id` 자동 생성(`{board_id}-{source_id}`), `AttachmentRef` 생성
- [ ] T017 [P] [US1] `tests/unit/test_cache.py` 작성 — `NoticeIndex.exists()`, `add()`, `load()`, `save()` 동작, JSON 파일 영속성, 동시 접근 안전성
- [ ] T018 [US1] `tests/integration/test_collect.py` 작성 — `respx`로 호서대 BBSList·BBSView 응답 mock; 수집 실행 시 Notice 생성 및 GitHub Issue API 호출 검증; 중복 수집 시 스킵 검증; 네트워크 오류 시 재시도 검증
- [ ] T019 [US1] `tests/contract/test_cli.py` 작성 — `collect --help` 출력 검증, `collect --dry-run` 종료코드 0, `collect` 환경변수 누락 시 종료코드 3

### US1 구현

- [ ] T020 [P] [US1] `src/notice_solver/parsers/markdown.py` 구현 — `html_to_markdown(html: str) -> str`: `<h1>~<h6>`, `<p>`, `<br>`, `<strong>/<b>`, `<em>/<i>`, `<a>`, `<table>`, `<ul>/<ol>/<li>` 변환 규칙; `<img>` 태그 제거(자산으로 별도 처리); `markdownify` 또는 직접 구현
- [ ] T021 [P] [US1] `src/notice_solver/parsers/notice.py` 구현 — `parse_notice_page(html: str, board_id: str, source_id: str) -> Notice`: BeautifulSoup으로 제목·본문·날짜·작성자 파싱; `<img src>` 목록 추출; 첨부 링크(`<a href*=download>`) 추출; `parsers/markdown.py` 사용
- [ ] T022 [P] [US1] `src/notice_solver/parsers/assets.py` 구현 — `extract_image_urls(soup) -> list[str]`: `<img>` 태그 src 추출, 썸네일 URL(`/ThumbnailPrint.do`) 감지 및 원본 URL 변환 시도(`/FileDownLoad.do`); `extract_attachment_refs(soup) -> list[AttachmentRef]`: 다운로드 링크 추출, 파일명·MIME 유형 추론
- [ ] T023 [US1] `src/notice_solver/crawlers/base.py` 구현 — `BaseCrawler` 추상 클래스: `fetch(url) -> str`(httpx + tenacity 재시도, asyncio.sleep rate limiting), `check_robots(base_url)`, `extract_notice_ids(list_html) -> list[str]`(추상), `parse_notice(view_html, id) -> Notice`(추상); 구조화 로그 출력
- [ ] T024 [US1] `src/notice_solver/crawlers/hoseo.py` 구현 — `HoseoCrawler(BaseCrawler)`: `BOARD_ID = "MAPP_1708240139"`, `BASE_URL`, `extract_notice_ids()` — `fn_viewData('ID')` 정규식 파싱, `parse_notice()` — `parsers/notice.py` 위임; 페이지네이션(`pageIndex=N`), 마지막 페이지 감지(`<strong>` 태그)
- [ ] T025 [US1] `src/notice_solver/cli/collect.py` 구현 — `collect(board: str, full: bool, limit: int, dry_run: bool)` Typer 명령: `HoseoCrawler` 실행, `NoticeIndex`로 중복 확인, `GitHubIssues.create_notice_issue()`, `CrawlRun` 기록, 완료 통계 출력; `--dry-run` 시 Issue 미생성
- [ ] T026 [US1] `src/notice_solver/cli/main.py` 구현 — `app = typer.Typer()`, `collect` 서브커맨드 등록, `--version` 옵션, 전역 설정 초기화

**Checkpoint**: US1 독립 검증 — `uv run notice-solver collect --dry-run` 정상 동작, 테스트 전체 GREEN

---

## Phase 4: User Story 2 - 자산 Issue 생성 (Priority: P2)

**Goal**: 공지 Issue의 이미지·첨부 URL → 각각 독립 자산 Issue 생성 및 공지 Issue 업데이트
**Independent Test**: 공지 Issue에 이미지 3개·첨부 2개 URL이 있을 때 `assets create` 실행 → 자산 Issue 5개 생성, 부모 Issue 테이블 업데이트

### ⚠️ 테스트 먼저 (RED 확인 후 구현)

- [ ] T027 [P] [US2] `tests/unit/test_asset_parsers.py` 작성 — `extract_image_urls()`: img 태그 추출, 썸네일→원본 URL 변환, 빈 경우; `extract_attachment_refs()`: PDF·HWP·DOCX 링크 추출, 파일명·MIME 추론
- [ ] T028 [US2] `tests/integration/test_assets.py` 작성 — mock GitHub API로 공지 Issue 조회, 자산 Issue 생성, 공지 Issue body 업데이트 검증; 자산 없는 공지 시 `has:no-assets` 레이블 검증; 이미 생성된 자산 스킵 검증

### US2 구현

- [ ] T029 [P] [US2] `src/notice_solver/github/issues.py` 확장 — `update_notice_body_with_assets(number, asset_issues)`: 공지 Issue body의 자산 목록 테이블 업데이트; `list_asset_issues(parent_notice_id)`: 특정 공지의 자산 Issue 목록 조회
- [ ] T030 [US2] `src/notice_solver/cli/assets.py` 구현 — `assets_app = typer.Typer()`; `create(notice: int, limit: int, dry_run: bool)`: `phase:collection` 공지 Issue 조회 → 프론트매터 파싱 → 이미지·첨부 URL 추출 → 자산 Issue 생성 → 공지 Issue 업데이트(`phase:organization`); `status(board: str)`: 자산 현황 집계 출력
- [ ] T031 [US2] `src/notice_solver/cli/main.py` 확장 — `assets` 서브커맨드 등록 (`assets create`, `assets status`)

**Checkpoint**: US2 독립 검증 — 공지 Issue 존재 상태에서 `assets create` 실행 → 자산 Issue 생성 확인, 테스트 GREEN

---

## Phase 5: User Story 3 - 자산 OCR 및 텍스트 추출 (Priority: P3)

**Goal**: `status:raw` 자산 Issue → OCR/텍스트 추출 → 결과를 자산 Issue에 기록
**Independent Test**: `status:raw` 자산 Issue 존재 시 `ocr run --limit 5` → 자산 Issue에 OCR 텍스트 기록, `status:ocr-complete` 전환

### ⚠️ 테스트 먼저 (RED 확인 후 구현)

- [ ] T032 [P] [US3] `tests/unit/test_ocr_image.py` 작성 — `EasyOCRWrapper.extract()`: 이미지 bytes 입력, 텍스트 반환, 신뢰도 임계값 필터, 빈 이미지 처리(→ no-text), 신뢰도 반환
- [ ] T033 [P] [US3] `tests/unit/test_ocr_document.py` 작성 — `PdfExtractor.extract()`: pdfplumber mock, 텍스트 반환; `DocxExtractor.extract()`: python-docx mock; `HwpExtractor.extract()`: LibreOffice 실행 mock, 변환 실패 시 예외
- [ ] T034 [US3] `tests/integration/test_ocr.py` 작성 — mock GitHub API + mock OCR: `status:raw` 이미지 자산 → OCR 실행 → 자산 Issue body 업데이트 + `status:ocr-complete` 레이블 검증; OCR 실패 → `status:ocr-failed` + 오류 코멘트 검증; 텍스트 없음 → `status:no-text` 검증

### US3 구현

- [ ] T035 [P] [US3] `src/notice_solver/ocr/image.py` 구현 — `EasyOCRWrapper` 클래스: `__init__`에서 `easyocr.Reader(['ko', 'en'], gpu=False)` 초기화(지연 로딩), `extract(image_bytes: bytes) -> tuple[str, float]`: readtext 실행, 신뢰도 필터링(`OCR_CONFIDENCE_THRESHOLD`), 한/영 텍스트 결합 반환; 빈 결과 시 `("", 0.0)`
- [ ] T036 [P] [US3] `src/notice_solver/ocr/document.py` 구현 — `DocumentExtractor` 팩토리: `PdfExtractor`(pdfplumber), `DocxExtractor`(python-docx 단락·표), `XlsxExtractor`(openpyxl 셀값), `HwpExtractor`(subprocess LibreOffice→DOCX→DocxExtractor); `get_extractor(mime_type: str) -> BaseExtractor`; 변환 실패 시 `ExtractionError` raise
- [ ] T037 [US3] `src/notice_solver/cli/ocr.py` 구현 — `ocr_app = typer.Typer()`; `run(limit: int, type: str, retry_failed: bool)`: `status:raw`(또는 `status:ocr-failed`) 자산 Issue 조회 → 유형별 추출기 선택 → 원본 URL 다운로드(httpx) → 추출 실행 → 자산 Issue 업데이트(OCR 텍스트 + 상태 레이블); `status()`: OCR 현황 집계; 배치 실패는 개별 처리, 전체 중단 없음
- [ ] T038 [US3] `src/notice_solver/cli/main.py` 확장 — `ocr` 서브커맨드 등록 (`ocr run`, `ocr status`)

**Checkpoint**: US3 독립 검증 — `status:raw` 자산 존재 시 `ocr run --limit 5 --dry-run` 정상 동작, 테스트 GREEN

---

## Phase 6: User Story 4 - 증분 크롤링 (Priority: P4)

**Goal**: 기수집 공지 발견 즉시 탐색 중단, 재실행 시 신규 공지만 수집
**Independent Test**: 첫 수집 후 재실행 시 수집 0건 "변경 없음" 출력

### ⚠️ 테스트 먼저 (RED 확인 후 구현)

- [ ] T039 [US4] `tests/integration/test_collect.py` 확장 — 기수집 ID 캐시 존재 시 탐색 중단 검증; `--full` 플래그 시 전체 재수집 검증; `collected: 0` 보고 시 "변경 없음" 메시지 검증

### US4 구현

- [ ] T040 [US4] `src/notice_solver/crawlers/hoseo.py` 확장 — `crawl_incremental(full: bool)`: `full=False`(기본) 시 목록 탐색 중 `NoticeIndex.exists(id)` 확인, 기수집 ID 발견 시 해당 페이지 이후 중단; `full=True` 시 전 페이지 탐색; `--limit` 옵션 적용

**Checkpoint**: US4 독립 검증 — 증분 수집 정상 동작, 테스트 GREEN

---

## Phase 7: User Story 5 - 지식 베이스 탐색 (Priority: P5)

**Goal**: GitHub Issues 레이블/검색으로 공지 탐색, description으로 빠른 미리보기
**Independent Test**: `notice-solver status` 실행 시 단계별 공지·자산 현황 출력

### ⚠️ 테스트 먼저 (RED 확인 후 구현)

- [ ] T041 [US5] `tests/contract/test_cli.py` 확장 — `status` 명령 출력 형식 검증: 공지 현황(phase별), 자산 현황(status별), 마지막 실행 시각

### US5 구현

- [ ] T042 [US5] `src/notice_solver/cli/status.py` 구현 — `status(board: str)`: GitHub Issues API로 `phase:collection`, `phase:organization` 각각 조회, `type:asset`별 `status:raw/ocr-complete/ocr-failed/no-text` 집계, `.cache/runs/` 최근 실행 기록 조회, 포맷된 현황 테이블 출력
- [ ] T043 [US5] `src/notice_solver/cli/main.py` 확장 — `status` 서브커맨드 등록

**Checkpoint**: US5 독립 검증 — `notice-solver status` 현황 출력 확인, 테스트 GREEN

---

## Phase 8: User Story 6 - 크롤링 실행 리포트 (Priority: P6)

**Goal**: 각 파이프라인 완료 후 처리 건수·소요 시간 구조화 출력, `.cache/runs/`에 기록
**Independent Test**: 파이프라인 실행 후 콘솔에 통계 출력, `.cache/runs/{id}.json` 생성

### ⚠️ 테스트 먼저 (RED 확인 후 구현)

- [ ] T044 [US6] `tests/unit/test_crawl_run.py` 작성 — `CrawlRun.report()` 출력 형식, `to_json()` 직렬화, 파일 저장 및 로드

### US6 구현

- [ ] T045 [US6] `src/notice_solver/models/crawl_run.py` 확장 — `save(cache_dir)`: `.cache/runs/{run_id}.json` 저장; `load_latest(cache_dir, pipeline)`: 최근 실행 기록 로드; 각 CLI 명령(collect, assets, ocr) 완료 시 `CrawlRun` 저장 연동

**Checkpoint**: US6 독립 검증 — 각 파이프라인 완료 후 통계 출력·파일 저장 확인

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: 전체 스토리에 걸친 품질 개선

- [ ] T046 [P] `src/notice_solver/github/labels.py` 전체 레이블 초기화 명령 추가 — `notice-solver init-labels` 서브커맨드: 저장소에 모든 레이블(`LABEL_DEFINITIONS`) 일괄 생성
- [ ] T047 [P] `.env.example` 최종 검토 및 `README.md` 작성 — 설치·설정·사용법·GitHub Actions 설명 포함
- [ ] T048 [P] `tests/contract/test_cli.py` 전체 CLI 계약 검증 완성 — 모든 명령(collect, assets, ocr, status)의 `--help` 출력, 종료코드, 필수 환경변수 누락 동작
- [ ] T049 `quickstart.md` 검증 — `uv sync && uv run notice-solver --help` 실제 실행 후 출력 확인, 필요 시 quickstart.md 업데이트
- [ ] T050 [P] GitHub Actions 워크플로우 통합 확인 — `.github/workflows/collect.yml`, `assets.yml`, `ocr.yml`의 `uv sync` 단계가 `pyproject.toml` 의존성과 일치하는지 검토
- [ ] T051 [P] `src/notice_solver/cli/infer.py` 스텁 생성 및 `src/notice_solver/cli/main.py`에 `infer` 서브커맨드 등록 — `infer run TOPIC` 호출 시 "[보류] 추론 기능은 향후 별도 스펙(002-knowledge-inference)에서 구현됩니다." 출력 후 정상 종료(exit 0); 실제 LLM 구현 없음

---

## Dependencies & Execution Order

### Phase 의존성

- **Phase 1 (Setup)**: 즉시 시작 가능
- **Phase 2 (Foundational)**: Phase 1 완료 후 — **모든 User Story 차단**
- **Phase 3 (US1)**: Phase 2 완료 후 — MVP. 완료 후 독립 배포 가능
- **Phase 4 (US2)**: Phase 3 완료 후 — US1 공지 Issue가 존재해야 함
- **Phase 5 (US3)**: Phase 4 완료 후 — US2 자산 Issue가 존재해야 함
- **Phase 6 (US4)**: Phase 3 완료 후 — US1 크롤러에 증분 로직 추가
- **Phase 7 (US5)**: Phase 2 완료 후 독립 가능 — GitHub API 조회만
- **Phase 8 (US6)**: Phase 2 완료 후 독립 가능 — CrawlRun 모델 확장
- **Polish**: 모든 US 완료 후

### User Story 의존성

- **US1 (P1)**: Phase 2 완료 후 시작. 다른 스토리 의존 없음
- **US2 (P2)**: US1 완료 후 시작 (공지 Issue 필요)
- **US3 (P3)**: US2 완료 후 시작 (자산 Issue 필요)
- **US4 (P4)**: US1 완료 후 시작 (크롤러 확장)
- **US5 (P5)**: Phase 2 완료 후 독립 가능
- **US6 (P6)**: Phase 2 완료 후 독립 가능

### 태스크 내 실행 순서

- 테스트(RED) → 구현(GREEN) → 리팩터링(REFACTOR)
- 모델 → 서비스 → CLI 명령
- 각 스토리 완료 후 Checkpoint 검증

### 병렬 기회

- T002, T003, T004, T005: Phase 1 전체 병렬
- T007, T008, T009: 모델 파일 병렬
- T015, T016, T017: US1 단위 테스트 병렬
- T020, T021, T022: US1 파서 병렬
- T032, T033: US3 OCR 단위 테스트 병렬
- T035, T036: US3 OCR 구현 병렬

---

## Implementation Strategy

### MVP First (US1만)

1. Phase 1: Setup 완료
2. Phase 2: Foundational 완료 (CRITICAL)
3. Phase 3: US1 완료 → **`notice-solver collect` 작동**
4. **STOP & VALIDATE**: `collect --dry-run` 동작, GitHub Issue 생성 확인
5. GitHub Actions `collect.yml`로 자동화 검증

### 증분 배포

1. Setup + Foundational → 기반 완성
2. US1 → `collect` 작동 → MVP!
3. US2 → `assets create` 작동 → 자산 분리
4. US3 → `ocr run` 작동 → 텍스트 추출
5. US4 → 증분 크롤링
6. US5 + US6 → 탐색·리포트

---

## Notes

- **[P]** = 병렬 실행 가능 (다른 파일, 의존성 없음)
- **TDD 필수**: 각 구현 태스크 전 테스트 먼저 작성 → RED 확인 → 구현 → GREEN
- Checkpoint마다 독립 검증 후 다음 단계 진행
- `--dry-run` 플래그로 GitHub API 호출 없이 동작 확인 가능
- `OCR_CONFIDENCE_THRESHOLD=0.5` 미만은 `status:no-text` 처리
