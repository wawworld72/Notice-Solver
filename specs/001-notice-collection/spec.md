# Feature Specification: 전체 공지사항 수집 시스템

**Feature Branch**: `001-notice-collection`
**Created**: 2026-05-09
**Status**: Draft
**Input**: 게시판 크롤링을 통해 공지사항을 수집하고 지식 베이스(Knowledge Base)화하는 전체 시스템

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 게시판 공지 수집 (Priority: P1)

운영자가 수집 대상 게시판 URL을 등록하면, 시스템이 해당 게시판을 크롤링하여
공지사항 목록을 수집하고 정규화된 형태로 저장한다.

**Why this priority**: 모든 후속 기능의 전제가 되는 핵심 파이프라인이다.
데이터 없이는 검색도, 지식 베이스도 존재하지 않는다.

**Independent Test**: CLI 명령(`specify crawl <URL>`)을 실행하면 공지 목록이
저장소에 저장되고, 저장된 항목 수가 터미널에 출력된다.

**Acceptance Scenarios**:

1. **Given** 유효한 게시판 URL이 등록되어 있을 때,
   **When** 크롤링을 실행하면,
   **Then** 해당 게시판의 공지 목록(제목, 본문, URL, 게시일)이 저장소에 저장된다.

2. **Given** 네트워크 오류가 발생했을 때,
   **When** 크롤링을 실행하면,
   **Then** 재시도를 3회 수행하고, 실패 시 오류 로그와 함께 해당 항목을 건너뛴다.

3. **Given** 이미 수집된 공지가 존재할 때,
   **When** 동일 게시판을 재크롤링하면,
   **Then** 중복 항목은 저장되지 않고 새 공지만 추가된다.

---

### User Story 2 - 증분 크롤링 (Priority: P2)

시스템이 이전 실행 이후 새로 게시된 공지만 수집하여 처리 시간과 리소스를 최소화한다.

**Why this priority**: 대형 게시판은 수천 건의 누적 공지를 보유한다.
전체 재크롤은 비효율적이며, 실운영 환경에서는 증분 수집이 필수적이다.

**Independent Test**: 첫 실행 후 새 공지를 추가한 상태에서 다시 실행하면,
새 공지만 수집되고 기존 공지의 `crawled_at` 값이 변경되지 않는다.

**Acceptance Scenarios**:

1. **Given** 지난 크롤링 기록이 존재할 때,
   **When** 증분 크롤링을 실행하면,
   **Then** 마지막 수집 이후 게시된 공지만 저장된다.

2. **Given** 게시판에 변경 사항이 없을 때,
   **When** 증분 크롤링을 실행하면,
   **Then** "수집 0건 (변경 없음)" 메시지와 함께 정상 종료된다.

---

### User Story 3 - 지식 베이스 검색 (Priority: P3)

사용자가 키워드로 공지를 검색하면, 수집된 공지 중 관련 항목이 정렬된 결과로 반환된다.

**Why this priority**: 수집된 데이터의 활용 가치를 제공하는 기능이다.
P1, P2가 완료된 이후에 의미 있는 테스트가 가능하다.

**Independent Test**: 수집된 공지가 존재하는 상태에서 키워드 검색을 실행하면,
해당 키워드가 제목 또는 본문에 포함된 공지 목록이 출력된다.

**Acceptance Scenarios**:

1. **Given** 공지가 저장소에 존재할 때,
   **When** 키워드로 검색하면,
   **Then** 제목 또는 본문에 키워드를 포함한 공지가 관련도 순으로 반환된다.

2. **Given** 키워드에 매칭되는 공지가 없을 때,
   **When** 검색하면,
   **Then** "결과 없음" 메시지가 출력된다.

---

### User Story 4 - 크롤링 실행 리포트 (Priority: P4)

크롤링 완료 후 운영자에게 수집 건수, 스킵 건수, 실패 건수, 소요 시간을 요약하여 제공한다.

**Why this priority**: 헌법 원칙 V(Observability)를 만족하는 필수 운영 기능이다.
문제 발생 시 진단을 가능하게 한다.

**Independent Test**: 크롤링 실행 후 콘솔에 구조화된 요약이 출력되며,
로그 파일에서도 동일한 통계를 확인할 수 있다.

**Acceptance Scenarios**:

1. **Given** 크롤링이 완료되었을 때,
   **When** 실행 결과를 확인하면,
   **Then** 수집(collected), 스킵(skipped), 실패(failed) 건수와 총 소요 시간이 표시된다.

2. **Given** 일부 공지 수집에 실패했을 때,
   **When** 실행 결과를 확인하면,
   **Then** 실패한 공지의 URL과 오류 사유가 로그에 기록된다.

---

### Edge Cases

- 게시판 구조(HTML)가 변경된 경우 파싱 실패를 감지하고 운영자에게 알린다.
- 게시판이 로그인을 요구하는 경우 인증 설정 없이 접근 시 명확한 오류를 반환한다.
- 동일 게시판을 여러 인스턴스가 동시에 크롤링할 때 중복 저장을 방지한다.
- 매우 긴 본문(1MB 이상)의 공지는 잘림(truncation) 없이 저장하거나, 잘리는 경우 사용자에게 명시한다.
- 게시판 접근이 rate-limit에 의해 차단되면 백오프(backoff) 후 재시도한다.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 시스템은 사용자가 등록한 게시판 URL에서 공지사항 목록을 수집할 수 있어야 한다.
- **FR-002**: 시스템은 각 공지를 정규화된 스키마(제목, 본문, source_url, 게시일, board_id, 수집일)로 저장해야 한다.
- **FR-003**: 시스템은 동일 공지의 중복 저장을 방지해야 한다 (source_url + published_at 기반).
- **FR-004**: 시스템은 증분 크롤링 모드를 지원해야 하며, 기본 동작은 증분이어야 한다.
- **FR-005**: 시스템은 네트워크 오류 발생 시 설정 가능한 재시도 횟수만큼 재시도해야 한다.
- **FR-006**: 시스템은 요청 간 최소 1초의 간격을 두어야 한다 (rate limiting).
- **FR-007**: 시스템은 크롤링 완료 후 수집/스킵/실패 건수 및 소요 시간을 출력해야 한다.
- **FR-008**: 시스템은 수집된 공지에 대해 키워드 전문 검색(full-text search)을 제공해야 한다.
- **FR-009**: 시스템은 CLI 인터페이스를 통해 크롤링 실행, 검색, 설정을 지원해야 한다.
- **FR-010**: 시스템은 robots.txt를 존중하고, 접근 불가 경로는 크롤링하지 않아야 한다.

### Key Entities *(include if feature involves data)*

- **Board (게시판)**: 수집 대상 게시판. 속성: board_id, url, name, last_crawled_at, enabled.
- **Notice (공지)**: 수집된 공지사항. 속성: id, board_id, title, body, source_url, published_at, crawled_at.
- **CrawlRun (크롤링 실행 기록)**: 각 크롤링 실행 결과. 속성: id, board_id, started_at, finished_at, collected, skipped, failed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 운영자가 새 게시판을 등록하고 첫 크롤링을 완료하는 데 5분 이내 소요된다.
- **SC-002**: 증분 크롤링 실행 시, 공지가 없는 게시판은 10초 이내에 "변경 없음"으로 완료된다.
- **SC-003**: 10만 건의 공지가 저장된 상태에서 키워드 검색 결과가 3초 이내 반환된다.
- **SC-004**: 크롤링 도중 네트워크 장애가 발생해도 이미 수집된 데이터는 손실 없이 보존된다.
- **SC-005**: 동일 게시판을 10회 반복 크롤링해도 중복 공지가 저장소에 생성되지 않는다.

## Assumptions

- 수집 대상 게시판은 인터넷에서 공개적으로 접근 가능하다 (로그인 불필요).
- 게시판은 표준 HTML 구조로 렌더링된다 (JavaScript 전용 SPA는 v1 범위 외).
- 단일 서버/로컬 환경에서 실행되며, 분산 크롤링은 v1 범위 외이다.
- 저장소는 로컬 파일시스템 또는 단일 데이터베이스로 구성된다.
- CLI 사용자는 터미널 조작에 익숙한 운영자 또는 개발자이다.
- 게시판별 HTML 파싱 로직은 대상 사이트마다 별도 어댑터로 구현된다.
