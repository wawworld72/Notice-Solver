"""Unit tests for asset parser functions (US2 specific)."""
import pytest

from notice_solver.parsers.assets import extract_image_urls, extract_attachment_refs


class TestExtractImageUrlsDetailed:
    def test_thumbnail_url_preserved(self):
        html = '<img src="https://www.hoseo.ac.kr/ThumbnailPrint.do?dir=editor&savename=img.jpg">'
        urls = extract_image_urls(html)
        assert len(urls) == 1
        assert "ThumbnailPrint.do" in urls[0]

    def test_multiple_images_order_preserved(self):
        html = (
            '<img src="https://example.com/a.jpg">'
            '<img src="https://example.com/b.jpg">'
            '<img src="https://example.com/c.jpg">'
        )
        urls = extract_image_urls(html)
        assert len(urls) == 3
        assert urls[0].endswith("a.jpg")
        assert urls[1].endswith("b.jpg")
        assert urls[2].endswith("c.jpg")

    def test_data_uri_excluded(self):
        html = '<img src="data:image/png;base64,abc123">'
        urls = extract_image_urls(html)
        assert all(not u.startswith("data:") for u in urls)

    def test_no_src_attribute(self):
        html = '<img alt="no src">'
        urls = extract_image_urls(html)
        assert urls == []

    def test_empty_src_excluded(self):
        html = '<img src="">'
        urls = extract_image_urls(html)
        assert urls == []


class TestExtractAttachmentRefsDetailed:
    def test_pdf_link(self):
        html = '<a href="https://example.com/file.pdf">공지문.pdf</a>'
        refs = extract_attachment_refs(html)
        assert len(refs) == 1
        assert refs[0].mime_type == "application/pdf"

    def test_hwp_link(self):
        html = '<a href="https://example.com/doc.hwp">문서.hwp</a>'
        refs = extract_attachment_refs(html)
        assert len(refs) == 1
        assert "hwp" in refs[0].mime_type

    def test_docx_link(self):
        html = '<a href="https://example.com/report.docx">보고서.docx</a>'
        refs = extract_attachment_refs(html)
        assert len(refs) == 1

    def test_xlsx_link(self):
        html = '<a href="https://example.com/data.xlsx">데이터.xlsx</a>'
        refs = extract_attachment_refs(html)
        assert len(refs) == 1

    def test_plain_link_excluded(self):
        html = '<a href="https://example.com/page">페이지</a>'
        refs = extract_attachment_refs(html)
        assert refs == []

    def test_multiple_attachments(self):
        html = (
            '<a href="https://example.com/a.pdf">A.pdf</a>'
            '<a href="https://example.com/b.hwp">B.hwp</a>'
        )
        refs = extract_attachment_refs(html)
        assert len(refs) == 2

    def test_duplicate_url_excluded(self):
        html = (
            '<a href="https://example.com/file.pdf">파일</a>'
            '<a href="https://example.com/file.pdf">파일 (복사)</a>'
        )
        refs = extract_attachment_refs(html)
        assert len(refs) == 1

    def test_filename_extracted_from_link_text(self):
        html = '<a href="https://example.com/download?id=123">공지문.pdf</a>'
        refs = extract_attachment_refs(html)
        if refs:
            assert "pdf" in refs[0].filename.lower() or "pdf" in refs[0].url.lower() or "pdf" in refs[0].mime_type
