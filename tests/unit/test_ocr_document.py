"""Unit tests for document text extractors."""
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

from notice_solver.ocr.document import (
    PdfExtractor, DocxExtractor, XlsxExtractor, HwpExtractor,
    get_extractor, ExtractionError,
)


class TestPdfExtractor:
    def test_extract_text(self, tmp_path):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "PDF 텍스트 내용"
        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = [mock_page]

        with patch("notice_solver.ocr.document.pdfplumber.open", return_value=mock_pdf):
            extractor = PdfExtractor()
            result = extractor.extract(b"fake_pdf_bytes")

        assert "PDF 텍스트 내용" in result

    def test_empty_pdf_returns_empty(self, tmp_path):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = None
        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = [mock_page]

        with patch("notice_solver.ocr.document.pdfplumber.open", return_value=mock_pdf):
            extractor = PdfExtractor()
            result = extractor.extract(b"fake_pdf_bytes")

        assert result == ""


class TestDocxExtractor:
    def test_extract_paragraphs(self):
        mock_para1 = MagicMock()
        mock_para1.text = "첫 번째 단락"
        mock_para2 = MagicMock()
        mock_para2.text = "두 번째 단락"
        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para1, mock_para2]
        mock_doc.tables = []

        with patch("notice_solver.ocr.document.docx.Document", return_value=mock_doc):
            extractor = DocxExtractor()
            result = extractor.extract(b"fake_docx_bytes")

        assert "첫 번째 단락" in result
        assert "두 번째 단락" in result


class TestXlsxExtractor:
    def test_extract_cell_values(self):
        mock_ws = MagicMock()
        mock_ws.iter_rows.return_value = [
            [MagicMock(value="이름"), MagicMock(value="점수")],
            [MagicMock(value="홍길동"), MagicMock(value=90)],
        ]
        mock_wb = MagicMock()
        mock_wb.active = mock_ws

        with patch("notice_solver.ocr.document.openpyxl.load_workbook", return_value=mock_wb):
            extractor = XlsxExtractor()
            result = extractor.extract(b"fake_xlsx_bytes")

        assert "이름" in result
        assert "홍길동" in result


class TestHwpExtractor:
    def test_libreoffice_not_found_raises(self):
        with patch("notice_solver.ocr.document.shutil.which", return_value=None):
            extractor = HwpExtractor()
            with pytest.raises(ExtractionError):
                extractor.extract(b"fake_hwp_bytes")

    def test_successful_conversion(self, tmp_path):
        mock_result = MagicMock()
        mock_result.returncode = 0

        mock_para = MagicMock()
        mock_para.text = "HWP 변환 텍스트"
        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para]
        mock_doc.tables = []

        with patch("notice_solver.ocr.document.shutil.which", return_value="/usr/bin/libreoffice"), \
             patch("notice_solver.ocr.document.subprocess.run", return_value=mock_result), \
             patch("notice_solver.ocr.document.docx.Document", return_value=mock_doc), \
             patch("notice_solver.ocr.document.tempfile.TemporaryDirectory") as mock_tmpdir:
            mock_tmpdir.return_value.__enter__ = MagicMock(return_value=str(tmp_path))
            mock_tmpdir.return_value.__exit__ = MagicMock(return_value=False)
            (tmp_path / "output.docx").write_bytes(b"fake")
            with patch("pathlib.Path.glob", return_value=[tmp_path / "output.docx"]):
                extractor = HwpExtractor()
                result = extractor.extract(b"fake_hwp_bytes")


class TestGetExtractor:
    def test_pdf_mime(self):
        assert isinstance(get_extractor("application/pdf"), PdfExtractor)

    def test_docx_mime(self):
        assert isinstance(get_extractor("application/vnd.openxmlformats-officedocument.wordprocessingml.document"), DocxExtractor)

    def test_xlsx_mime(self):
        assert isinstance(get_extractor("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"), XlsxExtractor)

    def test_hwp_mime(self):
        assert isinstance(get_extractor("application/x-hwp"), HwpExtractor)

    def test_image_returns_none(self):
        assert get_extractor("image/jpeg") is None

    def test_unknown_returns_none(self):
        assert get_extractor("application/unknown-type") is None
