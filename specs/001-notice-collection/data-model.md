# Data Model: 전체 공지사항 수집 시스템

**Feature**: 001-notice-collection
**Date**: 2026-05-09

---

## 핵심 엔티티

### 1. Notice (공지) — GitHub Issue로 표현

```python
@dataclass
class Notice:
    # 식별자
    source_id: str          # schIdx (예: "97042")
    board_id: str           # 예: "MAPP_1708240139"
    notice_id: str          # f"{board_id}-{source_id}"

    # 원본 메타데이터
    title: str
    body_text: str          # HTML → plain text 변환
    source_url: str
    published_at: datetime
    crawled_at: datetime
    author: str = ""

    # 자산 (수집 시 URL만 기록)
    image_urls: list[str] = field(default_factory=list)
    attachments: list[AttachmentRef] = field(default_factory=list)

    # GitHub Issue 참조
    github_issue_number: int | None = None

    # 파이프라인 상태
    phase: str = "collection"   # collection | organization | inference
```

**GitHub Issue 형식:**
```markdown
<!-- NOTICE_META
id: MAPP_1708240139-97042
board_id: MAPP_1708240139
board: 일반공지
title: 2026 대학축제 개최 안내
author: 학생처
published_at: 2026-05-01
crawled_at: 2026-05-09T03:00:00+09:00
source_url: https://www.hoseo.ac.kr/Home/BBSView.mbz?action=MAPP_1708240139&schIdx=97042
year: 2026
semester: spring
category: 행사
tags: [축제, 학생행사, 캠퍼스]
description: 5월 20일~22일 천안캠퍼스 대학축제. 공연·전시·먹거리 행사. 참가신청 5.10까지.
image_count: 3
attachment_count: 1
asset_issues: []
phase: collection
-->

> **요약**: 5월 20일~22일 천안캠퍼스 대학축제. 참가신청: **5월 10일까지**

## 공지 내용

[본문 plain text — HTML 태그 제거, Markdown 변환]

## 자산 목록

### 인라인 이미지
- img-001: `https://www.hoseo.ac.kr/ThumbnailPrint.do?dir=editor&savename=KakaoTalk_001.jpg`
- img-002: `https://www.hoseo.ac.kr/ThumbnailPrint.do?dir=editor&savename=KakaoTalk_002.jpg`
- img-003: `https://www.hoseo.ac.kr/ThumbnailPrint.do?dir=editor&savename=KakaoTalk_003.jpg`

### 첨부 파일
- attach-001: `https://www.hoseo.ac.kr/download/...` | `2026축제공지문.pdf` | `application/pdf`

## 원본

- **출처**: [원문 보기](https://www.hoseo.ac.kr/...)
- **게시판**: 일반공지 | **작성자**: 학생처 | **게시일**: 2026-05-01
```

**Labels**: `phase:collection`, `board:일반공지`, `year:2026`, `semester:spring`,
`category:행사`, `has:images`, `has:attachments`

---

### 2. Asset (자산) — GitHub Issue로 표현

```python
@dataclass
class AttachmentRef:
    url: str
    filename: str
    mime_type: str          # application/pdf, application/x-hwp 등

@dataclass
class Asset:
    # 식별자
    asset_id: str           # f"{notice_id}-img-{seq:03d}" 또는 f"{notice_id}-attach-{seq:03d}"
    parent_notice_id: str   # 부모 공지 notice_id
    parent_issue_number: int  # 부모 공지 GitHub Issue 번호

    # 자산 유형
    type: Literal["image", "attachment"]
    sequence: int           # 공지 내 순서 (1부터)
    total_in_notice: int    # 공지 내 동일 유형 자산 총수

    # 원본 정보
    src_url: str            # 수집된 URL (썸네일 또는 원본)
    full_url: str = ""      # 원본 URL (썸네일에서 변환, 빈 경우 src_url 사용)
    filename: str = ""      # 첨부 파일명
    mime_type: str = ""     # MIME 유형

    # OCR/추출 상태
    ocr_status: str = "raw"
    # raw | ocr-complete | ocr-failed | no-text | auth-required
    ocr_text: str = ""
    ocr_confidence: float = 0.0
    ocr_processed_at: datetime | None = None

    # GitHub Issue 참조
    github_issue_number: int | None = None
```

**이미지 자산 GitHub Issue 형식:**
```markdown
<!-- ASSET_META
asset_id: MAPP_1708240139-97042-img-001
type: image
parent_notice_id: MAPP_1708240139-97042
parent_issue_number: 42
sequence: 1
total_in_notice: 3
src_url: https://www.hoseo.ac.kr/ThumbnailPrint.do?dir=editor&savename=KakaoTalk_001.jpg
full_url: https://www.hoseo.ac.kr/FileDownLoad.do?dir=editor&savename=KakaoTalk_001.jpg
ocr_status: raw
-->

**공지**: #42 — 2026 대학축제 개최 안내
**게시판**: 일반공지 | **게시일**: 2026-05-01 | **이미지**: 1/3

---

## OCR 결과

_미처리 (`status:raw`)_
```

**첨부 자산 GitHub Issue 형식:**
```markdown
<!-- ASSET_META
asset_id: MAPP_1708240139-97042-attach-001
type: attachment
parent_notice_id: MAPP_1708240139-97042
parent_issue_number: 42
sequence: 1
total_in_notice: 1
src_url: https://www.hoseo.ac.kr/download/2026festival.pdf
filename: 2026축제공지문.pdf
mime_type: application/pdf
ocr_status: raw
-->

**공지**: #42 — 2026 대학축제 개최 안내
**파일**: `2026축제공지문.pdf` (application/pdf) | **첨부**: 1/1

---

## 텍스트 추출 결과

_미처리 (`status:raw`)_
```

**OCR 완료 후 업데이트:**
```markdown
## OCR 결과

**처리일**: 2026-05-09T04:00:00+09:00
**신뢰도**: 0.91

```text
호서대학교 대학축제
일시: 2026.05.20(수) ~ 05.22(금)
장소: 천안캠퍼스 잔디광장
주최: 총학생회
...
```
```

**Labels (이미지)**: `type:asset`, `asset:image`, `status:raw`, `board:일반공지`
**Labels (첨부)**: `type:asset`, `asset:attachment`, `status:raw`, `board:일반공지`

---

### 3. CrawlRun (실행 기록) — 로컬 JSON 파일

GitHub Issues API 요청을 아끼기 위해 실행 기록은 로컬에 저장합니다.

```python
@dataclass
class CrawlRun:
    run_id: str             # ISO 타임스탬프 기반 고유 ID
    pipeline: str           # collect | asset | ocr | infer
    board_id: str = ""
    started_at: datetime = field(default_factory=datetime.utcnow)
    finished_at: datetime | None = None
    processed: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[dict] = field(default_factory=list)
    # errors: [{"id": "...", "url": "...", "reason": "..."}]
```

**파일**: `.cache/runs/{run_id}.json`

---

### 4. 로컬 상태 캐시 — 중복 확인용

```json
// .cache/notice-index.json
{
  "MAPP_1708240139-97042": 42,
  "MAPP_1708240139-97041": 41,
  ...
}

// .cache/asset-index.json
{
  "MAPP_1708240139-97042-img-001": 51,
  "MAPP_1708240139-97042-img-002": 52,
  ...
}
```

---

## 상태 전이

### Notice Phase 전이

```
[수집] phase:collection
    ↓ (자산 Issue 생성 완료)
[정리] phase:organization
    ↓ (추론 처리 완료)
[추론] phase:inference
```

### Asset OCR 상태 전이

```
[초기] status:raw
    ↓
    ├── OCR 성공 → status:ocr-complete
    ├── 텍스트 없음 → status:no-text
    ├── OCR 실패 → status:ocr-failed (재시도 가능)
    └── 인증 필요 → status:auth-required (수동 처리)
```

---

## GitHub Label 체계

```
# 파이프라인 단계
phase:collection
phase:organization
phase:inference

# 자산 구분
type:asset
asset:image
asset:attachment

# OCR 상태
status:raw
status:ocr-complete
status:ocr-failed
status:no-text
status:auth-required

# 게시판
board:일반공지
board:장학
board:학사
board:취업

# 분류
category:행사
category:장학금
category:학사일정
category:취업

# 연도/학기
year:2026
year:2025
semester:spring
semester:fall

# 콘텐츠
has:images
has:attachments
has:no-assets
```

---

## HTML → Markdown 변환 규칙

| 원본 HTML | Markdown 변환 |
|----------|--------------|
| `<h1>~<h6>` | `#`~`######` |
| `<p>` | 줄바꿈 2회 |
| `<br>` | 줄바꿈 1회 |
| `<strong>`, `<b>` | `**text**` |
| `<em>`, `<i>` | `*text*` |
| `<a href="...">` | `[text](url)` |
| `<img src="...">` | 제거 (자산으로 별도 처리) |
| `<table>` | GFM 테이블 |
| `<ul>`, `<ol>`, `<li>` | Markdown 목록 |
| 나머지 태그 | 태그 제거, 텍스트만 유지 |
