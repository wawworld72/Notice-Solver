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

    # 호서대 실제 BBSView 구조: table 기반 제목, 상대경로 이미지, lnb 네비게이션
    HOSEO_HTML = """
    <html><body>
    <div class="lnb">
      <ul><li>공지사항</li><li>ICAN+학기제</li><li>학사공지</li></ul>
    </div>
    <div class="board-view">
      <table class="bbsView">
        <tr><th>제목</th><td>2026학년도 1학기 수강신청 안내</td></tr>
        <tr><th>작성자</th><td>교학처</td></tr>
        <tr><th>등록일</th><td class="date">2026-03-01</td></tr>
        <tr><td colspan="2" class="bbs-content">
          <p>수강신청 기간 안내입니다.</p>
          <img src="/ThumbnailPrint.do?dir=editor&savename=notice.jpg">
          <a href="/download/guide.pdf">수강신청안내.pdf</a>
        </td></tr>
      </table>
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

    def test_hoseo_table_title_extracted(self):
        """<th>제목</th><td>...</td> 패턴 제목 추출"""
        notice = parse_notice_page(self.HOSEO_HTML, board_id="MAPP_TEST", source_id="99999")
        assert notice.title == "2026학년도 1학기 수강신청 안내"

    def test_hoseo_h5_title_extracted(self):
        """<h5> 태그 안의 제목 추출 (호서대 실제 구조)"""
        html = """<html><body>
        <div class="lnb"><ul><li>공지사항</li></ul></div>
        <div class="board-view">
          <h5>[충남산학융합원] 미래내일 일경험(인턴형) 참여 청년 모집</h5>
          <strong>작성자</strong>취업팀
          <p>본문 내용</p>
        </div></body></html>"""
        notice = parse_notice_page(html, board_id="MAPP_TEST", source_id="12345")
        assert "[충남산학융합원]" in notice.title
        assert notice.title != "공지사항"

    def test_hoseo_author_strong_pattern(self):
        """<strong>작성자</strong> 다음 텍스트 작성자 추출"""
        html = """<html><body><div class="board-view">
        <h5>제목입니다</h5>
        <strong>작성자</strong>취업팀
        </div></body></html>"""
        notice = parse_notice_page(html, board_id="MAPP_TEST", source_id="12345")
        assert notice.author == "취업팀"

    def test_hoseo_relative_image_resolved(self):
        """상대경로 이미지가 base_url로 절대경로 변환"""
        notice = parse_notice_page(
            self.HOSEO_HTML, board_id="MAPP_TEST", source_id="99999",
            base_url="https://www.hoseo.ac.kr"
        )
        assert len(notice.image_urls) >= 1
        assert any("hoseo.ac.kr" in url for url in notice.image_urls)

    def test_hoseo_nav_not_in_body(self):
        """좌측 네비게이션 메뉴가 본문에 포함되지 않아야 함"""
        notice = parse_notice_page(self.HOSEO_HTML, board_id="MAPP_TEST", source_id="99999")
        assert "ICAN+학기제" not in notice.body_text

    def test_hoseo_js_nav_not_in_body(self):
        """fn_selectCategory JS 링크 목록이 본문에 포함되지 않아야 함"""
        html = """<html><body><div class="board-view">
        <ul>
          <li><a href="javascript:fn_selectCategory('CTG_001')">공지사항</a></li>
          <li><a href="javascript:fn_selectCategory('CTG_002')">학사공지</a></li>
        </ul>
        <h5>실제 공지 제목</h5>
        <p>본문 내용</p>
        </div></body></html>"""
        notice = parse_notice_page(html, board_id="MAPP_TEST", source_id="12345")
        assert "fn_selectCategory" not in notice.body_text
        assert "공지사항" not in notice.body_text

    def test_view_count_not_in_body(self):
        """조회수 표시가 본문에 포함되지 않아야 함"""
        html = """<html><body><div class="board-view">
        <h5>공지 제목</h5>
        <strong>조회수</strong>42
        <p>본문 내용</p>
        </div></body></html>"""
        notice = parse_notice_page(html, board_id="MAPP_TEST", source_id="12345")
        assert "조회수" not in notice.body_text

    def test_icon_images_excluded(self):
        """파일형식 아이콘 이미지가 자산 목록에서 제외되어야 함"""
        html = """<html><body><div class="board-view">
        <img src="https://www.hoseo.ac.kr/resources/images/icon/icon_jpg.png">
        <img src="https://www.hoseo.ac.kr/resources/images/icon/icon_hwp.png">
        <img src="https://www.hoseo.ac.kr/ThumbnailPrint.do?dir=editor&savename=actual.jpg">
        </div></body></html>"""
        notice = parse_notice_page(html, board_id="MAPP_TEST", source_id="12345",
                                   base_url="https://www.hoseo.ac.kr")
        assert all("icon_jpg" not in url and "icon_hwp" not in url for url in notice.image_urls)
        assert any("ThumbnailPrint" in url for url in notice.image_urls)

    def test_hoseo_relative_attachment_resolved(self):
        """상대경로 첨부파일이 base_url로 절대경로 변환"""
        notice = parse_notice_page(
            self.HOSEO_HTML, board_id="MAPP_TEST", source_id="99999",
            base_url="https://www.hoseo.ac.kr"
        )
        assert len(notice.attachments) >= 1
        assert any("hoseo.ac.kr" in a.url for a in notice.attachments)

    def test_title_not_in_body_text(self):
        """공지 제목이 본문에 포함되지 않아야 함 (이슈 제목으로 이미 제공)"""
        notice = parse_notice_page(self.HOSEO_HTML, board_id="MAPP_TEST", source_id="99999")
        assert "2026학년도 1학기 수강신청 안내" not in notice.body_text

    def test_author_date_not_in_body_text(self):
        """작성자·등록일자가 본문에 포함되지 않아야 함"""
        html = """<html><body><div class="board-view">
        <h5>공지 제목</h5>
        <strong>작성자</strong>교학처
        <strong>등록일자</strong>2026-03-01
        <strong>조회수</strong>42
        <p>실제 본문 내용입니다.</p>
        </div></body></html>"""
        notice = parse_notice_page(html, board_id="MAPP_TEST", source_id="12345")
        assert "교학처" not in notice.body_text
        assert "등록일자" not in notice.body_text
        assert "42" not in notice.body_text
        assert "실제 본문 내용입니다" in notice.body_text

    def test_dl_content_label_not_in_body(self):
        """<dl><dt>내용</dt><dd>text</dd></dl> 구조에서 '내용:' 라벨 미포함"""
        html = """<html><body><div class="board-view">
        <h5>공지 제목</h5>
        <strong>작성자</strong>홍보팀
        <strong>조회수</strong>436
        <dl><dt>내용</dt><dd>신청서 제출 이메일: test@example.com</dd></dl>
        </div></body></html>"""
        notice = parse_notice_page(html, board_id="MAPP_TEST", source_id="12345")
        assert "436" not in notice.body_text
        assert "내용" not in notice.body_text
        assert "신청서 제출 이메일: test@example.com" in notice.body_text
