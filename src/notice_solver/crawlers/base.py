import asyncio
import logging
import time
from abc import ABC, abstractmethod
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class BaseCrawler(ABC):
    def __init__(self, base_url: str, delay_sec: float = 1.0, retry_count: int = 3) -> None:
        self._base_url = base_url
        self._delay_sec = delay_sec
        self._retry_count = retry_count
        self._robots: RobotFileParser | None = None
        self._last_fetch: float = 0.0
        self._client = httpx.Client(timeout=30.0, follow_redirects=True, headers={
            "User-Agent": "notice-solver/0.1 (+https://github.com/wawworld72/Notice-Solver)"
        })

    def check_robots(self, base_url: str) -> bool:
        robots_url = urljoin(base_url, "/robots.txt")
        self._robots = RobotFileParser()
        self._robots.set_url(robots_url)
        try:
            self._robots.read()
        except Exception:
            self._robots = None
            return True
        return self._robots.can_fetch("*", base_url)

    def fetch(self, url: str) -> str:
        elapsed = time.monotonic() - self._last_fetch
        if elapsed < self._delay_sec:
            time.sleep(self._delay_sec - elapsed)
        self._last_fetch = time.monotonic()

        @retry(
            stop=stop_after_attempt(self._retry_count),
            wait=wait_exponential(multiplier=1, min=2, max=30),
            retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError)),
            reraise=True,
        )
        def _do_fetch():
            response = self._client.get(url)
            response.raise_for_status()
            return response.text

        return _do_fetch()

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    @abstractmethod
    def extract_notice_ids(self, list_html: str) -> list[str]:
        """목록 HTML에서 공지 ID 목록을 추출한다."""

    @abstractmethod
    def parse_notice(self, view_html: str, source_id: str) -> object:
        """공지 상세 HTML을 Notice 객체로 변환한다."""
