# Feature Specification: 전체 공지사항 수집 시스템

**Feature Branch**: `001-notice-collection`
**Created**: 2026-05-09
**Status**: Draft
**Input**: 게시판 크롤링을 통해 공지사항을 수집하고 지식 베이스(Knowledge Base)화하는 전체 시스템

## User Scenarios & Testing *(mandatory)*

<!--
  자산(Asset) 정의:
  - 인라인 이미지: 공지 본문 HTML 내 <img> 태그로 삽입된 이미지 파일
  - 첨부 파일: 공지 하단 다운로드 링크로 제공되는 파일 (PDF, HWP, DOCX, XLSX, ZIP 등)
  두 유형 모두 공지와 별도로 관리되며, OCR/텍스트 추출은 독립 파이프라인에서 처리한다.
-->

### User Story 1 - 공지 텍스트 수집 (Priority: P1)

운영자가 수집 대상 게시판 URL을 등록하면, 시스템이 해당 게시판을 크롤링하여
공지의 텍스트 정보(제목, 본문, 게시일, 작성자)를 수집하고 GitHub Issue로 저장한다.
자산(이미지·첨부)은 이 단계에서 URL만 기록하고 별도 처리하지 않는다.

**Why this priority**: 텍스트 수집이 모든 후속 처리의 전제이다.
자산 없이도 공지의 핵심 내용을 확보할 수 있어 독립적으로 가치를 제공한다.

**Independent Test**: CLI로 크롤링을 실행하면 공지 텍스트가 GitHub Issue로 생성되고
`phase:collection` 레이블이 붙는다. 이미지·첨부는 URL 목록만 기록된다.

**Acceptance Scenarios**:

1. **Given** 유효한 게시판 URL이 등록되어 있을 때,
   **When** 크롤링을 실행하면,
   **Then** 각 공지의 제목·본문·게시일·작성자가 GitHub Issue로 생성되고
   본문 내 인라인 이미지 URL 목록과 첨부 파일 URL 목록이 Issue에 기록된다.

2. **Given** 네트워크 오류가 발생했을 때,
   **When** 크롤링을 실행하면,
   **Then** 최대 3회 재시도 후 실패 시 오류 사유를 로그에 기록하고 다음 공지로 진행한다.

3. **Given** 이미 수집된 공지가 존재할 때,
   **When** 동일 게시판을 재크롤링하면,
   **Then** 중복 Issue는 생성되지 않고 새 공지만 추가된다.

---

### User Story 2 - 자산 Issue 생성 (Priority: P2)

수집된 공지 Issue에 기록된 이미지·첨부 URL을 바탕으로, 각 자산마다 독립된
GitHub Issue를 생성하고 부모 공지 Issue와 연결한다.
자산 Issue는 이후 OCR·텍스트 추출 파이프라인의 처리 단위가 된다.

**Why this priority**: 자산을 독립 Issue로 분리해야 OCR 처리·실패·재시도를
공지와 무관하게 관리할 수 있다.

**Independent Test**: 공지 Issue가 존재하는 상태에서 자산 생성 명령을 실행하면,
인라인 이미지 3개·첨부 2개인 공지에 대해 자산 Issue 5개가 생성되고
각각 `type:asset`, `status:raw` 레이블을 가지며 부모 공지 Issue 번호를 참조한다.

**Acceptance Scenarios**:

1. **Given** 공지 Issue 내에 인라인 이미지 URL이 기록되어 있을 때,
   **When** 자산 생성을 실행하면,
   **Then** 이미지마다 `asset:image`, `status:raw` 레이블의 자산 Issue가 생성되고
   부모 공지 Issue 번호가 메타데이터에 기록된다.

2. **Given** 공지 Issue 내에 첨부 파일 URL이 기록되어 있을 때,
   **When** 자산 생성을 실행하면,
   **Then** 첨부마다 `asset:attachment`, `status:raw` 레이블의 자산 Issue가 생성되고
   파일명·MIME 유형·부모 공지 Issue 번호가 메타데이터에 기록된다.

3. **Given** 자산이 없는 공지 Issue일 때,
   **When** 자산 생성을 실행하면,
   **Then** 자산 Issue가 생성되지 않고 공지 Issue에 `has:no-assets` 레이블이 추가된다.

---

### User Story 3 - 자산 OCR 및 텍스트 추출 (Priority: P3)

`status:raw` 자산 Issue를 대상으로 독립 배치 파이프라인이 OCR 또는 텍스트 추출을 수행하고
결과를 자산 Issue에 기록한다. 이 단계는 공지 수집·자산 생성과 완전히 분리되어 실행된다.

**Why this priority**: OCR은 CPU·시간 집약적이므로 수집과 분리해야 한다.
처리 실패가 공지 수집 흐름에 영향을 주지 않아야 한다.

**Independent Test**: `status:raw,asset:image` 자산 Issue가 존재할 때 OCR 배치를 실행하면,
각 자산 Issue에 OCR 텍스트가 기록되고 `status:ocr-complete`로 전환된다.
원본 공지 수집 파이프라인은 중단 없이 동작한다.

**Acceptance Scenarios**:

1. **Given** `status:raw`, `asset:image` 자산 Issue가 존재할 때,
   **When** OCR 배치를 실행하면,
   **Then** 이미지를 원본 URL에서 다운로드하여 OCR을 수행하고
   한국어·영어 텍스트를 추출하여 자산 Issue에 기록한 뒤 `status:ocr-complete`로 전환한다.

2. **Given** `status:raw`, `asset:attachment` 자산 Issue가 존재할 때 (PDF/HWP/DOCX 등),
   **When** 텍스트 추출 배치를 실행하면,
   **Then** 파일 형식에 맞는 추출기로 텍스트를 추출하여 자산 Issue에 기록한 뒤
   `status:ocr-complete`로 전환한다.

3. **Given** OCR·추출이 실패했을 때,
   **When** 배치가 실패를 감지하면,
   **Then** 자산 Issue에 실패 사유를 기록하고 `status:ocr-failed`로 전환하며
   다른 자산 처리는 계속한다.

4. **Given** 텍스트가 없는 이미지(사진, 도표)일 때,
   **When** OCR을 수행하면,
   **Then** `status:no-text`로 분류하고 자산 Issue에 "텍스트 미검출"을 기록한다.

---

### User Story 4 - 증분 크롤링 (Priority: P4)

시스템이 이전 실행 이후 새로 게시된 공지만 수집하여 처리 시간과 리소스를 최소화한다.

**Why this priority**: 약 3,600건 이상의 기존 공지가 존재하므로
매회 전체 재크롤은 비효율적이다.

**Independent Test**: 첫 실행 후 새 공지가 추가된 상태에서 다시 실행하면,
새 공지 Issue만 생성되고 기존 Issue는 변경되지 않는다.

**Acceptance Scenarios**:

1. **Given** 지난 크롤링 기록이 존재할 때,
   **When** 증분 크롤링을 실행하면,
   **Then** 마지막 수집 이후 게시된 공지만 새 Issue로 생성된다.

2. **Given** 게시판에 변경 사항이 없을 때,
   **When** 증분 크롤링을 실행하면,
   **Then** "수집 0건 (변경 없음)" 메시지와 함께 정상 종료된다.

---

### User Story 5 - 지식 베이스 탐색 (Priority: P5)

사용자가 GitHub Issues 레이블·검색으로 공지를 탐색하고,
`description` 프론트매터만으로 전체 본문 로드 없이 관련 공지를 찾을 수 있다.

**Why this priority**: 수집·정리된 데이터의 활용 가치를 제공한다.

**Independent Test**: `phase:organization` 공지 Issue가 존재할 때,
레이블 필터(`category:장학금,year:2026`)와 키워드 검색으로 관련 공지를 찾고
description만으로 내용을 파악할 수 있다.

**Acceptance Scenarios**:

1. **Given** 정리된 공지 Issue가 존재할 때,
   **When** `category:행사,year:2026` 레이블로 필터링하면,
   **Then** 해당 조건의 공지 목록이 반환되며 각 Issue의 description으로 내용을 파악할 수 있다.

2. **Given** OCR이 완료된 자산 Issue가 연결되어 있을 때,
   **When** 공지 Issue에서 자산 Issue를 조회하면,
   **Then** 이미지·첨부의 OCR 텍스트를 포함한 전체 내용을 확인할 수 있다.

---

### User Story 6 - 크롤링 실행 리포트 (Priority: P6)

크롤링·자산 생성·OCR 각 단계 완료 후 처리 건수와 소요 시간을 출력한다.

**Independent Test**: 각 파이프라인 실행 후 콘솔에 단계별 통계가 출력된다.

**Acceptance Scenarios**:

1. **Given** 크롤링이 완료되었을 때,
   **When** 결과를 확인하면,
   **Then** 공지 수집(collected/skipped/failed), 자산 생성(images/attachments) 건수와
   소요 시간이 표시된다.

2. **Given** OCR 배치가 완료되었을 때,
   **When** 결과를 확인하면,
   **Then** OCR 성공/실패/텍스트 없음 건수와 소요 시간이 표시된다.

---

### Edge Cases

- 공지 본문에 인라인 이미지와 첨부 파일이 동시에 존재하는 경우 각각 별도 자산 Issue로 생성한다.
- 동일 이미지 URL이 여러 공지에 등장하면 각 공지마다 별도 자산 Issue를 생성한다 (참조 중복 허용).
- 첨부 파일이 ZIP인 경우 압축 해제 후 내부 파일을 별도 자산으로 처리한다 (v1 범위 외, TODO).
- HWP 파일은 플랫폼 의존적이므로 LibreOffice 변환 또는 hwp2text를 사용하며,
  변환 불가 시 `status:ocr-failed`로 분류한다.
- 이미지 URL이 썸네일 경로(`/ThumbnailPrint.do`)인 경우 원본 URL 패턴으로 변환하여 OCR한다.
  원본 URL 변환 실패 시 썸네일로 OCR을 시도한다.
- 첨부 파일 다운로드가 인증을 요구하는 경우 `status:auth-required`로 분류한다.
- 게시판 구조 변경으로 자산 URL 추출이 실패하면 파싱 오류 알림을 발생시킨다.

## Requirements *(mandatory)*

### Functional Requirements

**수집 (Phase 1)**
- **FR-001**: 시스템은 등록된 게시판 URL에서 공지 목록을 크롤링할 수 있어야 한다.
- **FR-002**: 각 공지는 제목·본문 텍스트·게시일·작성자·source_url을 포함한
  GitHub Issue로 저장되어야 한다 (`phase:collection` 레이블).
- **FR-003**: 공지 본문 내 인라인 이미지 URL 목록이 공지 Issue 메타데이터에 기록되어야 한다.
- **FR-004**: 공지 하단 첨부 파일 URL·파일명·형식이 공지 Issue 메타데이터에 기록되어야 한다.
- **FR-005**: 동일 공지의 중복 Issue 생성이 방지되어야 한다 (`source_id` 기반).
- **FR-006**: 네트워크 오류 시 설정 가능한 횟수만큼 재시도해야 한다 (기본 3회).
- **FR-007**: 요청 간 최소 1초의 간격을 두어야 한다.

**자산 처리 (Phase 2)**
- **FR-008**: 공지 Issue 메타데이터의 이미지 URL마다 `asset:image`, `status:raw` 레이블의
  자산 Issue를 생성해야 한다.
- **FR-009**: 공지 Issue 메타데이터의 첨부 URL마다 `asset:attachment`, `status:raw` 레이블의
  자산 Issue를 생성해야 한다.
- **FR-010**: 자산 Issue는 부모 공지 Issue 번호를 메타데이터에 포함해야 한다.
- **FR-011**: 자산이 없는 공지에는 `has:no-assets` 레이블을 부여해야 한다.

**OCR / 텍스트 추출 (Phase 2.5 — 독립 배치)**
- **FR-012**: OCR 배치는 `status:raw` 자산 Issue를 조회하여 독립적으로 실행되어야 한다.
- **FR-013**: 이미지 자산은 EasyOCR(한/영)로 텍스트를 추출하여 자산 Issue에 기록해야 한다.
- **FR-014**: 문서 자산(PDF·DOCX·HWP·XLSX)은 형식별 추출기로 텍스트를 추출해야 한다.
- **FR-015**: OCR·추출 결과는 자산 Issue에 기록되고 `status:ocr-complete`,
  `status:ocr-failed`, `status:no-text` 중 하나로 전환되어야 한다.
- **FR-016**: OCR 배치 실패는 개별 자산에 국한되며 전체 배치를 중단하지 않아야 한다.

**탐색 (Phase 3)**
- **FR-017**: 시스템은 GitHub Issues 레이블 필터와 검색으로 공지를 탐색할 수 있어야 한다.
- **FR-018**: 공지 Issue의 `description` 프론트매터만으로 전체 본문 로드 없이
  내용 파악이 가능해야 한다.
- **FR-019**: 시스템은 robots.txt를 준수해야 한다.

**운영**
- **FR-020**: 시스템은 CLI를 통해 크롤링, 자산 생성, OCR 배치, 탐색을 각각 독립 실행할 수 있어야 한다.
- **FR-021**: 각 파이프라인 실행 후 처리 건수·소요 시간 리포트를 출력해야 한다.
- **FR-022**: 증분 크롤링을 지원해야 하며, 기본 동작은 증분이어야 한다.

### Key Entities *(include if feature involves data)*

- **Board (게시판)**: 수집 대상 게시판.
  속성: `board_id`, `url`, `name`, `last_crawled_at`, `enabled`.

- **Notice (공지)**: 수집된 공지사항 — GitHub Issue로 표현.
  메타데이터: `id`, `board_id`, `title`, `body_text`, `source_url`, `published_at`,
  `crawled_at`, `phase`, `image_urls[]`, `attachment_urls[]`.

- **Asset (자산)**: 공지에 포함된 이미지 또는 첨부 파일 — GitHub Issue로 표현.
  메타데이터: `asset_id`, `parent_notice_id`, `type` (image|attachment),
  `src_url`, `filename`, `mime_type`, `ocr_status`, `ocr_text`.
  - **인라인 이미지**: 공지 본문 `<img>` 태그에서 추출.
  - **첨부 파일**: 공지 하단 다운로드 링크에서 추출 (PDF, HWP, DOCX, XLSX, ZIP 등).

- **CrawlRun (실행 기록)**: 각 파이프라인 실행 결과.
  속성: `pipeline` (collect|asset|ocr), `started_at`, `finished_at`,
  `processed`, `skipped`, `failed`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 새 게시판 등록 후 첫 크롤링(텍스트 수집)이 5분 이내 완료된다.
- **SC-002**: 증분 크롤링 시 변경 없는 게시판은 10초 이내 "변경 없음"으로 완료된다.
- **SC-003**: 이미지 자산 Issue와 첨부 자산 Issue가 부모 공지 Issue와 정확히 연결된다.
- **SC-004**: OCR 배치 실패율이 전체 자산의 10% 미만이다 (일반적인 공개 이미지 기준).
- **SC-005**: OCR 완료된 자산의 텍스트가 공지 탐색 시 활용 가능하다.
- **SC-006**: 동일 게시판을 10회 반복 크롤링해도 중복 Issue가 생성되지 않는다.
- **SC-007**: `description` 프론트매터로 전체 본문 로드 없이 공지 내용을 파악할 수 있다.

## Assumptions

- 수집 대상 게시판은 로그인 없이 공개 접근 가능하다 (확인됨).
- 게시판은 SSR 방식이며 정적 HTML 파싱만으로 수집 가능하다 (확인됨).
- 공지 링크는 `javascript:fn_viewData('ID')` 형식이다 (확인됨).
- 호서대학교 게시판 기준 총 약 360페이지, 3,600건 이상의 공지가 존재한다 (확인됨).
- 공지 본문 내 인라인 이미지(`<img>`)와 하단 첨부 파일(다운로드 링크) 두 유형의 자산이 존재한다.
- 이미지 원본 URL 패턴(`/ThumbnailPrint.do` → `/FileDownLoad.do` 또는 유사)은 구현 시 확인 필요.
- 첨부 파일 형식은 PDF, HWP, DOCX, XLSX, 이미지 파일이 주를 이룬다.
- OCR·텍스트 추출 파이프라인은 수집·자산 생성과 별도로 독립 실행된다.
- 자산 파일은 GitHub에 별도 저장하지 않고 원본 URL을 참조한다 (v1).
  원본 서버 접근 불가 시 OCR은 `status:ocr-failed`로 처리한다.
- 지식 베이스는 GitHub Issues로 구성하며 별도 SQL 데이터베이스를 사용하지 않는다.
- CLI 사용자는 터미널에 익숙한 운영자 또는 개발자이다.
- v1 범위: 호서대학교 일반공지 게시판 전용 어댑터.
- v1 범위 외: 분산 크롤링, JS 렌더링(SPA), 인증 게시판, ZIP 내부 파일 처리.
