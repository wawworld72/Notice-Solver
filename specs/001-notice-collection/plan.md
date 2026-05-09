# Implementation Plan: 전체 공지사항 수집 시스템

**Branch**: `claude/integrate-spec-kit-6wnSA` | **Date**: 2026-05-09 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/001-notice-collection/spec.md`

---

## Summary

게시판 크롤링으로 공지사항을 수집하여 GitHub Issues 기반 지식 베이스를 구축하는
Python CLI 도구. 4단계 독립 파이프라인(수집 → 자산 생성 → OCR → 추론)으로 구성되며,
공지 본문 내 인라인 이미지와 첨부 파일을 자산 Issue로 분리 관리하고
EasyOCR·pdfplumber로 텍스트를 추출한다. SQL 없이 GitHub Issues를 저장소로 사용한다.

---

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**:
- `httpx` — 비동기 HTTP 클라이언트 (크롤링)
- `beautifulsoup4` + `lxml` — HTML 파싱
- `easyocr` — 이미지 OCR (한/영)
- `pdfplumber` — PDF 텍스트 추출
- `python-docx` — DOCX 추출
- `openpyxl` — XLSX 추출
- `ghapi` — GitHub Issues API
- `python-frontmatter` — Issue body 메타데이터 파싱
- `typer[all]` — CLI 프레임워크
- `pydantic-settings` — 설정 관리
- `tenacity` — 재시도 로직 (지수 백오프)

**Storage**: GitHub Issues (SQL 없음) + 로컬 JSON 캐시 (`.cache/`)

**Testing**: pytest + pytest-asyncio + respx (HTTP mock) + typer.testing.CliRunner

**Target Platform**: Linux / macOS (로컬 또는 서버 실행)

**Project Type**: CLI 도구 (Python 패키지)

**Performance Goals**:
- 수집: 1 req/sec (rate limit 준수)
- OCR 배치: 50건/실행 기본, 이미지당 2~10초
- 전체 초기 수집: 약 60분 (~3,600건)
- 증분 수집: 5분 이내 (신규 공지 수십 건)

**Constraints**:
- robots.txt 준수 필수
- GitHub API: Core 5,000 req/시간, Search 30 req/분
- 자산 파일 GitHub 저장 없음 (원본 URL 참조)
- .env 파일로 비밀 관리, 저장소 커밋 금지

**Scale/Scope**: v1 — 호서대학교 일반공지 1개 게시판, ~3,600건

---

## Constitution Check

*GATE: Phase 0 시작 전 확인. Phase 1 설계 후 재확인.*

| 원칙 | 상태 | 확인 내용 |
|------|------|---------|
| **I. Reliable Data Collection** | ✅ PASS | `tenacity` 재시도, `asyncio.sleep(1.0)` rate limiting, 증분 크롤링으로 재시작 가능 |
| **II. Structured Knowledge Representation** | ✅ PASS | Notice·Asset HTML 주석 프론트매터로 정규화. 원본 HTML 미저장 |
| **III. Test-First (NON-NEGOTIABLE)** | ✅ PASS | 구현 전 테스트 작성. `tests/unit/`, `tests/integration/`, `tests/contract/` 구조 |
| **IV. Incremental Processing** | ✅ PASS | 기본 증분 크롤링. 전체 재수집은 `--full` 명시 필요. `notice_id` 기반 멱등성 |
| **V. Observability** | ✅ PASS | 공지·자산·OCR 각 단계별 구조화 로그. 파이프라인 완료 후 통계 출력 |

**⚠️ 헌법 편차**: 헌법 Technology Constraints "SQLite 또는 PostgreSQL" → 스펙이 GitHub Issues 채택.

---

## Complexity Tracking

| 편차 | 필요한 이유 | 더 단순한 대안이 기각된 이유 |
|------|------------|--------------------------|
| SQL 없이 GitHub Issues 사용 (헌법 편차) | 별도 DB 인프라 없이 FTS·레이블·이슈 연결·감사 로그를 GitHub 기능으로 대체 | SQLite 도입 시 스키마 관리·마이그레이션·배포 복잡도 증가. 지식 베이스 협업 기능도 GitHub가 기본 제공 |
| LibreOffice 시스템 의존성 (HWP 처리) | Python HWP 파서 없음 (독점 포맷). LibreOffice만 신뢰할 수 있는 변환 도구 | hwp2text pip 패키지는 구형 포맷만 지원, 최신 HWP 미지원 |

---

## Project Structure

### Documentation

```text
specs/001-notice-collection/
├── plan.md           ✅ 이 파일
├── spec.md           ✅ 기능 명세
├── research.md       ✅ 기술 결정 리서치
├── data-model.md     ✅ 데이터 모델 및 GitHub Issue 형식
├── quickstart.md     ✅ 빠른 시작 가이드
├── contracts/
│   └── cli.md        ✅ CLI 명령 컨트랙트
└── tasks.md          ⏳ /speckit-tasks 실행 후 생성
```

### Source Code (저장소 루트)

```text
notice-solver/
├── src/
│   └── notice_solver/
│       ├── __init__.py
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── main.py          # Typer app + 서브커맨드 등록
│       │   ├── collect.py       # collect 명령
│       │   ├── assets.py        # assets create / status 명령
│       │   ├── ocr.py           # ocr run / status 명령
│       │   ├── infer.py         # infer run 명령
│       │   └── status.py        # status 명령
│       ├── crawlers/
│       │   ├── __init__.py
│       │   ├── base.py          # 추상 크롤러 인터페이스
│       │   └── hoseo.py         # 호서대 어댑터 (fn_viewData 파싱)
│       ├── parsers/
│       │   ├── __init__.py
│       │   ├── notice.py        # HTML → Notice 모델 변환
│       │   ├── assets.py        # 이미지·첨부 URL 추출
│       │   └── markdown.py      # HTML → Markdown 변환
│       ├── ocr/
│       │   ├── __init__.py
│       │   ├── image.py         # EasyOCR 래퍼
│       │   └── document.py      # PDF/DOCX/HWP/XLSX 추출기
│       ├── github/
│       │   ├── __init__.py
│       │   ├── issues.py        # GitHub Issues CRUD
│       │   ├── labels.py        # 레이블 관리·일괄 생성
│       │   └── frontmatter.py   # 프론트매터 파싱·생성
│       ├── models/
│       │   ├── __init__.py
│       │   ├── notice.py        # Notice 데이터클래스
│       │   ├── asset.py         # Asset, AttachmentRef 데이터클래스
│       │   └── crawl_run.py     # CrawlRun 데이터클래스
│       ├── cache/
│       │   ├── __init__.py
│       │   └── index.py         # 로컬 JSON 인덱스 (중복 확인)
│       └── config.py            # pydantic-settings 설정
│
├── tests/
│   ├── conftest.py              # 픽스처, CliRunner, Mock 설정
│   ├── unit/
│   │   ├── test_parsers.py      # HTML 파싱, 프론트매터 변환
│   │   ├── test_models.py       # 데이터클래스 검증
│   │   └── test_cache.py        # 로컬 인덱스 CRUD
│   ├── integration/
│   │   ├── test_collect.py      # 크롤러 → GitHub Issue 통합
│   │   ├── test_assets.py       # 자산 추출 → Asset Issue 통합
│   │   └── test_ocr.py          # OCR 파이프라인 통합
│   └── contract/
│       └── test_cli.py          # CLI 명령 계약 검증
│
├── pyproject.toml
├── .env.example
├── .gitignore                   # .env, .cache/, logs/ 제외
└── README.md
```

**구조 결정**: 단일 Python 패키지. 크롤러·OCR·GitHub 계층이 명확히 분리됨.
CLI는 얇은 진입점이고 비즈니스 로직은 서비스 레이어에 위치.

---

## Constitution Check (Phase 1 설계 후 재확인)

| 원칙 | 상태 | 설계 반영 내용 |
|------|------|--------------|
| **I. Reliable Data Collection** | ✅ PASS | `crawlers/base.py`에 `tenacity` 재시도 추상화. `hoseo.py` 어댑터에서 robots.txt 확인 |
| **II. Structured Knowledge Representation** | ✅ PASS | `models/` 데이터클래스가 정규화 강제. `parsers/markdown.py`가 HTML→Markdown 변환 |
| **III. Test-First** | ✅ PASS | `tests/unit/`, `tests/integration/`, `tests/contract/` 구조. 구현 전 테스트 필수 |
| **IV. Incremental Processing** | ✅ PASS | `cache/index.py`가 O(1) 중복 확인. `collect.py`에서 기수집 ID 발견 시 탐색 중단 |
| **V. Observability** | ✅ PASS | 각 CLI 명령이 구조화 로그 + 완료 통계 출력. `crawl_run.py`가 실행 기록 보존 |
