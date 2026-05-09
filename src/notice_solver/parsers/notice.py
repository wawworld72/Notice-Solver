import re
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from notice_solver.models.notice import Notice
from notice_solver.parsers.assets import extract_attachment_refs, extract_image_urls
from notice_solver.parsers.markdown import html_to_markdown

_DATE_PATTERNS = [
    r"\d{4}-\d{2}-\d{2}",
    r"\d{4}\.\d{2}\.\d{2}",
    r"\d{4}/\d{2}/\d{2}",
]


def parse_notice_page(html: str, board_id: str, source_id: str) -> Notice:
    soup = BeautifulSoup(html, "lxml")

    title = _extract_title(soup)
    author = _extract_author(soup)
    published_at = _extract_date(soup)
    content_html = _extract_content_html(soup)

    image_urls = extract_image_urls(str(soup), base_url="")
    attachments = extract_attachment_refs(str(soup), base_url="")
    body_text = html_to_markdown(content_html)

    return Notice(
        source_id=source_id,
        board_id=board_id,
        title=title,
        body_text=body_text,
        source_url="",
        published_at=published_at,
        crawled_at=datetime.now(timezone.utc),
        author=author,
        image_urls=image_urls,
        attachments=attachments,
    )


def _extract_title(soup: BeautifulSoup) -> str:
    for selector in [
        "h1.board-title", "h2.board-title", ".board-title",
        "h1.subject", ".subject", "h1", "title",
    ]:
        el = soup.select_one(selector)
        if el:
            return el.get_text(strip=True)
    return ""


def _extract_author(soup: BeautifulSoup) -> str:
    for selector in [
        ".author", ".writer", "[class*='author']", "[class*='writer']",
        "td.writer", "span.writer",
    ]:
        el = soup.select_one(selector)
        if el:
            return el.get_text(strip=True)
    return ""


def _extract_date(soup: BeautifulSoup) -> datetime:
    for selector in [".date", ".reg-date", "[class*='date']", "td.date"]:
        el = soup.select_one(selector)
        if el:
            text = el.get_text(strip=True)
            dt = _parse_date_str(text)
            if dt:
                return dt
    full_text = soup.get_text()
    for pattern in _DATE_PATTERNS:
        m = re.search(pattern, full_text)
        if m:
            dt = _parse_date_str(m.group(0))
            if dt:
                return dt
    return datetime.now(timezone.utc)


def _parse_date_str(text: str) -> datetime | None:
    normalized = re.sub(r"[./]", "-", text.strip())
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(normalized[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return None


def _extract_content_html(soup: BeautifulSoup) -> str:
    for selector in [
        ".board-content", ".content", ".view-content",
        "#content", ".bbs-content", "article",
    ]:
        el = soup.select_one(selector)
        if el:
            return str(el)
    body = soup.find("body")
    return str(body) if body else str(soup)
