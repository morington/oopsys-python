from oopsys_python import configure, core
from oopsys_python.core import Oopsys


def test_configure_reads_oopsys_env(reset_default, monkeypatch) -> None:
    monkeypatch.setenv("OOPSYS_SERVICE_NAME", "billing")
    monkeypatch.setenv("OOPSYS_AGENT__ENABLED", "false")

    oops = configure()

    assert isinstance(oops, Oopsys)
    assert oops.config.service_name == "billing"
    assert core._default is oops


def test_get_oopsys_lazy_inits_when_not_configured(reset_default) -> None:
    from oopsys_python.core import get_oopsys

    oops = get_oopsys()

    assert isinstance(oops, Oopsys)
    assert core._default is oops
