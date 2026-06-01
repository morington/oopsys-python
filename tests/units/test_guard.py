import pytest

from oopsys_python import Severity, guard
from oopsys_python.core import Oopsys
from oopsys_python.settings import Settings
from recording import RecordingTransport


def test_guard_sync_swallows_and_returns_fallback(recorder: RecordingTransport) -> None:
    @guard(fallback=-1)
    def divide(a: int, b: int) -> int:
        return a // b

    assert divide(10, 2) == 5
    assert divide(10, 0) == -1
    assert recorder.reports[0].severity is Severity.ERROR


def test_guard_default_fallback_is_none(recorder: RecordingTransport) -> None:
    @guard
    def boom() -> int | None:
        raise ValueError("x")

    assert boom() is None


def test_guard_bare_decorator_syntax(recorder: RecordingTransport) -> None:
    @guard
    def bare() -> None:
        raise OSError("bare")

    assert bare() is None
    assert recorder.reports[0].exception_type == "OSError"


def test_guard_records_callable_qualname(recorder: RecordingTransport) -> None:
    @guard(fallback=None)
    def my_worker() -> None:
        raise ValueError("fail")

    my_worker()

    assert recorder.reports[0].context["callable"].endswith("my_worker")


def test_guard_sync_critical_severity(recorder: RecordingTransport) -> None:
    @guard(critical=True)
    def boom() -> None:
        raise RuntimeError("dead")

    boom()
    assert recorder.reports[0].severity is Severity.CRITICAL


def test_guard_reraise_propagates(recorder: RecordingTransport) -> None:
    @guard(reraise=True)
    def boom() -> None:
        raise KeyError("k")

    with pytest.raises(KeyError):
        boom()
    assert recorder.reports[0].exception_type == "KeyError"


def test_guard_honors_global_reraise_from_config(recorder: RecordingTransport) -> None:
    from oopsys_python import core

    core._default = Oopsys(Settings(_env_file=None, reraise=True), transport=recorder)

    @guard
    def boom() -> None:
        raise TypeError("t")

    with pytest.raises(TypeError):
        boom()


async def test_guard_async_swallows(recorder: RecordingTransport) -> None:
    @guard(fallback=0)
    async def divide(a: int, b: int) -> int:
        return a // b

    assert await divide(8, 2) == 4
    assert await divide(8, 0) == 0
    assert recorder.reports[0].exception_type == "ZeroDivisionError"
