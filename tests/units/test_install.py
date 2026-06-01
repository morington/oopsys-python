import asyncio
import sys
import threading

import pytest

from oopsys_python import Severity, core, install
from oopsys_python.core import Oopsys, _IGNORE_ATTR
from oopsys_python.settings import Settings
from recording import RecordingTransport


@pytest.fixture
def hooks(recorder: RecordingTransport) -> RecordingTransport:
    old_sys = sys.excepthook
    old_thread = threading.excepthook
    install()
    yield recorder
    sys.excepthook = old_sys
    threading.excepthook = old_thread


def test_excepthook_captures_unhandled(hooks: RecordingTransport) -> None:
    try:
        raise ValueError("unhandled")
    except ValueError as exc:
        sys.excepthook(type(exc), exc, exc.__traceback__)

    assert len(hooks.reports) == 1
    assert hooks.reports[0].severity is Severity.CRITICAL
    assert hooks.reports[0].context["source"] == "excepthook"


def test_excepthook_skips_keyboard_interrupt(
    recorder: RecordingTransport, monkeypatch: pytest.MonkeyPatch
) -> None:
    delegated: list[bool] = []

    def original_hook(exc_type: type[BaseException], exc: BaseException, tb) -> None:
        delegated.append(True)

    monkeypatch.setattr(sys, "__excepthook__", original_hook)
    install()

    try:
        raise KeyboardInterrupt
    except KeyboardInterrupt as exc:
        sys.excepthook(type(exc), exc, exc.__traceback__)

    assert delegated
    assert recorder.reports == []


def test_excepthook_skips_ignored_marker(hooks: RecordingTransport) -> None:
    exc = RuntimeError("skip")
    setattr(exc, _IGNORE_ATTR, True)
    sys.excepthook(RuntimeError, exc, None)

    assert hooks.reports == []


def test_thread_excepthook_captures(hooks: RecordingTransport) -> None:
    try:
        raise RuntimeError("thread")
    except RuntimeError as exc:
        args = threading.ExceptHookArgs(
            (RuntimeError, exc, exc.__traceback__, threading.current_thread()),
        )
    threading.excepthook(args)

    assert hooks.reports[0].context["source"] == "threading"


async def test_asyncio_handler_captures(recorder: RecordingTransport) -> None:
    core._default = Oopsys(Settings(_env_file=None), transport=recorder)
    install()

    loop = asyncio.get_running_loop()
    handler = loop.get_exception_handler()
    assert handler is not None

    handler(loop, {"exception": ValueError("async leak")})

    assert recorder.reports[0].context["source"] == "asyncio"
