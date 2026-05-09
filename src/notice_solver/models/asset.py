from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


@dataclass
class Asset:
    asset_id: str
    parent_notice_id: str
    parent_issue_number: int
    type: Literal["image", "attachment"]
    sequence: int
    total_in_notice: int
    src_url: str
    full_url: str = ""
    filename: str = ""
    mime_type: str = ""
    ocr_status: str = "raw"
    ocr_text: str = ""
    ocr_confidence: float = 0.0
    ocr_processed_at: datetime | None = None
    github_issue_number: int | None = None
