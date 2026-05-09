import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class CrawlRun:
    run_id: str
    pipeline: str
    board_id: str = ""
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None
    processed: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[dict] = field(default_factory=list)

    def to_json(self) -> dict:
        return {
            "run_id": self.run_id,
            "pipeline": self.pipeline,
            "board_id": self.board_id,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "processed": self.processed,
            "skipped": self.skipped,
            "failed": self.failed,
            "errors": self.errors,
        }

    def report(self) -> str:
        elapsed = ""
        if self.finished_at and self.started_at:
            secs = (self.finished_at - self.started_at).total_seconds()
            elapsed = f" | 소요: {secs:.1f}초"
        return (
            f"[완료] 처리: {self.processed}건 | "
            f"스킵: {self.skipped}건 | "
            f"실패: {self.failed}건{elapsed}"
        )

    def save(self, cache_dir: Path) -> None:
        runs_dir = cache_dir / "runs"
        runs_dir.mkdir(parents=True, exist_ok=True)
        path = runs_dir / f"{self.run_id}.json"
        path.write_text(json.dumps(self.to_json(), ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load_latest(cls, cache_dir: Path, pipeline: str) -> "CrawlRun | None":
        runs_dir = cache_dir / "runs"
        if not runs_dir.exists():
            return None
        candidates = sorted(runs_dir.glob("*.json"), reverse=True)
        for path in candidates:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if data.get("pipeline") == pipeline:
                    return cls._from_dict(data)
            except (json.JSONDecodeError, KeyError):
                continue
        return None

    @classmethod
    def _from_dict(cls, data: dict) -> "CrawlRun":
        run = cls(run_id=data["run_id"], pipeline=data["pipeline"], board_id=data.get("board_id", ""))
        run.started_at = datetime.fromisoformat(data["started_at"])
        run.finished_at = datetime.fromisoformat(data["finished_at"]) if data.get("finished_at") else None
        run.processed = data.get("processed", 0)
        run.skipped = data.get("skipped", 0)
        run.failed = data.get("failed", 0)
        run.errors = data.get("errors", [])
        return run
