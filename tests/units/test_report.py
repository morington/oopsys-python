from oopsys_python import ErrorReport, Severity


def test_from_exception_fills_fields() -> None:
    try:
        raise ValueError("boom")
    except ValueError as exc:
        report = ErrorReport.from_exception(
            exc,
            severity=Severity.ERROR,
            service="svc",
            environment="test",
            context={"callable": "f"},
        )

    assert report.severity is Severity.ERROR
    assert report.exception_type == "ValueError"
    assert report.message == "boom"
    assert "ValueError" in report.traceback
    assert report.context == {"callable": "f"}


def test_empty_message_falls_back_to_type() -> None:
    try:
        raise ZeroDivisionError
    except ZeroDivisionError as exc:
        report = ErrorReport.from_exception(exc, severity=Severity.CRITICAL, service="s", environment="e")

    assert report.message == "ZeroDivisionError"
