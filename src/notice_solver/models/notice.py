from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AttachmentRef:
    url: str
    filename: str
    mime_type: str = ""


@dataclass
class Notice:
    source_id: str
    board_id: str
    title: str
    body_text: str
    source_url: str
    published_at: datetime
    crawled_at: datetime
    author: str = ""
    image_urls: list[str] = field(default_factory=list)
    attachments: list[AttachmentRef] = field(default_factory=list)
    github_issue_number: int | None = None
    phase: str = "collection"

    @property
    def notice_id(self) -> str:
        return f"{self.board_id}-{self.source_id}"
