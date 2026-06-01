import pytest

from oopsys_python.settings import OOPSYS_LOGGER_NAME, AgentModel, Settings


def test_defaults() -> None:
    settings = Settings(_env_file=None)
    assert settings.is_development is False
    assert settings.environment == "production"
    assert settings.service_name == "app"
    assert settings.reraise is False
    assert settings.logger_name == OOPSYS_LOGGER_NAME
    assert settings.agent.enabled is True
    assert settings.agent.url() == "http://localhost:8080/reports"


def test_environment_follows_dev_flag() -> None:
    assert Settings(_env_file=None, is_development=True).environment == "development"


def test_reads_only_prefixed_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OOPSYS_SERVICE_NAME", "billing")
    monkeypatch.setenv("OOPSYS_AGENT__ENABLED", "false")
    monkeypatch.setenv("SERVICE_NAME", "ignored")
    monkeypatch.setenv("DATABASE_URL", "postgres://ignored")

    settings = Settings(_env_file=None)
    assert settings.service_name == "billing"
    assert settings.agent.enabled is False


def test_agent_url_from_nested_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OOPSYS_AGENT__HOST", "agent.internal")
    monkeypatch.setenv("OOPSYS_AGENT__PORT", "9000")
    monkeypatch.setenv("OOPSYS_AGENT__PATH", "/v1/events")

    settings = Settings(_env_file=None)

    assert settings.agent.url() == "http://agent.internal:9000/v1/events"


def test_agent_model_url_helper() -> None:
    agent = AgentModel(host="h", port=443, path="/api")
    assert agent.url() == "http://h:443/api"
