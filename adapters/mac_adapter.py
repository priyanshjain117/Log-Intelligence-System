import re
from datetime import datetime
from adapters.base_adapter import BaseAdapter


class MacAdapter(BaseAdapter):
    """
    Adapter for macOS system logs (kernel + user processes).
    """

    MAC_LOG_PATTERN = re.compile(
        r'(?P<month>\w{3})\s+'
        r'(?P<day>\d{1,2})\s+'
        r'(?P<time>\d{2}:\d{2}:\d{2})\s+'
        r'(?P<host>\S+)\s+'
        r'(?P<process>[A-Za-z0-9\.\-_]+)'
        r'\[(?P<pid>\d+)\]:\s+'
        r'(?P<message>.*)'
    )

    def __init__(self):
        super().__init__(source_name="mac")

    def parse(self, raw_log: str) -> dict:
        match = self.MAC_LOG_PATTERN.search(raw_log)

        if not match:
            # Safe fallback
            clean_message = self.normalize_text(raw_log)
            log_level = self.detect_log_level(raw_log)

            return self.base_output(
                raw_log=raw_log,
                clean_message=clean_message,
                log_level=log_level,
                service="macos"
            )

        data = match.groupdict()

        timestamp = self._parse_time(
            data["month"], data["day"], data["time"]
        )

        process = data["process"]
        pid = data["pid"]
        message = data["message"]

        log_level = self._infer_log_level(process, message)
        clean_message = self.normalize_text(message)

        structured_fields = {
            "host": data["host"],
            "pid": pid
        }

        # Optional: detect kernel subsystems
        component = self._detect_component(message)
        if component:
            structured_fields["component"] = component

        return self.base_output(
            raw_log=raw_log,
            clean_message=clean_message,
            log_level=log_level,
            service=process,
            timestamp=timestamp,
            structured_fields=structured_fields
        )

    # ---------- Helpers ----------

    def _parse_time(self, month, day, time_str):
        """
        macOS logs do not include year.
        Assume current year.
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

    def _infer_log_level(self, process: str, message: str) -> str:
        msg = message.lower()

        if process == "kernel":
            if "error" in msg or "failed" in msg or "panic" in msg:
                return "ERROR"
            return "INFO"

        if "error" in msg or "unexpected" in msg or "alert" in msg:
            return "ERROR"

        if "warning" in msg or "pressure" in msg:
            return "WARN"

        return "INFO"

    def _detect_component(self, message: str):
        """
        Extract kernel / system subsystems if present.
        """
        if message.startswith("ARPT"):
            return "wifi"
        if "Thunderbolt" in message:
            return "thunderbolt"
        if "AirPort" in message or "IO80211" in message:
            return "wifi"
        if "Sleep" in message or "Wake" in message:
            return "power"
        return None
    