<!-- Sync Impact Report
Version change: N/A → 1.0.0 (initial ratification)
Modified principles: N/A (initial adoption)
Added sections: Core Principles (I–V), Technology Constraints, Development Workflow, Governance
Removed sections: N/A
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ Constitution Check gates derive from these principles
  - .specify/templates/spec-template.md ✅ No structural changes required
  - .specify/templates/tasks-template.md ✅ No structural changes required
Follow-up TODOs: None — all placeholders resolved
-->

# Notice-Solver Constitution

## Core Principles

### I. Reliable Data Collection

Web crawlers MUST handle network failures, timeouts, and HTTP errors with configurable
retry logic. Crawlers MUST respect `robots.txt` and enforce polite rate limiting
(minimum 1-second delay between requests to the same host). Crawling sessions MUST be
resumable after interruption without duplicating already-collected data.

**Rationale**: Bulletin boards are fragile targets; resilient collection prevents data
gaps and avoids unintentional load on source servers.

### II. Structured Knowledge Representation

Every notice MUST be normalized to the canonical Notice schema
(`title`, `body`, `source_url`, `published_at`, `board_id`, `crawled_at`) before any
storage or indexing operation. Raw HTML MUST NOT be stored as the primary artifact.
Schema changes MUST be versioned and accompanied by a migration.

**Rationale**: Downstream knowledge base queries depend on a consistent shape; ad-hoc
raw-data storage makes search and analysis fragile.

### III. Test-First Development (NON-NEGOTIABLE)

Tests MUST be written before implementation code. Each test MUST fail (red) before the
corresponding implementation is written (green). The Red-Green-Refactor cycle is
mandatory. No feature is complete until all associated tests pass.

**Rationale**: Crawling logic is inherently stateful and timing-dependent; test-first
discipline is the primary defense against silent regressions.

### IV. Incremental Processing

The system MUST support incremental crawl runs that collect only new or updated notices
since the last run. Full re-crawls MUST be opt-in, not the default. Deduplication MUST
use a stable canonical identifier (`source_url` + `published_at`) and MUST be
idempotent across repeated runs.

**Rationale**: Bulletin boards accumulate large archives; full re-crawls waste
resources and inflate the knowledge base with duplicates.

### V. Observability

Every crawl run MUST produce a structured log entry per notice processed
(`status`: collected / skipped / failed, source, timestamp). Aggregated run
statistics (total collected, skipped, failed, duration) MUST be surfaced at run
completion. Errors MUST be logged with sufficient context to reproduce the failure
without code changes.

**Rationale**: Silent failures in background crawling are operationally dangerous;
structured output enables monitoring and debugging at any scale.

## Technology Constraints

- **Primary language**: Python 3.11+
- **Crawling**: `requests` or `httpx`; `BeautifulSoup` or `lxml` for HTML parsing
- **Storage**: Structured format only — SQLite (local/dev) or PostgreSQL (production);
  raw HTML storage as the primary artifact is prohibited
- **Knowledge base indexing**: Full-text search MUST be provided
  (e.g., SQLite FTS5, Elasticsearch, or equivalent)
- **Packaging**: Project MUST be installable as a Python package with a CLI entrypoint
- **Secrets**: Configuration via environment variables or `.env` file;
  secrets MUST NOT be committed to the repository

## Development Workflow

- All feature development MUST occur on a named branch; direct commits to `main`
  are prohibited
- Every pull request MUST include at least one automated test covering the new behavior
- The `main` branch MUST remain deployable (all CI checks passing) at all times
- Complexity beyond what the current feature requires MUST be justified in the PR
  description (YAGNI enforcement)
- Breaking schema changes MUST include a migration script executable without data loss

## Governance

This constitution supersedes all other development guidelines for Notice-Solver.
Amendments require: (1) a written rationale, (2) team agreement, (3) a version bump per
the policy below, and (4) propagation of changes to affected templates and documentation.

Compliance is verified at every `Constitution Check` gate in implementation plans.
Any violation detected during code review MUST be resolved before merge.

**Versioning policy**:
- MAJOR: principle removal or redefinition that breaks backward compatibility
- MINOR: new principle or material section added
- PATCH: wording clarifications, typo fixes, non-semantic refinements

**Version**: 1.0.0 | **Ratified**: 2026-05-09 | **Last Amended**: 2026-05-09
