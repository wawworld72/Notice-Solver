from ghapi.all import GhApi

LABEL_DEFINITIONS: list[dict] = [
    # Pipeline phase
    {"name": "phase:collection", "color": "0075ca", "description": "Phase 1: 공지 수집 완료"},
    {"name": "phase:organization", "color": "e4e669", "description": "Phase 2: 자산 생성 완료"},
    {"name": "phase:inference", "color": "d93f0b", "description": "Phase 3: 추론 완료"},
    # Asset type
    {"name": "type:asset", "color": "bfd4f2", "description": "자산 Issue (이미지/첨부)"},
    {"name": "asset:image", "color": "c2e0c6", "description": "인라인 이미지 자산"},
    {"name": "asset:attachment", "color": "f9d0c4", "description": "첨부 파일 자산"},
    # OCR status
    {"name": "status:raw", "color": "ededed", "description": "OCR 미처리"},
    {"name": "status:ocr-complete", "color": "0e8a16", "description": "OCR 완료"},
    {"name": "status:ocr-failed", "color": "b60205", "description": "OCR 실패"},
    {"name": "status:no-text", "color": "fbca04", "description": "텍스트 없음"},
    {"name": "status:auth-required", "color": "e11d48", "description": "인증 필요"},
    # Board
    {"name": "board:일반공지", "color": "0052cc", "description": "일반공지 게시판"},
    {"name": "board:장학", "color": "006b75", "description": "장학 게시판"},
    {"name": "board:학사", "color": "5319e7", "description": "학사 게시판"},
    {"name": "board:취업", "color": "1d76db", "description": "취업 게시판"},
    # Category
    {"name": "category:행사", "color": "e99695", "description": "행사 공지"},
    {"name": "category:장학금", "color": "c5def5", "description": "장학금 공지"},
    {"name": "category:학사일정", "color": "bfd4f2", "description": "학사일정 공지"},
    {"name": "category:취업", "color": "fef2c0", "description": "취업 공지"},
    # Year
    {"name": "year:2025", "color": "eeeeee", "description": "2025년"},
    {"name": "year:2026", "color": "dddddd", "description": "2026년"},
    {"name": "year:2027", "color": "cccccc", "description": "2027년"},
    # Semester
    {"name": "semester:spring", "color": "c2e0c6", "description": "봄 학기"},
    {"name": "semester:fall", "color": "f9d0c4", "description": "가을 학기"},
    # Content
    {"name": "has:images", "color": "bfd4f2", "description": "인라인 이미지 포함"},
    {"name": "has:attachments", "color": "fef2c0", "description": "첨부 파일 포함"},
    {"name": "has:no-assets", "color": "f0f0f0", "description": "자산 없음"},
]


def ensure_labels(api: GhApi, owner: str, repo: str) -> tuple[int, int]:
    """Create missing labels. Returns (created, skipped) counts."""
    existing = {label["name"] for label in api.issues.list_labels_for_repo(owner=owner, repo=repo, per_page=100)}
    created = 0
    skipped = 0
    for label in LABEL_DEFINITIONS:
        if label["name"] not in existing:
            api.issues.create_label(owner=owner, repo=repo, **label)
            created += 1
        else:
            skipped += 1
    return created, skipped
