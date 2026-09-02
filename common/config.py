import json
from pathlib import Path
from dataclasses import dataclass, field
from common.logger import Logger

# Base path relative to this file (independent of current working directory)
BASE_DIR = Path(__file__).resolve().parent
URL_MAPPING_FILE = BASE_DIR / "mapping" / "url.json"


def safe_load_json(filepath: Path | str) -> dict:
    path = Path(filepath)
    if not path.is_file():
        print(f"[FileLoadError] File does not exist: {path}")
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        print(f"[FileLoadError] Failed to load {path}: {exc}")
        return {}


@dataclass
class Config:
    logger: Logger = field(default_factory=lambda: Logger(operation="ConfigHandler"))

    def __post_init__(self):
        for name,value in safe_load_json(URL_MAPPING_FILE).items():
            setattr(self,name,value)

config = Config()