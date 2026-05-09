"""Unit tests for EasyOCR wrapper."""
from unittest.mock import MagicMock, patch

import pytest

from notice_solver.ocr.image import EasyOCRWrapper


class TestEasyOCRWrapper:
    def test_extract_returns_text_and_confidence(self):
        mock_reader = MagicMock()
        mock_reader.readtext.return_value = [
            (None, "안녕하세요", 0.95),
            (None, "hello", 0.88),
        ]
        with patch("notice_solver.ocr.image.easyocr.Reader", return_value=mock_reader):
            wrapper = EasyOCRWrapper(confidence_threshold=0.5)
            text, confidence = wrapper.extract(b"fake_image_bytes")

        assert "안녕하세요" in text
        assert "hello" in text
        assert confidence > 0.5

    def test_low_confidence_filtered(self):
        mock_reader = MagicMock()
        mock_reader.readtext.return_value = [
            (None, "고신뢰", 0.9),
            (None, "저신뢰", 0.2),
        ]
        with patch("notice_solver.ocr.image.easyocr.Reader", return_value=mock_reader):
            wrapper = EasyOCRWrapper(confidence_threshold=0.5)
            text, confidence = wrapper.extract(b"fake_image_bytes")

        assert "고신뢰" in text
        assert "저신뢰" not in text

    def test_empty_image_returns_empty(self):
        mock_reader = MagicMock()
        mock_reader.readtext.return_value = []
        with patch("notice_solver.ocr.image.easyocr.Reader", return_value=mock_reader):
            wrapper = EasyOCRWrapper(confidence_threshold=0.5)
            text, confidence = wrapper.extract(b"blank_image")

        assert text == ""
        assert confidence == 0.0

    def test_all_below_threshold_returns_empty(self):
        mock_reader = MagicMock()
        mock_reader.readtext.return_value = [
            (None, "텍스트", 0.1),
        ]
        with patch("notice_solver.ocr.image.easyocr.Reader", return_value=mock_reader):
            wrapper = EasyOCRWrapper(confidence_threshold=0.5)
            text, confidence = wrapper.extract(b"image")

        assert text == ""
        assert confidence == 0.0

    def test_lazy_initialization(self):
        """Reader는 첫 extract 호출 시에만 초기화된다."""
        with patch("notice_solver.ocr.image.easyocr.Reader") as mock_reader_cls:
            mock_reader_cls.return_value.readtext.return_value = []
            wrapper = EasyOCRWrapper(confidence_threshold=0.5)
            mock_reader_cls.assert_not_called()
            wrapper.extract(b"image")
            mock_reader_cls.assert_called_once()
