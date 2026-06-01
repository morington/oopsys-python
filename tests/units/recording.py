from oopsys_python.report import ErrorReport


class RecordingTransport:
    active = False

    def __init__(self) -> None:
        self.reports: list[ErrorReport] = []

    def deliver(self, report: ErrorReport) -> None:
        self.reports.append(report)

    async def adeliver(self, report: ErrorReport) -> None:
        self.reports.append(report)
