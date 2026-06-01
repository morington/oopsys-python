import pytest

from oopsys_python import guard, ignore
from recording import RecordingTransport


def test_ignored_exception_passes_through_guard(recorder: RecordingTransport) -> None:
    @ignore
    def inner() -> None:
        raise ValueError("leave me alone")

    @guard(fallback="caught")
    def outer() -> str:
        inner()
        return "ok"

    with pytest.raises(ValueError, match="leave me alone"):
        outer()
    assert recorder.reports == []


async def test_ignored_async_exception_passes_through(recorder: RecordingTransport) -> None:
    @ignore
    async def inner() -> None:
        raise RuntimeError("nope")

    with pytest.raises(RuntimeError, match="nope"):
        await inner()
    assert recorder.reports == []


async def test_ignored_inner_bypasses_async_guard(recorder: RecordingTransport) -> None:
    @ignore
    async def inner() -> None:
        raise ValueError("propagate")

    @guard(fallback="swallowed")
    async def outer() -> str:
        await inner()
        return "ok"

    with pytest.raises(ValueError, match="propagate"):
        await outer()
    assert recorder.reports == []
