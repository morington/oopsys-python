import pytest

from oopsys_python import configure, core, timeit
from oopsys_python.core import Oopsys
from oopsys_python.settings import Settings


@pytest.fixture
def dev(monkeypatch: pytest.MonkeyPatch) -> Oopsys:
    monkeypatch.setenv("OOPSYS_IS_DEVELOPMENT", "true")
    oops = Oopsys(Settings(_env_file=None, is_development=True))
    core._default = oops
    return oops


def test_timeit_sync_preserves_return_value(dev: Oopsys) -> None:
    @timeit
    def add(a: int, b: int) -> int:
        return a + b

    assert add(2, 3) == 5


def test_timeit_sync_propagates_errors(dev: Oopsys) -> None:
    @timeit
    def boom() -> None:
        raise ValueError("x")

    with pytest.raises(ValueError, match="x"):
        boom()


async def test_timeit_async_preserves_return_value(dev: Oopsys) -> None:
    @timeit(label="async-add")
    async def add(a: int, b: int) -> int:
        return a + b

    assert await add(4, 5) == 9


def test_timeit_logs_elapsed_in_development(dev: Oopsys, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, float]] = []
    monkeypatch.setattr(dev, "log_elapsed", lambda name, start: calls.append((name, start)))

    @timeit(label="labeled")
    def work() -> int:
        return 7

    assert work() == 7
    assert calls[0][0] == "labeled"


def test_timeit_is_noop_outside_development(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OOPSYS_IS_DEVELOPMENT", "false")
    configure()

    @timeit
    def add(a: int, b: int) -> int:
        return a + b

    assert add(1, 1) == 2
