import logging
import re

from notice_solver.crawlers.base import BaseCrawler
from notice_solver.models.notice import Notice
from notice_solver.parsers.notice import parse_notice_page

logger = logging.getLogger(__name__)

BOARD_ID = "MAPP_1708240139"
BASE_URL = "https://www.hoseo.ac.kr"
LIST_URL = f"{BASE_URL}/Home/BBSList.mbz"
VIEW_URL = f"{BASE_URL}/Home/BBSView.mbz"

_FN_VIEW_RE = re.compile(r"javascript:fn_viewData\('(\d+)'\)")
_LAST_PAGE_RE = re.compile(r'<strong[^>]*>(\d+)</strong>')


class HoseoCrawler(BaseCrawler):
    def __init__(self, delay_sec: float = 1.0, retry_count: int = 3) -> None:
        super().__init__(BASE_URL, delay_sec, retry_count)

    def extract_notice_ids(self, list_html: str) -> list[str]:
        return _FN_VIEW_RE.findall(list_html)

    def parse_notice(self, view_html: str, source_id: str) -> Notice:
        notice = parse_notice_page(view_html, board_id=BOARD_ID, source_id=source_id, base_url=BASE_URL)
        notice.source_url = f"{VIEW_URL}?action={BOARD_ID}&schIdx={source_id}"
        return notice

    def crawl_incremental(
        self,
        full: bool = False,
        limit: int = 0,
        known_ids: set[str] | None = None,
    ):
        """공지 Notice 객체를 순서대로 yield한다.

        full=False 이면 known_ids에서 이미 수집된 ID 발견 시 탐색 중단.
        """
        if known_ids is None:
            known_ids = set()

        if not self.check_robots(BASE_URL):
            logger.warning("robots.txt에 의해 크롤링이 제한되어 있습니다.")
            return

        collected = 0
        page = 1

        while True:
            list_html = self.fetch(f"{LIST_URL}?action={BOARD_ID}&pageIndex={page}")
            ids = self.extract_notice_ids(list_html)

            if not ids:
                logger.info(f"페이지 {page}: 공지 없음 — 종료")
                break

            stop_flag = False
            for source_id in ids:
                notice_id = f"{BOARD_ID}-{source_id}"

                if not full and notice_id in known_ids:
                    logger.info(f"기수집 공지 발견: {notice_id} — 증분 탐색 종료")
                    stop_flag = True
                    break

                if notice_id in known_ids:
                    logger.debug(f"스킵 (이미 수집됨): {notice_id}")
                    continue

                try:
                    view_html = self.fetch(f"{VIEW_URL}?action={BOARD_ID}&schIdx={source_id}")
                    notice = self.parse_notice(view_html, source_id)
                    yield notice
                    collected += 1
                    logger.info(f"수집: {notice_id} ({notice.title[:30]})")
                except Exception as e:
                    logger.error(f"수집 실패 {notice_id}: {e}")
                    continue

                if limit > 0 and collected >= limit:
                    logger.info(f"제한 도달 ({limit}건) — 종료")
                    return

            if stop_flag:
                break

            if not _has_next_page(list_html, page):
                break

            page += 1


def _has_next_page(html: str, current_page: int) -> bool:
    next_link = re.search(rf"pageIndex={current_page + 1}", html)
    return bool(next_link)
