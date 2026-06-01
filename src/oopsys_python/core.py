import asyncio
import functools
import inspect
import sys
import threading
from collections.abc import Callable
from contextlib import suppress
from time import perf_counter
from types import TracebackType
from typing import Any

from structlog import getLogger

from oopsys_python.report import ErrorReport, Severity
from oopsys_python.settings import Settings
from oopsys_python.transport import AgentTransport

_IGNORE_ATTR = "__oopsys_ignore__"


class Oopsys:
    def __init__(
        self,
        config: Settings | None = None,
        *,
        transport: AgentTransport | None = None,
    ) -> None:
        self.config = config or Settings()
        self.transport = transport or AgentTransport(self.config)
        self._log = getLogger(self.config.logger_name)

    def _build(self, exc: BaseException, *, critical: bool, context: dict[str, Any]) -> ErrorReport:
        return ErrorReport.from_exception(
            exc,
            severity=Severity.CRITICAL if critical else Severity.ERROR,
            service=self.config.service_name,
            environment=self.config.environment,
            context=context,
        )

    def _emit(self, report: ErrorReport) -> None:
        payload = {
            "severity": report.severity.value,
            "error_type": report.exception_type,
            "detail": report.message,
            "agent_enabled": self.transport.active,
            **report.context,
        }
        if report.severity is Severity.CRITICAL:
            self._log.critical("application crashed", **payload)
        else:
            self._log.error("captured exception", **payload)

    def capture(self, exc: BaseException, *, critical: bool = False, **context: Any) -> ErrorReport:
        report = self._build(exc, critical=critical, context=context)
        self._emit(report)
        self.transport.deliver(report)
        return report

    async def acapture(self, exc: BaseException, *, critical: bool = False, **context: Any) -> ErrorReport:
        report = self._build(exc, critical=critical, context=context)
        self._emit(report)
        await self.transport.adeliver(report)
        return report

    def log_elapsed(self, name: str, start: float) -> None:
        elapsed = perf_counter() - start
        hours, rem = divmod(elapsed, 3600)
        minutes, seconds = divmod(rem, 60)
        self._log.debug(
            "execution time",
            callable=name,
            ms=round(elapsed * 1000, 2),
            hf=f"{int(hours)}:{int(minutes):02d}:{seconds:06.4f}",
        )

    def install(self) -> None:
        def _excepthook(exc_type: type[BaseException], exc: BaseException, tb: TracebackType | None) -> None:
            if issubclass(exc_type, (KeyboardInterrupt, SystemExit)) or getattr(exc, _IGNORE_ATTR, False):
                sys.__excepthook__(exc_type, exc, tb)
                return
            self.capture(exc, critical=True, source="excepthook")

        def _threadhook(args: threading.ExceptHookArgs) -> None:
            exc = args.exc_value
            if exc is None or issubclass(args.exc_type, (KeyboardInterrupt, SystemExit)):
                return
            if getattr(exc, _IGNORE_ATTR, False):
                return
            self.capture(exc, critical=True, source="threading")

        def _loophook(loop: asyncio.AbstractEventLoop, ctx: dict[str, Any]) -> None:
            exc = ctx.get("exception")
            if isinstance(exc, BaseException) and not getattr(exc, _IGNORE_ATTR, False):
                self.capture(exc, critical=True, source="asyncio")
            else:
                loop.default_exception_handler(ctx)

        sys.excepthook = _excepthook
        threading.excepthook = _threadhook
        with suppress(RuntimeError):
            asyncio.get_running_loop().set_exception_handler(_loophook)


_default: Oopsys | None = None


def configure(*, transport: AgentTransport | None = None) -> Oopsys:
    """Init oopsys from ``OOPSYS_*`` environment variables / ``.env``."""
    global _default
    _default = Oopsys(transport=transport)
    return _default


def get_oopsys() -> Oopsys:
    global _default
    if _default is None:
        _default = Oopsys()
    return _default


def guard(
    func: Callable[..., Any] | None = None,
    *,
    critical: bool = False,
    reraise: bool | None = None,
    fallback: Any = None,
) -> Any:
    """Catch exceptions, log/report them, return ``fallback`` (sync and async)."""

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        if inspect.iscoroutinefunction(fn):

            @functools.wraps(fn)
            async def awrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return await fn(*args, **kwargs)
                except Exception as exc:
                    if getattr(exc, _IGNORE_ATTR, False):
                        raise
                    oops = get_oopsys()
                    await oops.acapture(exc, critical=critical, callable=fn.__qualname__)
                    if oops.config.reraise if reraise is None else reraise:
                        raise
                    return fallback

            return awrapper

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return fn(*args, **kwargs)
            except Exception as exc:
                if getattr(exc, _IGNORE_ATTR, False):
                    raise
                oops = get_oopsys()
                oops.capture(exc, critical=critical, callable=fn.__qualname__)
                if oops.config.reraise if reraise is None else reraise:
                    raise
                return fallback

        return wrapper

    return decorator if func is None else decorator(func)


def ignore(func: Callable[..., Any] | None = None) -> Any:
    """Skip oopsys handling for this callable."""

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        if inspect.iscoroutinefunction(fn):

            @functools.wraps(fn)
            async def awrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return await fn(*args, **kwargs)
                except Exception as exc:
                    setattr(exc, _IGNORE_ATTR, True)
                    raise

            return awrapper

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return fn(*args, **kwargs)
            except Exception as exc:
                setattr(exc, _IGNORE_ATTR, True)
                raise

        return wrapper

    return decorator if func is None else decorator(func)


def timeit(func: Callable[..., Any] | None = None, *, label: str | None = None) -> Any:
    """Log call duration at DEBUG when ``is_development`` is true."""

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        name = label or fn.__qualname__

        if inspect.iscoroutinefunction(fn):

            @functools.wraps(fn)
            async def awrapper(*args: Any, **kwargs: Any) -> Any:
                oops = get_oopsys()
                if not oops.config.is_development:
                    return await fn(*args, **kwargs)
                start = perf_counter()
                try:
                    return await fn(*args, **kwargs)
                finally:
                    oops.log_elapsed(name, start)

            return awrapper

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            oops = get_oopsys()
            if not oops.config.is_development:
                return fn(*args, **kwargs)
            start = perf_counter()
            try:
                return fn(*args, **kwargs)
            finally:
                oops.log_elapsed(name, start)

        return wrapper

    return decorator if func is None else decorator(func)


def install() -> None:
    get_oopsys().install()
