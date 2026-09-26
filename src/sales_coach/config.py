import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Settings:
    data_dir: Path = field(default_factory=lambda: Path(os.getenv("COACH_DATA_DIR", "data")).resolve())
    audio_root: Path = field(default_factory=lambda: Path(os.getenv("COACH_AUDIO_ROOT", "audio")).resolve())
    api_token: str = field(default_factory=lambda: os.getenv("COACH_API_TOKEN", ""))
    deepgram_key: str = field(default_factory=lambda: os.getenv("DEEPGRAM_API_KEY", ""))
    deepgram_model: str = field(default_factory=lambda: os.getenv("DEEPGRAM_MODEL", "nova-3"))
    anthropic_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    anthropic_model: str = field(default_factory=lambda: os.getenv("ANTHROPIC_MODEL", ""))
    max_upload_bytes: int = field(default_factory=lambda: int(os.getenv("COACH_MAX_UPLOAD_MB", "100")) * 1024 * 1024)
    max_coaching_chars: int = field(default_factory=lambda: int(os.getenv("COACH_MAX_COACHING_CHARS", "100000")))
    provider_timeout: float = 300.0
    max_active_jobs: int = field(default_factory=lambda: int(os.getenv("COACH_MAX_ACTIVE_JOBS", "32")))

    def __post_init__(self):
        if self.max_upload_bytes <= 0 or self.max_coaching_chars <= 0 or self.max_active_jobs <= 0:
            raise ValueError("Limits must be positive")
