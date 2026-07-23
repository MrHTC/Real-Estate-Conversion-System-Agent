import datetime


class Logger:
    def __init__(self, prefix: str = "v2"):
        self.prefix = prefix

    def _format(self, level: str, message: str) -> str:
        timestamp = datetime.datetime.now().isoformat(timespec="seconds")
        return f"[{timestamp}][{self.prefix}][{level}] {message}"

    def info(self, message: str) -> None:
        print(self._format("INFO", message))

    def warn(self, message: str) -> None:
        print(self._format("WARN", message))

    def error(self, message: str) -> None:
        print(self._format("ERROR", message))
