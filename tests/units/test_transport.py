from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from oopsys_python.report import ErrorReport, Severity
from oopsys_python.settings import Settings
from oopsys_python.transport import AgentTransport


def _report() -> ErrorReport:
    return ErrorReport(
        severity=Severity.ERROR,
        service="s",
        environment="e",
        exception_type="ValueError",
        message="m",
        traceback="tb",
    )


def test_transport_inactive_when_agent_disabled() -> None:
    settings = Settings(_env_file=None)
    settings.agent.enabled = False
    transport = AgentTransport(settings)

    assert transport.active is False
    transport.deliver(_report())


def test_transport_swallows_delivery_errors() -> None:
    settings = Settings(_env_file=None)
    settings.agent.port = 1
    settings.agent.timeout = 0.01
    transport = AgentTransport(settings)

    assert transport.active is True
    transport.deliver(_report())


async def test_adeliver_swallows_delivery_errors() -> None:
    settings = Settings(_env_file=None)
    settings.agent.port = 1
    settings.agent.timeout = 0.01
    transport = AgentTransport(settings)

    await transport.adeliver(_report())


def test_deliver_posts_json_when_active() -> None:
    settings = Settings(_env_file=None)
    settings.agent.enabled = True
    transport = AgentTransport(settings)
    report = _report()

    with patch("oopsys_python.transport.httpx.post") as post:
        transport.deliver(report)

    post.assert_called_once()
    assert post.call_args.kwargs["json"]["severity"] == "error"
    assert post.call_args.args[0] == settings.agent.url()


async def test_adeliver_posts_json_when_active() -> None:
    settings = Settings(_env_file=None)
    settings.agent.enabled = True
    transport = AgentTransport(settings)
    report = _report()

    mock_response = MagicMock()
    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("oopsys_python.transport.httpx.AsyncClient", return_value=mock_client):
        await transport.adeliver(report)

    mock_client.post.assert_awaited_once_with(settings.agent.url(), json=report.model_dump(mode="json"))
