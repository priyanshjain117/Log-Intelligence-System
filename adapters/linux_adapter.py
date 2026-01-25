import re
from datetime import datetime
from adapters.base_adapter import BaseAdapter


class LinuxAdapter(BaseAdapter):
    """
    Adapter for Linux syslog / auth.log style logs.
    """

    SYSLOG_PATTERN = re.compile(
        r'(?P<month>\w{3})\s+'
        r'(?P<day>\d{1,2})\s+'
        r'(?P<time>\d{2}:\d{2}:\d{2})\s+'
        r'(?P<host>\S+)\s+'
        r'(?P<service>\w+)(?:\((?P<subsystem>[^)]+)\))?'
        r'\[(?P<pid>\d+)\]:\s+'
        r'(?P<message>.*)'
    )

    def __init__(self):
        super().__init__(source_name="linux")

    def parse(self, raw_log: str) -> dict:
        match = self.SYSLOG_PATTERN.search(raw_log)

        if not match:
            # Fallback: treat as generic
            clean_message = self.normalize_text(raw_log)
            log_level = self.detect_log_level(raw_log)

            return self.base_output(
                raw_log=raw_log,
                clean_message=clean_message,
                log_level=log_level,
                service="linux"
            )

        data = match.groupdict()

        timestamp = self._parse_time(
            data["month"], data["day"], data["time"]
        )

        service = data["service"]
        pid = data["pid"]
        message = data["message"]

        # Extract useful entities
        user = self._extract_user(message)
        rhost = self._extract_rhost(message)

        # Determine log level heuristically
        log_level = self._infer_log_level(message)

        clean_message = self.normalize_text(message)

        structured_fields = {
            "host": data["host"],
            "pid": pid
        }

        if user:
            structured_fields["user"] = user
        if rhost:
            structured_fields["rhost"] = rhost

        return self.base_output(
            raw_log=raw_log,
            clean_message=clean_message,
            log_level=log_level,
            service=service,
            timestamp=timestamp,
            structured_fields=structured_fields
        )

    # ---------- Helpers ----------

    def _parse_time(self, month, day, time_str):
        """
        Linux logs do not include year.
        We assume current year for normalization.
        """
        try:
            year = datetime.now().year
            dt = datetime.strptime(
                f"{year} {month} {day} {time_str}",
                "%Y %b %d %H:%M:%S"
            )
            return dt.isoformat()
        except Exception:
            return None

    def _infer_log_level(self, message: str) -> str:
        msg = message.lower()
        if "error" in msg or "failure" in msg or "alert" in msg:
            return "ERROR"
        if "unknown" in msg or "denied" in msg:
            return "WARN"
        return "INFO"

    def _extract_user(self, message: str):
        match = re.search(r'user=([a-zA-Z0-9_\-]+)', message)
        return match.group(1) if match else None

    def _extract_rhost(self, message: str):
        match = re.search(r'rhost=([^\s]+)', message)
        return match.group(1) if match else None
