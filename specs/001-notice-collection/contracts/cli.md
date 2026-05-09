# CLI Contract: notice-solver

**Tool**: `notice-solver`
**Entrypoint**: `notice_solver.cli.main:app`
**Framework**: Typer

---

## 명령 구조

```
notice-solver
├── collect      # Phase 1: 공지 텍스트 수집
├── assets       # Phase 2: 자산 Issue 생성
│   ├── create
│   └── status
├── ocr          # Phase 2.5: OCR 배치 처리
│   ├── run
│   └── status
├── infer        # Phase 3: 추론
│   └── run
└── status       # 전체 현황 요약
```

---

## 명령 상세

### `notice-solver collect`

게시판을 크롤링하여 공지를 GitHub Issues로 수집합니다.

```
USAGE:
  notice-solver collect [OPTIONS]

OPTIONS:
  --board TEXT        게시판 ID (기본: 환경변수 DEFAULT_BOARD_ID)
  --full              전체 재수집 (기본: 증분)
  --limit INTEGER     수집할 최대 공지 수 (기본: 무제한)
  --dry-run           실제 Issue 생성 없이 수집 결과만 출력
  --help

EXAMPLE:
  notice-solver collect --board MAPP_1708240139
  notice-solver collect --full --limit 100 --dry-run

EXIT CODES:
  0  성공
  1  게시판 접근 실패
  2  GitHub API 오류
  3  설정 오류

OUTPUT (stdout):
  [2026-05-09 03:00:01] 수집 시작: MAPP_1708240139 (증분)
  [2026-05-09 03:00:02] 공지 97042 → Issue #42 생성 (이미지 3개, 첨부 1개)
  [2026-05-09 03:00:03] 공지 97041 → 스킵 (이미 수집됨)
  ...
  [완료] 수집: 5건 | 스킵: 120건 | 실패: 0건 | 소요: 32.4초
```

---

### `notice-solver assets create`

수집된 공지 Issues에서 자산 Issues를 생성합니다.

```
USAGE:
  notice-solver assets create [OPTIONS]

OPTIONS:
  --notice INTEGER    특정 공지 Issue 번호만 처리
  --limit INTEGER     처리할 최대 공지 수 (기본: 50)
  --dry-run           실제 Issue 생성 없이 결과만 출력
  --help

EXAMPLE:
  notice-solver assets create
  notice-solver assets create --notice 42
  notice-solver assets create --limit 20 --dry-run

OUTPUT (stdout):
  [처리] 공지 #42 → 이미지 자산 3개, 첨부 자산 1개 생성
  [처리] 공지 #41 → 자산 없음 (has:no-assets)
  ...
  [완료] 이미지 자산: 12개 | 첨부 자산: 4개 | 소요: 8.2초
```

---

### `notice-solver assets status`

자산 처리 현황을 출력합니다.

```
USAGE:
  notice-solver assets status [OPTIONS]

OPTIONS:
  --board TEXT        게시판 필터
  --help

OUTPUT (stdout):
  자산 현황 (board: 일반공지)
  ─────────────────────────────
  raw (미처리):        245개
  ocr-complete:        812개
  no-text:              38개
  ocr-failed:           12개
  auth-required:         3개
```

---

### `notice-solver ocr run`

`status:raw` 자산 Issues에 OCR/텍스트 추출을 실행합니다.

```
USAGE:
  notice-solver ocr run [OPTIONS]

OPTIONS:
  --limit INTEGER     처리할 최대 자산 수 (기본: 50)
  --type TEXT         자산 유형 필터: image | attachment | all (기본: all)
  --retry-failed      status:ocr-failed 자산 재시도
  --help

EXAMPLE:
  notice-solver ocr run
  notice-solver ocr run --limit 100 --type image
  notice-solver ocr run --retry-failed

OUTPUT (stdout):
  [처리] 자산 #51 (이미지) → OCR 완료, 신뢰도 0.91, 텍스트 47자
  [처리] 자산 #52 (이미지) → 텍스트 없음 (사진)
  [처리] 자산 #53 (PDF)    → 텍스트 추출 완료, 1,234자
  [오류] 자산 #54 (HWP)    → LibreOffice 변환 실패: exit code 1
  ...
  [완료] 성공: 42개 | 텍스트없음: 5개 | 실패: 2개 | 소요: 4분 12초

EXIT CODES:
  0  성공 (일부 실패 포함)
  1  전체 실패 (설정 오류 등)
```

---

### `notice-solver ocr status`

OCR 처리 현황을 출력합니다.

```
USAGE:
  notice-solver ocr status

OUTPUT (stdout):
  OCR 현황
  ─────────────────────────────
  이미지 자산
    raw:            245개
    ocr-complete:   612개
    no-text:         38개
    ocr-failed:      12개

  첨부 자산
    raw:             80개
    ocr-complete:   200개
    ocr-failed:       0개
```

---

### `notice-solver infer run`

수집·정리된 공지를 LLM으로 분석하여 추론 Issue를 생성합니다.

```
USAGE:
  notice-solver infer run [OPTIONS] TOPIC

ARGUMENTS:
  TOPIC               분석 주제 (예: "장학금 패턴", "학사일정 요약")

OPTIONS:
  --labels TEXT       조회할 GitHub Issue 레이블 (콤마 구분)
  --limit INTEGER     참조할 최대 공지 수 (기본: 30)
  --help

EXAMPLE:
  notice-solver infer run "장학금 패턴" --labels "category:장학금,year:2026"
  notice-solver infer run "2026 학사일정" --labels "category:학사일정"

OUTPUT (stdout):
  [분석] 장학금 패턴 — 참조 공지: 24건
  [완료] 추론 Issue #98 생성: "[추론] 장학금 패턴 — 2026년 상반기"
```

---

### `notice-solver status`

전체 파이프라인 현황을 출력합니다.

```
USAGE:
  notice-solver status [OPTIONS]

OPTIONS:
  --board TEXT    게시판 필터
  --help

OUTPUT (stdout):
  Notice-Solver 현황
  ═══════════════════════════════════════
  저장소: wawworld72/Notice-Solver
  게시판: MAPP_1708240139 (일반공지)

  공지 현황
  ─────────────────────────────
  phase:collection:   12개 (자산 생성 대기)
  phase:organization: 3,588개 (정리 완료)
  phase:inference:    45개 (추론 완료)

  자산 현황
  ─────────────────────────────
  status:raw:         325개 (OCR 대기)
  status:ocr-complete: 812개
  status:no-text:      38개
  status:ocr-failed:   12개

  마지막 실행
  ─────────────────────────────
  수집:  2026-05-09 03:00  (5건 수집)
  OCR:   2026-05-09 04:00  (50건 처리)
```

---

## 환경변수 (`.env`)

```bash
# 필수
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
GITHUB_REPO_OWNER=wawworld72
GITHUB_REPO_NAME=Notice-Solver

# 선택 (기본값 존재)
DEFAULT_BOARD_ID=MAPP_1708240139
RETRY_COUNT=3
REQUEST_DELAY_SEC=1.0
OCR_BATCH_LIMIT=50
OCR_CONFIDENCE_THRESHOLD=0.5
LOG_DIR=./logs
CACHE_DIR=./.cache
```

---

## 오류 형식

모든 오류는 stderr로 출력됩니다:

```
[오류] 공지 97042: HTTP 503 — 3회 재시도 후 실패
[오류] 자산 #51: 이미지 다운로드 실패 (ConnectionTimeout)
[경고] HWP 변환: LibreOffice 미설치 — status:ocr-failed 처리
```
