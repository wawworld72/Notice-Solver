import json
from pathlib import Path


class _JsonIndex:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._data: dict[str, int] = {}
        self.load()

    def load(self) -> None:
        if self._path.exists():
            try:
                self._data = json.loads(self._path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._data = {}
        else:
            self._data = {}

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")

    def exists(self, id_: str) -> bool:
        return id_ in self._data

    def add(self, id_: str, issue_number: int) -> None:
        self._data[id_] = issue_number
        self.save()

    def get(self, id_: str) -> int | None:
        return self._data.get(id_)

    def __len__(self) -> int:
        return len(self._data)


class NoticeIndex(_JsonIndex):
    def __init__(self, cache_dir: Path) -> None:
        super().__init__(cache_dir / "notice-index.json")


class AssetIndex(_JsonIndex):
    def __init__(self, cache_dir: Path) -> None:
        super().__init__(cache_dir / "asset-index.json")
