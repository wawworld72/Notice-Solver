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


def parse_notice_page(html: str, board_id: str, source_id: str, base_url: str = "") -> Notice:
    soup = BeautifulSoup(html, "lxml")

    title = _extract_title(soup) or f"[공지 {source_id}]"
    author = _extract_author(soup)
    published_at = _extract_date(soup)
    content_html = _extract_content_html(soup)

    image_urls = extract_image_urls(content_html, base_url=base_url)
    attachments = extract_attachment_refs(content_html, base_url=base_url)
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
    # 한국 BBS 공통 패턴: <th>제목</th> 옆 <td>
    for th in soup.find_all("th"):
        if th.get_text(strip=True) in ("제목", "Title", "SUBJECT", "제 목"):
            td = th.find_next_sibling("td")
            if td:
                t = td.get_text(strip=True)
                if t:
                    return t

    # 다양한 한국 BBS/JSP 시스템 셀렉터 (호서대 포함)
    for selector in [
        # class 기반
        ".board-title", ".boardTitle", ".view-title", ".viewTitle",
        ".view_title", ".viewSubject", ".view_subject",
        ".subject", ".bbs-title", ".bbs_title",
        ".notice-title", ".noticeTitle",
        # id 기반
        "#subject", "#title", "#viewTitle",
        # heading 기반
        "h1.subject", "h2.subject", "h3.subject",
        "h1.title", "h2.title",
        "h1", "h2",
        # table 기반 (한국 BBS 다수)
        "td.subject", "th.subject", "td.title", "th.title",
        "table.bbsView td.subject", "table.view td.subject",
        # HTML title 태그
        "title",
    ]:
        el = soup.select_one(selector)
        if el:
            text = el.get_text(strip=True)
            # <title> 태그는 사이트명 포함 경우가 많아 일부만 사용
            if selector == "title" and " - " in text:
                text = text.split(" - ")[0].strip()
            if text:
                return text
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


_NAV_STRIP = [
    "header", "footer", "nav",
    ".lnb", "#lnb", ".gnb", "#gnb",
    ".left-menu", ".leftMenu", ".left_menu",
    ".sidebar", "#sidebar",
    ".sub-menu", ".subMenu", "#subMenu",
    ".quick-menu", ".quickMenu",
    ".top-area", ".topArea", "#topArea",
    ".breadcrumb", "#breadcrumb",
    ".banner", "#banner", "#header", "#footer",
]


def _extract_content_html(soup: BeautifulSoup) -> str:
    for selector in [
        ".board-content", ".boardContent", ".board_content",
        ".view-content", ".viewContent", ".view_content",
        ".bbs-content", ".bbsContent", ".bbs_content",
        ".bbs-view", ".bbsView", ".board-view", ".boardView",
        ".view-body", ".viewBody", ".board-body", ".boardBody",
        "#view_content", "#viewContent", "#bbsContent",
        "article", "main",
        "td.content", "td.bbs-content", "td.boardContent",
        "#content", ".content",
    ]:
        el = soup.select_one(selector)
        if el:
            return str(el)
    # 폴백: 좌측 메뉴 등 네비게이션 요소 제거 후 body 반환
    body = soup.find("body")
    if body:
        body_copy = BeautifulSoup(str(body), "lxml").find("body")
        if body_copy:
            for sel in _NAV_STRIP:
                for el in body_copy.select(sel):
                    el.decompose()
            return str(body_copy)
    return str(soup)
