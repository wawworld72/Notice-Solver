import time
from datetime import datetime, timezone

from ghapi.all import GhApi

from notice_solver.github.frontmatter import render_asset_body, render_notice_body
from notice_solver.models.asset import Asset
from notice_solver.models.notice import Notice


class GitHubIssues:
    def __init__(self, token: str, owner: str, repo: str) -> None:
        self._api = GhApi(owner=owner, repo=repo, token=token)
        self._owner = owner
        self._repo = repo

    def create_notice_issue(self, notice: Notice) -> int:
        body = render_notice_body(notice)
        labels = self._notice_labels(notice)
        for label in labels:
            if label.startswith("author:"):
                self._ensure_label(label, color="c5def5", description=f"작성자: {label[7:]}")
        issue = self._api.issues.create(
            owner=self._owner,
            repo=self._repo,
            title=notice.title,
            body=body,
            labels=labels,
        )
        return issue["number"]

    def update_notice_issue(self, number: int, body: str, labels: list[str]) -> None:
        self._api.issues.update(
            owner=self._owner,
            repo=self._repo,
            issue_number=number,
            body=body,
            labels=labels,
        )

    def create_asset_issue(self, asset: Asset, notice_title: str = "") -> int:
        body = render_asset_body(asset)
        asset_type_label = f"asset:{asset.type}"
        title = f"[자산] {asset.asset_id}"
        if notice_title:
            title = f"[자산] {notice_title} — {'이미지' if asset.type == 'image' else '첨부'} {asset.sequence}/{asset.total_in_notice}"
        issue = self._api.issues.create(
            owner=self._owner,
            repo=self._repo,
            title=title,
            body=body,
            labels=["type:asset", asset_type_label, "status:raw"],
        )
        return issue["number"]

    def update_asset_issue(self, number: int, ocr_text: str, status: str, confidence: float = 0.0) -> None:
        issue = self.get_issue(number)
        body = issue["body"] or ""
        now = datetime.now(timezone.utc).isoformat()
        if status == "ocr-complete":
            ocr_section = (
                f"## OCR 결과\n\n"
                f"**처리일**: {now}\n"
                f"**신뢰도**: {confidence:.2f}\n\n"
                f"```text\n{ocr_text}\n```\n"
            )
        elif status == "no-text":
            ocr_section = f"## OCR 결과\n\n_텍스트 없음 (`status:no-text`)_\n"
        else:
            ocr_section = f"## OCR 결과\n\n_처리 실패 (`status:{status}`)_\n"

        import re
        body = re.sub(r"## (OCR 결과|텍스트 추출 결과).*$", ocr_section, body, flags=re.DOTALL)

        existing_labels = [lbl["name"] for lbl in issue.get("labels", [])]
        new_labels = [l for l in existing_labels if not l.startswith("status:")] + [f"status:{status}"]

        self._api.issues.update(
            owner=self._owner,
            repo=self._repo,
            issue_number=number,
            body=body,
            labels=new_labels,
        )

    def list_issues(self, labels: str = "", state: str = "open", limit: int = 100) -> list[dict]:
        results = []
        page = 1
        while len(results) < limit:
            per_page = min(100, limit - len(results))
            batch = self._api.issues.list_for_repo(
                owner=self._owner,
                repo=self._repo,
                labels=labels,
                state=state,
                per_page=per_page,
                page=page,
            )
            if not batch:
                break
            results.extend(batch)
            if len(batch) < per_page:
                break
            page += 1
        return results

    def get_issue(self, number: int) -> dict:
        return self._api.issues.get(owner=self._owner, repo=self._repo, issue_number=number)

    def update_notice_body_with_assets(self, number: int, asset_issues: list[dict]) -> None:
        issue = self.get_issue(number)
        body = issue["body"] or ""
        table_rows = "\n".join(
            f"| #{a['number']} | {a.get('type', '')} | {a.get('seq', '')} | {a.get('status', 'raw')} |"
            for a in asset_issues
        )
        asset_table = (
            "| Issue | 유형 | 순서 | 상태 |\n"
            "|-------|------|------|------|\n"
            f"{table_rows}"
        )
        import re
        body = re.sub(r"## 자산 목록.*?(?=## |$)", f"## 자산 목록\n\n{asset_table}\n\n", body, flags=re.DOTALL)
        existing_labels = [lbl["name"] for lbl in issue.get("labels", [])]
        new_labels = [l for l in existing_labels if l != "phase:collection"] + ["phase:organization"]
        self._api.issues.update(
            owner=self._owner,
            repo=self._repo,
            issue_number=number,
            body=body,
            labels=new_labels,
        )

    def get_known_notice_ids(self) -> dict[str, int]:
        """GitHub Issues에서 기수집 공지 ID 목록을 반환한다. {notice_id: issue_number}"""
        from notice_solver.github.frontmatter import parse_notice_meta
        issues = self.list_issues(labels="type:notice", state="open", limit=5000)
        result: dict[str, int] = {}
        for issue in issues:
            meta = parse_notice_meta(issue.get("body") or "")
            notice_id = meta.get("id")
            if notice_id:
                result[notice_id] = issue["number"]
        return result

    def list_asset_issues(self, parent_notice_id: str) -> list[dict]:
        all_issues = self.list_issues(labels="type:asset", state="open", limit=500)
        results = []
        from notice_solver.github.frontmatter import parse_asset_meta
        for issue in all_issues:
            meta = parse_asset_meta(issue.get("body") or "")
            if meta.get("parent_notice_id") == parent_notice_id:
                results.append(issue)
        return results

    def _notice_labels(self, notice: Notice) -> list[str]:
        labels = ["type:notice", f"phase:{notice.phase}"]
        if notice.image_urls:
            labels.append("has:images")
        if notice.attachments:
            labels.append("has:attachments")
        if not notice.image_urls and not notice.attachments:
            labels.append("has:no-assets")
        if isinstance(notice.published_at, datetime):
            labels.append(f"year:{notice.published_at.year}")
        if notice.author:
            labels.append(f"author:{notice.author}")
        return labels

    def _ensure_label(self, name: str, color: str = "ededed", description: str = "") -> None:
        try:
            self._api.issues.get_label(owner=self._owner, repo=self._repo, name=name)
        except Exception:
            try:
                self._api.issues.create_label(
                    owner=self._owner, repo=self._repo,
                    name=name, color=color, description=description,
                )
            except Exception:
                pass

    def _with_retry(self, fn, *args, **kwargs):
        for attempt in range(3):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                if "429" in str(e) or "rate limit" in str(e).lower():
                    time.sleep(60)
                elif attempt < 2:
                    time.sleep(2 ** attempt)
                else:
                    raise
