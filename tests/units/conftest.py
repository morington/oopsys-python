import pytest

from oopsys_python import core
from oopsys_python.core import Oopsys
from oopsys_python.settings import Settings
from recording import RecordingTransport


@pytest.fixture
def recorder(monkeypatch: pytest.MonkeyPatch) -> RecordingTransport:
    monkeypatch.setenv("OOPSYS_AGENT__ENABLED", "false")
    transport = RecordingTransport()
    core._default = Oopsys(Settings(_env_file=None), transport=transport)
    return transport


@pytest.fixture
def reset_default() -> None:
    core._default = None
    yield
    core._default = None
