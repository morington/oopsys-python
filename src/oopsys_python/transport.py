import httpx
from structlog import getLogger

from oopsys_python.report import ErrorReport
from oopsys_python.settings import Settings


class AgentTransport:
    def __init__(self, config: Settings) -> None:
        self._config = config
        self._log = getLogger(config.logger_name)

    @property
    def active(self) -> bool:
        return self._config.agent.enabled

    def deliver(self, report: ErrorReport) -> None:
        if not self.active:
            return
        try:
            httpx.post(
                self._config.agent.url(),
                json=report.model_dump(mode="json"),
                timeout=self._config.agent.timeout,
            )
        except Exception as exc:
            self._log.debug("oopsys delivery failed", error=str(exc))

    async def adeliver(self, report: ErrorReport) -> None:
        if not self.active:
            return
        try:
            async with httpx.AsyncClient(timeout=self._config.agent.timeout) as client:
                await client.post(self._config.agent.url(), json=report.model_dump(mode="json"))
        except Exception as exc:
            self._log.debug("oopsys delivery failed", error=str(exc))
