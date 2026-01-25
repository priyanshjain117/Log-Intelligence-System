import re
from datetime import datetime
from adapters.base_adapter import BaseAdapter


class ApacheAdapter(BaseAdapter):
    """
    Adapter for Apache HTTP server logs:
    - Access logs (CLF / Combined)
    - Error logs
    """

    # Access log pattern
    ACCESS_LOG_PATTERN = re.compile(
        r'(?P<ip>\S+) \S+ \S+ '
        r'\[(?P<time>[^\]]+)\] '
        r'"(?P<method>\S+) (?P<endpoint>\S+) \S+" '
        r'(?P<status>\d{3}) (?P<size>\S+)'
    )

    # Error log pattern (like your example)
    ERROR_LOG_PATTERN = re.compile(
        r'\[(?P<time>[^\]]+)\] '
        r'\[(?P<level>\w+)\] '
        r'(?P<module>\S+)\s*(?P<message>.*)'
    )

    def __init__(self):
        super().__init__(source_name="apache")

    def parse(self, raw_log: str) -> dict:
        # 1️⃣ Try ACCESS log parsing
        access_match = self.ACCESS_LOG_PATTERN.search(raw_log)
        if access_match:
            return self._parse_access_log(raw_log, access_match)

        # 2️⃣ Try ERROR log parsing
        error_match = self.ERROR_LOG_PATTERN.search(raw_log)
        if error_match:
            return self._parse_error_log(raw_log, error_match)

        # 3️⃣ Fallback
        clean_message = self.normalize_text(raw_log)
        log_level = self.detect_log_level(raw_log)

        return self.base_output(
            raw_log=raw_log,
            clean_message=clean_message,
            log_level=log_level,
            service="apache"
        )

    # ---------- Helpers ----------

    def _parse_access_log(self, raw_log, match):
        data = match.groupdict()

        method = data["method"]
        endpoint = data["endpoint"]
        status_code = int(data["status"])
        timestamp = self._parse_time(data["time"])
        log_level = self._status_to_level(status_code)

        clean_message = self.normalize_text(
            f"http {method} {endpoint} status {status_code}"
        )

        return self.base_output(
            raw_log=raw_log,
            clean_message=clean_message,
            log_level=log_level,
            service="apache",
            timestamp=timestamp,
            structured_fields={
                "method": method,
                "endpoint": endpoint,
                "status_code": status_code
            }
        )

    def _parse_error_log(self, raw_log, match):
        data = match.groupdict()

        level = data["level"].upper()
        module = data["module"]
        message = data["message"]
        timestamp = self._parse_error_time(data["time"])

        clean_message = self.normalize_text(message)

        return self.base_output(
            raw_log=raw_log,
            clean_message=clean_message,
            log_level=level,
            service=module,
            timestamp=timestamp,
            structured_fields={
                "module": module
            }
        )

    def _status_to_level(self, status_code: int) -> str:
        if status_code >= 500:
            return "ERROR"
        elif status_code >= 400:
            return "WARN"
        else:
            return "INFO"

    def _parse_time(self, time_str: str):
        try:
            return datetime.strptime(
                time_str.split(" ")[0], "%d/%b/%Y:%H:%M:%S"
            ).isoformat()
        except Exception:
            return None

    def _parse_error_time(self, time_str: str):
        """
        Example: Sun Dec 04 04:47:44 2005
        """
        try:
            return datetime.strptime(
                time_str, "%a %b %d %H:%M:%S %Y"
            ).isoformat()
        except Exception:
            return None
