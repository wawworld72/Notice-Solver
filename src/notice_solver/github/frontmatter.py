import re
from datetime import datetime

import yaml

from notice_solver.models.asset import Asset
from notice_solver.models.notice import Notice

_NOTICE_META_RE = re.compile(r"<!--\s*NOTICE_META\s*\n(.*?)\n-->", re.DOTALL)
_ASSET_META_RE = re.compile(r"<!--\s*ASSET_META\s*\n(.*?)\n-->", re.DOTALL)


def parse_notice_meta(body: str) -> dict:
    m = _NOTICE_META_RE.search(body)
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}


def parse_asset_meta(body: str) -> dict:
    m = _ASSET_META_RE.search(body)
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}


def render_notice_body(notice: Notice) -> str:
    image_lines = "\n".join(
        f"![이미지 {i+1}]({url})" for i, url in enumerate(notice.image_urls)
    ) or "_없음_"
    attach_lines = "\n".join(
        f"- attach-{i+1:03d}: `{a.url}` | `{a.filename}` | `{a.mime_type}`"
        for i, a in enumerate(notice.attachments)
    ) or "_없음_"

    published = notice.published_at.strftime("%Y-%m-%d") if isinstance(notice.published_at, datetime) else str(notice.published_at)
    crawled = notice.crawled_at.isoformat() if isinstance(notice.crawled_at, datetime) else str(notice.crawled_at)
    year = notice.published_at.year if isinstance(notice.published_at, datetime) else ""

    meta_yaml = (
        f"id: {notice.notice_id}\n"
        f"board_id: {notice.board_id}\n"
        f"title: {notice.title}\n"
        f"author: {notice.author}\n"
        f"published_at: {published}\n"
        f"crawled_at: {crawled}\n"
        f"source_url: {notice.source_url}\n"
        f"year: {year}\n"
        f"image_count: {len(notice.image_urls)}\n"
        f"attachment_count: {len(notice.attachments)}\n"
        f"phase: {notice.phase}"
    )

    return (
        f"<!-- NOTICE_META\n{meta_yaml}\n-->\n\n"
        f"## 공지 내용\n\n{notice.body_text}\n\n"
        f"## 자산 목록\n\n"
        f"### 인라인 이미지\n{image_lines}\n\n"
        f"### 첨부 파일\n{attach_lines}\n\n"
        f"## 원본\n\n"
        f"- **출처**: [{notice.source_url}]({notice.source_url})\n"
        f"- **게시판**: {notice.board_id} | **작성자**: {notice.author} | **게시일**: {published}\n"
    )


def render_asset_body(asset: Asset) -> str:
    if asset.type == "image":
        meta_yaml = (
            f"asset_id: {asset.asset_id}\n"
            f"type: {asset.type}\n"
            f"parent_notice_id: {asset.parent_notice_id}\n"
            f"parent_issue_number: {asset.parent_issue_number}\n"
            f"sequence: {asset.sequence}\n"
            f"total_in_notice: {asset.total_in_notice}\n"
            f"src_url: {asset.src_url}\n"
            f"full_url: {asset.full_url}\n"
            f"ocr_status: {asset.ocr_status}"
        )
        body = (
            f"<!-- ASSET_META\n{meta_yaml}\n-->\n\n"
            f"**공지**: #{asset.parent_issue_number}\n"
            f"**이미지**: {asset.sequence}/{asset.total_in_notice}\n\n"
            f"---\n\n## OCR 결과\n\n_미처리 (`status:raw`)_\n"
        )
    else:
        meta_yaml = (
            f"asset_id: {asset.asset_id}\n"
            f"type: {asset.type}\n"
            f"parent_notice_id: {asset.parent_notice_id}\n"
            f"parent_issue_number: {asset.parent_issue_number}\n"
            f"sequence: {asset.sequence}\n"
            f"total_in_notice: {asset.total_in_notice}\n"
            f"src_url: {asset.src_url}\n"
            f"filename: {asset.filename}\n"
            f"mime_type: {asset.mime_type}\n"
            f"ocr_status: {asset.ocr_status}"
        )
        body = (
            f"<!-- ASSET_META\n{meta_yaml}\n-->\n\n"
            f"**공지**: #{asset.parent_issue_number}\n"
            f"**파일**: `{asset.filename}` ({asset.mime_type}) | **첨부**: {asset.sequence}/{asset.total_in_notice}\n\n"
            f"---\n\n## 텍스트 추출 결과\n\n_미처리 (`status:raw`)_\n"
        )
    return body
