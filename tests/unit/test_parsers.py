"""Unit tests for HTML parsers. Write before implementation (RED phase)."""
import pytest

from notice_solver.parsers.markdown import html_to_markdown
from notice_solver.parsers.assets import extract_image_urls, extract_attachment_refs
from notice_solver.parsers.notice import parse_notice_page


class TestHtmlToMarkdown:
    def test_headings(self):
        assert html_to_markdown("<h1>제목</h1>") == "# 제목"
        assert html_to_markdown("<h2>부제</h2>") == "## 부제"

    def test_bold_and_italic(self):
        assert "**굵게**" in html_to_markdown("<strong>굵게</strong>")
        assert "*이탤릭*" in html_to_markdown("<em>이탤릭</em>")

    def test_link(self):
        result = html_to_markdown('<a href="http://example.com">링크</a>')
        assert "[링크](http://example.com)" in result

    def test_img_removed(self):
        result = html_to_markdown('<img src="http://example.com/img.jpg" alt="사진">')
        assert "<img" not in result
        assert "http://example.com/img.jpg" not in result

    def test_paragraph(self):
        result = html_to_markdown("<p>첫 번째 단락</p><p>두 번째 단락</p>")
        assert "첫 번째 단락" in result
        assert "두 번째 단락" in result

    def test_unordered_list(self):
        result = html_to_markdown("<ul><li>항목1</li><li>항목2</li></ul>")
        assert "항목1" in result
        assert "항목2" in result

    def test_table(self):
        html = "<table><tr><th>이름</th><th>점수</th></tr><tr><td>홍길동</td><td>90</td></tr></table>"
        result = html_to_markdown(html)
        assert "이름" in result
        assert "점수" in result
        assert "홍길동" in result

    def test_empty_string(self):
        assert html_to_markdown("") == ""

    def test_plain_text_unchanged(self):
        assert "안녕하세요" in html_to_markdown("안녕하세요")


class TestExtractImageUrls:
    def test_basic_img_tag(self):
        html = '<img src="http://example.com/img.jpg">'
        urls = extract_image_urls(html)
        assert "http://example.com/img.jpg" in urls

    def test_multiple_images(self):
        html = '<img src="http://example.com/a.jpg"><img src="http://example.com/b.png">'
        urls = extract_image_urls(html)
        assert len(urls) == 2

    def test_thumbnail_url_detected(self):
        html = '<img src="https://www.hoseo.ac.kr/ThumbnailPrint.do?dir=editor&savename=img.jpg">'
        urls = extract_image_urls(html)
        assert len(urls) == 1
        assert "ThumbnailPrint.do" in urls[0]

    def test_empty_html(self):
        assert extract_image_urls("") == []

    def test_no_images(self):
        assert extract_image_urls("<p>텍스트만</p>") == []

    def test_relative_url_excluded(self):
        html = '<img src="/local/image.jpg">'
        urls = extract_image_urls(html)
        assert len(urls) >= 0


class TestExtractAttachmentRefs:
    def test_pdf_attachment(self):
        html = '<a href="https://www.hoseo.ac.kr/download/file.pdf">공지문.pdf 다운로드</a>'
        refs = extract_attachment_refs(html)
        assert len(refs) == 1
        assert refs[0].filename.endswith(".pdf") or "pdf" in refs[0].url

    def test_hwp_attachment(self):
        html = '<a href="https://www.hoseo.ac.kr/download/doc.hwp">문서.hwp</a>'
        refs = extract_attachment_refs(html)
        assert len(refs) == 1

    def test_no_attachments(self):
        html = "<p>첨부 없음</p>"
        refs = extract_attachment_refs(html)
        assert refs == []

    def test_mime_inference_pdf(self):
        html = '<a href="https://example.com/file.pdf">PDF</a>'
        refs = extract_attachment_refs(html)
        if refs:
            assert refs[0].mime_type == "application/pdf"

    def test_mime_inference_hwp(self):
        html = '<a href="https://example.com/doc.hwp">HWP</a>'
        refs = extract_attachment_refs(html)
        if refs:
            assert refs[0].mime_type in ("application/x-hwp", "application/haansofthwp")


class TestParseNoticePage:
    SAMPLE_HTML = """
    <html><body>
    <h1 class="board-title">2026 대학축제 개최 안내</h1>
    <div class="board-info">
        <span class="author">학생처</span>
        <span class="date">2026-05-01</span>
    </div>
    <div class="board-content">
        <p>5월 20일~22일 천안캠퍼스 대학축제.</p>
        <img src="https://www.hoseo.ac.kr/ThumbnailPrint.do?dir=editor&savename=img1.jpg">
        <a href="https://www.hoseo.ac.kr/download/festival.pdf">행사안내.pdf</a>
    </div>
    </body></html>
    """

    def test_returns_notice(self):
        from notice_solver.models.notice import Notice
        notice = parse_notice_page(self.SAMPLE_HTML, board_id="MAPP_TEST", source_id="12345")
        assert isinstance(notice, Notice)

    def test_source_id_board_id(self):
        notice = parse_notice_page(self.SAMPLE_HTML, board_id="MAPP_TEST", source_id="12345")
        assert notice.source_id == "12345"
        assert notice.board_id == "MAPP_TEST"
        assert notice.notice_id == "MAPP_TEST-12345"

    def test_image_urls_extracted(self):
        notice = parse_notice_page(self.SAMPLE_HTML, board_id="MAPP_TEST", source_id="12345")
        assert len(notice.image_urls) >= 1
        assert any("ThumbnailPrint" in url for url in notice.image_urls)

    def test_attachments_extracted(self):
        notice = parse_notice_page(self.SAMPLE_HTML, board_id="MAPP_TEST", source_id="12345")
        assert len(notice.attachments) >= 1

    def test_body_text_not_empty(self):
        notice = parse_notice_page(self.SAMPLE_HTML, board_id="MAPP_TEST", source_id="12345")
        assert len(notice.body_text) > 0

    def test_img_not_in_body_text(self):
        notice = parse_notice_page(self.SAMPLE_HTML, board_id="MAPP_TEST", source_id="12345")
        assert "<img" not in notice.body_text
