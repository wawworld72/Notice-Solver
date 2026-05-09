import io
from typing import Optional

import easyocr


class EasyOCRWrapper:
    def __init__(self, confidence_threshold: float = 0.5) -> None:
        self._threshold = confidence_threshold
        self._reader: Optional[easyocr.Reader] = None

    def _get_reader(self) -> easyocr.Reader:
        if self._reader is None:
            self._reader = easyocr.Reader(["ko", "en"], gpu=False)
        return self._reader

    def extract(self, image_bytes: bytes) -> tuple[str, float]:
        reader = self._get_reader()
        results = reader.readtext(image_bytes)

        texts = []
        confidences = []
        for _, text, confidence in results:
            if confidence >= self._threshold:
                texts.append(text)
                confidences.append(confidence)

        if not texts:
            return "", 0.0

        combined = " ".join(texts)
        avg_confidence = sum(confidences) / len(confidences)
        return combined, avg_confidence
