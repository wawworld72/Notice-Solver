import mimetypes
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from notice_solver.models.notice import AttachmentRef

_ATTACHMENT_EXTENSIONS = {".pdf", ".hwp", ".hwpx", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".zip", ".txt"}
_MIME_MAP = {
    ".pdf": "application/pdf",
    ".hwp": "application/x-hwp",
    ".hwpx": "application/x-hwpx",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".doc": "application/msword",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xls": "application/vnd.ms-excel",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".zip": "application/zip",
}

# 파일형식 아이콘 등 UI 전용 이미지 제외 패턴
_ICON_URL_RE = re.compile(
    r"/resources/images/icon/|"
    r"/images/ico/|"
    r"icon_\w+\.(png|gif|svg)|"
    r"/static/images/btn|"
    r"/common/images/|"
    r"/skin/|"
    r"/_img/",
    re.IGNORECASE,
)


def extract_image_urls(html: str, base_url: str = "") -> list[str]:
    if not html:
        return []
    soup = BeautifulSoup(html, "lxml")
    urls = []
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if not src:
            continue
        if base_url and not src.startswith("http"):
            src = urljoin(base_url, src)
        if not src.startswith("http"):
            continue
        if _ICON_URL_RE.search(src):
            continue
        urls.append(src)
    return urls


def extract_attachment_refs(html: str, base_url: str = "") -> list[AttachmentRef]:
    if not html:
        return []
    soup = BeautifulSoup(html, "lxml")
    refs = []
    seen_urls: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href:
            continue
        if base_url and not href.startswith("http"):
            href = urljoin(base_url, href)

        parsed = urlparse(href)
        path = parsed.path.lower()
        ext = _get_extension(path, a.get_text(strip=True))
        if not ext:
            continue
        if href in seen_urls:
            continue
        seen_urls.add(href)

        filename = _guess_filename(a.get_text(strip=True), path) or path.rsplit("/", 1)[-1]
        mime_type = _MIME_MAP.get(ext) or mimetypes.guess_type(filename)[0] or "application/octet-stream"
        refs.append(AttachmentRef(url=href, filename=filename, mime_type=mime_type))
    return refs


def _get_extension(path: str, link_text: str) -> str:
    for ext in _ATTACHMENT_EXTENSIONS:
        if path.endswith(ext):
            return ext
    for ext in _ATTACHMENT_EXTENSIONS:
        if ext in link_text.lower():
            return ext
    return ""


def _guess_filename(link_text: str, path: str) -> str:
    for ext in _ATTACHMENT_EXTENSIONS:
        if link_text.lower().endswith(ext):
            return link_text.strip()
    return path.rsplit("/", 1)[-1] if "/" in path else link_text.strip()
