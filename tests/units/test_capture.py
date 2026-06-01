import pytest

from oopsys_python import Severity
from oopsys_python.core import Oopsys
from oopsys_python.settings import Settings
from recording import RecordingTransport


def test_capture_returns_report_with_context(recorder: RecordingTransport) -> None:
    oops = Oopsys(Settings(_env_file=None), transport=recorder)

    report = oops.capture(ValueError("boom"), callable="my_fn", extra=1)

    assert report.message == "boom"
    assert report.severity is Severity.ERROR
    assert report.context == {"callable": "my_fn", "extra": 1}
    assert len(recorder.reports) == 1


async def test_acapture_uses_async_delivery(recorder: RecordingTransport) -> None:
    oops = Oopsys(Settings(_env_file=None), transport=recorder)

    report = await oops.acapture(RuntimeError("async"), critical=True)

    assert report.severity is Severity.CRITICAL
    assert recorder.reports[0] is report


def test_log_elapsed_calls_debug_logger(monkeypatch: pytest.MonkeyPatch) -> None:
    oops = Oopsys(Settings(_env_file=None, is_development=True))
    logged: list[dict[str, object]] = []

    def fake_debug(event: str, **kwargs: object) -> None:
        logged.append({"event": event, **kwargs})

    monkeypatch.setattr(oops._log, "debug", fake_debug)
    oops.log_elapsed("my_fn", 0.0)

    assert logged[0]["event"] == "execution time"
    assert logged[0]["callable"] == "my_fn"
    assert "ms" in logged[0]
    assert "hf" in logged[0]
