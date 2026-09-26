import pytest
from sales_coach.config import Settings
from sales_coach.engine import Engine


@pytest.fixture
def settings(tmp_path):
    return Settings(data_dir=tmp_path / "data", audio_root=tmp_path / "audio",
        api_token="test-token", deepgram_key="", anthropic_key="", anthropic_model="")


@pytest.fixture
def engine(settings):
    instance = Engine(settings)
    yield instance
    instance.close()
