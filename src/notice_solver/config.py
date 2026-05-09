from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    github_token: str
    github_repo_owner: str
    github_repo_name: str

    default_board_id: str = "MAPP_1708240139"
    retry_count: int = 3
    request_delay_sec: float = 1.0
    ocr_batch_limit: int = 50
    ocr_confidence_threshold: float = 0.5
    log_dir: Path = Path("./logs")
    cache_dir: Path = Path("./.cache")
