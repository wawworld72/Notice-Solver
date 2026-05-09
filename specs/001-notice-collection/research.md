# Research: 전체 공지사항 수집 시스템

**Feature**: 001-notice-collection
**Date**: 2026-05-09
**Status**: Complete — all NEEDS CLARIFICATION resolved

---

## 1. OCR / 텍스트 추출 라이브러리

### 결정: EasyOCR (이미지), pdfplumber (PDF), python-docx (DOCX), LibreOffice (HWP)

**이미지 OCR**

| 라이브러리 | 한국어 정확도 | 속도 | 결정 |
|-----------|--------------|------|------|
| EasyOCR | ★★★★★ 최고 | 중간 | ✅ 채택 |
| PaddleOCR | ★★★★☆ 우수 | 빠름 | 대안 (대용량 배치) |
| Tesseract | ★★☆☆☆ 낮음 | 빠름 | 기각 |

```python
import easyocr
reader = easyocr.Reader(['ko', 'en'], gpu=False)
results = reader.readtext(image_path, detail=0)  # list[str]
text = "\n".join(results)
```

- 초기 모델 다운로드 ~1GB, 이후 캐시됨
- GPU 없이도 동작 (CPU 모드)
- 신뢰도 임계값: 0.5 미만 → `status:no-text`

**문서 추출**

| 형식 | 라이브러리 | 이유 |
|------|-----------|------|
| PDF | `pdfplumber` | 표 추출 지원, 한국어 완벽 지원 |
| DOCX | `python-docx` | 공식 라이브러리, 단순 API |
| XLSX | `openpyxl` | 경량, 빠름 |
| HWP | LibreOffice headless → DOCX 변환 | Python HWP 파서 없음 (독점 포맷) |
| 이미지 첨부 | EasyOCR | 동일 파이프라인 재사용 |

HWP 처리:
```bash
libreoffice --headless --convert-to docx notice.hwp --outdir /tmp/
```
변환 실패 시 → `status:ocr-failed`, 오류 사유 기록.

**대안 고려 및 기각**
- Naver Clova OCR: 정확도 최고이나 유료 API → v2 옵션
- PyMuPDF: pdfplumber보다 빠르나 표 추출 열위 → 대용량 PDF에서 대안

---

## 2. GitHub Issues API 라이브러리

### 결정: `ghapi` + `python-frontmatter`, 로컬 JSON 캐시

**라이브러리 비교**

| 라이브러리 | 커버리지 | 크기 | 결정 |
|-----------|---------|------|------|
| ghapi | GitHub OpenAPI 완전 커버 | 35KB | ✅ 채택 |
| PyGithub | 주요 기능만 | 중간 | 기각 (API 갭 존재) |
| httpx 직접 | 완전 제어 | N/A | 기각 (인증·페이지네이션 직접 구현) |

```python
from ghapi.all import GhApi
api = GhApi(token=settings.github_token)
issue = api.issues.create(
    owner=settings.github_repo_owner,
    repo=settings.github_repo_name,
    title="[수집] 공지 제목",
    body=issue_body,
    labels=["phase:collection", "board:일반공지"]
)
```

**Rate Limits**
- Core API (이슈 읽기/쓰기): 5,000 req/시간
- Search API: 30 req/분 (매우 엄격)
- **전략**: Search API 미사용. 레이블 필터 + 클라이언트 사이드 매칭으로 중복 확인.

**중복 확인 전략 (2레이어)**
```python
# Layer 1: 로컬 JSON 캐시 (O(1) 조회)
# .cache/notice-index.json: {"MAPP_1708240139-97042": 42}

# Layer 2: GitHub Issues 레이블 조회 + 메타데이터 매칭
# Search API 사용 금지 (rate limit)
```

로컬 캐시가 없거나 불일치 시에만 API 조회.

**프론트매터 형식: HTML 주석 블록**
```markdown
<!-- NOTICE_META
id: MAPP_1708240139-97042
title: 공지 제목
published_at: 2026-05-01
phase: collection
-->

> **요약**: ...
```

- GitHub 렌더링에서 보이지 않음 (사용자 경험 깔끔)
- API `body` 필드에서 파싱 가능
- `python-frontmatter`로 파싱

**기각된 대안: YAML 코드 블록**
- 렌더링 시 노출되어 시각적으로 복잡

---

## 3. CLI 프레임워크 및 패키징

### 결정: Typer + pydantic-settings + uv + hatchling

**CLI: Typer**
- type hint 기반 자동 CLI 생성 → 보일러플레이트 최소
- Click 대비 서브커맨드 구조가 더 깔끔
- 기각: Click (더 많은 수작업 필요)

**설정: pydantic-settings**
```python
class Settings(BaseSettings):
    github_token: str
    github_repo_owner: str
    github_repo_name: str
    retry_count: int = 3
    request_delay_sec: float = 1.0
    ocr_batch_limit: int = 50
    model_config = SettingsConfigDict(env_file=".env")
```

**패키징**
```toml
[project.scripts]
notice-solver = "notice_solver.cli.main:app"
```

```bash
uv sync && uv run notice-solver --help
```

**테스트: pytest + typer.testing.CliRunner**
- `pytest-asyncio`: 비동기 크롤러 테스트
- `respx`: httpx mock (HTTP 요청 테스트)
- `CliRunner`: CLI 명령 통합 테스트

---

## 4. 크롤러 기술

### 결정: httpx (비동기) + BeautifulSoup4

- `httpx`: requests 대비 async 지원, HTTP/2 지원
- `lxml` 파서: BeautifulSoup4와 조합, 가장 빠름

```python
async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
    resp = await client.get(url)
    soup = BeautifulSoup(resp.text, "lxml")
```

- 재시도: `tenacity` 라이브러리 (지수 백오프)
- Rate limiting: `asyncio.sleep(settings.request_delay_sec)`

---

## 5. 핵심 설계 결정 요약

| 항목 | 결정 | 근거 |
|------|------|------|
| 이미지 OCR | EasyOCR (ko+en) | 한국어 최고 정확도 |
| PDF | pdfplumber | 표 지원 |
| HWP | LibreOffice 변환 | Python HWP 파서 없음 |
| GitHub API | ghapi | 완전 커버리지 |
| 중복 확인 | 로컬 JSON 캐시 | Search API rate limit 회피 |
| 프론트매터 | HTML 주석 | 렌더링 숨김 + 파싱 가능 |
| CLI | Typer | type hint 기반, 간결 |
| 설정 | pydantic-settings | 타입 안전 .env 로딩 |
| HTTP | httpx (async) | async 지원 |
| 패키지 | uv + hatchling | 최신 Python 생태계 |
