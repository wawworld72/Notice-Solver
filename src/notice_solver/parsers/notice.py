import re
from datetime import datetime, timezone

from bs4 import BeautifulSoup, NavigableString

from notice_solver.models.notice import Notice
from notice_solver.parsers.assets import extract_attachment_refs, extract_image_urls
from notice_solver.parsers.markdown import html_to_markdown

_DATE_PATTERNS = [
    r"\d{4}-\d{2}-\d{2}",
    r"\d{4}\.\d{2}\.\d{2}",
    r"\d{4}/\d{2}/\d{2}",
]

_JS_NAV_RE = re.compile(r"javascript:fn_(selectCategory|print)\(")


def parse_notice_page(html: str, board_id: str, source_id: str, base_url: str = "") -> Notice:
    soup = BeautifulSoup(html, "lxml")

    # 본문 먼저 추출 → 네비게이션과 분리된 컨텍스트에서 메타 파싱
    content_html = _extract_content_html(soup)
    content_soup = BeautifulSoup(content_html, "lxml")

    title = _extract_title(content_soup) or f"[공지 {source_id}]"
    author = _extract_author(content_soup)
    published_at = _extract_date(content_soup)

    image_urls = extract_image_urls(content_html, base_url=base_url)
    attachments = extract_attachment_refs(content_html, base_url=base_url)
    body_html = _extract_body_html(content_soup)
    body_text = html_to_markdown(body_html)

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
    # 한국 BBS: <th>제목</th> → sibling <td>
    for th in soup.find_all("th"):
        if th.get_text(strip=True) in ("제목", "Title", "SUBJECT", "제 목"):
            td = th.find_next_sibling("td")
            if td:
                t = td.get_text(strip=True)
                if t:
                    return t

    for selector in [
        ".board-title", ".boardTitle", ".view-title", ".viewTitle",
        ".view_title", ".viewSubject", ".view_subject",
        ".subject", ".bbs-title", ".bbs_title",
        ".notice-title", ".noticeTitle",
        "#subject", "#title", "#viewTitle",
        "h1.subject", "h2.subject", "h3.subject",
        "h1.title", "h2.title",
        "h1", "h2", "h3", "h4", "h5",
        "td.subject", "th.subject", "td.title", "th.title",
        "table.bbsView td.subject", "table.view td.subject",
        "title",
    ]:
        el = soup.select_one(selector)
        if el:
            text = el.get_text(strip=True)
            if selector == "title" and " - " in text:
                text = text.split(" - ")[0].strip()
            if text:
                return text
    return ""


def _extract_author(soup: BeautifulSoup) -> str:
    # 호서대 패턴: <strong>작성자</strong> 또는 <th>작성자</th>
    for tag in soup.find_all(["strong", "b", "th"]):
        if tag.get_text(strip=True) in ("작성자", "Writer", "작 성 자"):
            if tag.name == "th":
                td = tag.find_next_sibling("td")
                if td:
                    t = td.get_text(strip=True)
                    if t:
                        return t
            else:
                for sib in tag.next_siblings:
                    t = sib.get_text(strip=True) if hasattr(sib, "get_text") else str(sib).strip()
                    if t:
                        return t

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


def _strip_js_nav(el: BeautifulSoup) -> None:
    """카테고리 선택/PRINT/조회수 등 UI 전용 요소 in-place 제거."""
    # fn_selectCategory 링크만 있는 <ul>/<ol> 제거
    for ul in list(el.find_all(["ul", "ol"])):
        links = ul.find_all("a")
        if links and all(_JS_NAV_RE.search(a.get("href") or "") for a in links):
            ul.decompose()
    # JS 전용 단독 링크 제거 (fn_print, fn_selectCategory, fn_fileView)
    for a in list(el.find_all("a")):
        href = a.get("href") or ""
        if _JS_NAV_RE.search(href):
            a.decompose()
    # 조회수 표시 제거 (<strong>조회수</strong> 또는 <th>조회수</th> 행)
    for tag in list(el.find_all(["strong", "b", "th"])):
        if tag.get_text(strip=True) in ("조회수", "조 회 수", "Views", "Hit", "Hits"):
            parent = tag.parent
            if parent and parent.name == "tr":
                parent.decompose()
            else:
                sib = tag.next_sibling
                if sib and isinstance(sib, NavigableString) and sib.strip():
                    sib.extract()
                tag.decompose()
    # JS 전용 단독 링크 제거
    for a in list(el.find_all("a")):
        href = a.get("href") or ""
        if _JS_NAV_RE.search(href):
            a.decompose()


_META_LABELS = frozenset((
    "작성자", "Writer", "작 성 자",
    "등록일자", "등록일", "Date",
    "조회수", "조 회 수", "Views", "Hit", "Hits",
))


def _strip_dl_wrappers(el: BeautifulSoup) -> None:
    """<dl><dt>내용</dt><dd>text</dd></dl> → <p>text</p> 변환 (마크다운 정의 목록 제거)."""
    for dl in list(el.find_all("dl")):
        for dt in list(dl.find_all("dt")):
            dt.decompose()
        for dd in list(dl.find_all("dd")):
            dd.name = "p"
        dl.unwrap()


def _extract_body_html(soup: BeautifulSoup) -> str:
    """공지 본문만 추출 — 제목·작성자·날짜·조회수 제외."""
    # bbsView 테이블 구조: bbs-content td 또는 colspan td
    bbs_td = soup.select_one("td.bbs-content, td.bbsContent, td.bbs_content")
    if not bbs_td:
        for td in soup.find_all("td", attrs={"colspan": True}):
            bbs_td = td
            break
    if bbs_td:
        inner = BeautifulSoup(str(bbs_td), "lxml")
        _strip_js_nav(inner)
        _strip_dl_wrappers(inner)
        return str(inner)

    # h5/strong 구조: 제목 헤딩 + 메타 라벨과 이어지는 텍스트 노드 제거
    body_copy = BeautifulSoup(str(soup), "lxml")
    for tag in list(body_copy.find_all(["h1", "h2", "h3", "h4", "h5"])):
        tag.decompose()
    for tag in list(body_copy.find_all(["strong", "b", "th"])):
        if tag.get_text(strip=True) in _META_LABELS:
            sib = tag.next_sibling
            while sib and (isinstance(sib, NavigableString) or
                           (hasattr(sib, "name") and sib.name in ("br", "span"))):
                next_s = sib.next_sibling
                sib.extract()
                sib = next_s
            tag.decompose()
    _strip_dl_wrappers(body_copy)
    return str(body_copy)


def _extract_content_html(soup: BeautifulSoup) -> str:
    for selector in [
        # 넓은 컨테이너 우선 (title 테이블 행 포함)
        ".bbs-view", ".bbsView", ".board-view", ".boardView",
        ".board-content", ".boardContent", ".board_content",
        ".view-content", ".viewContent", ".view_content",
        ".view-body", ".viewBody", ".board-body", ".boardBody",
        "#view_content", "#viewContent", "#bbsContent",
        "article", "main",
        "#content", ".content",
        # 테이블 셀은 마지막 (좁은 범위)
        ".bbs-content", ".bbsContent", ".bbs_content",
        "td.content", "td.bbs-content", "td.boardContent",
    ]:
        el = soup.select_one(selector)
        if el:
            target = BeautifulSoup(str(el), "lxml")
            _strip_js_nav(target)
            return str(target)
    # 폴백: 좌측 메뉴 등 네비게이션 요소 제거 후 body 반환
    body = soup.find("body")
    if body:
        body_copy = BeautifulSoup(str(body), "lxml").find("body")
        if body_copy:
            for sel in _NAV_STRIP:
                for nav_el in body_copy.select(sel):
                    nav_el.decompose()
            _strip_js_nav(body_copy)
            return str(body_copy)
    return str(soup)
