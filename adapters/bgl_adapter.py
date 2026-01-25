import re
from datetime import datetime
from adapters.base_adapter import BaseAdapter


class BGLAdapter(BaseAdapter):
    """
    Adapter for IBM Blue Gene/L (BGL) RAS logs.
    """

    BGL_PATTERN = re.compile(
        r'(?P<prefix>-|APPREAD)\s+'
        r'(?P<epoch>\d+)\s+'
        r'(?P<date>\d{4}\.\d{2}\.\d{2})\s+'
        r'(?P<location1>[A-Z0-9\-:]+)\s+'
        r'(?P<timestamp>\d{4}-\d{2}-\d{2}-\d{2}\.\d{2}\.\d{2}\.\d+)\s+'
        r'(?P<location2>[A-Z0-9\-:]+)\s+'
        r'RAS\s+'
        r'(?P<subsystem>\w+)\s+'
        r'(?P<severity>\w+)\s+'
        r'(?P<message>.*)'
    )

    def __init__(self):
        super().__init__(source_name="bgl")

    def parse(self, raw_log: str) -> dict:
        match = self.BGL_PATTERN.search(raw_log)

        if not match:
            clean_message = self.normalize_text(raw_log)
            log_level = self.detect_log_level(raw_log)

            return self.base_output(
                raw_log=raw_log,
                clean_message=clean_message,
                log_level=log_level,
                service="bgl"
            )

        data = match.groupdict()

        timestamp = self._parse_precise_time(data["timestamp"])
        severity = data["severity"].upper()
        subsystem = data["subsystem"].upper()
        message = data["message"]

        log_level = self._map_severity(severity)
        error_class = self._infer_error_class(message)

        clean_message = self.normalize_text(message)

        structured_fields = {
            "epoch": data["epoch"],
            "location": data["location1"],
            "subsystem": subsystem,
            "severity": severity
        }

        if error_class:
            structured_fields["error_class"] = error_class

        return self.base_output(
            raw_log=raw_log,
            clean_message=clean_message,
            log_level=log_level,
            service=subsystem,
            timestamp=timestamp,
            structured_fields=structured_fields
        )

    # ---------- Helpers ----------

    def _parse_precise_time(self, time_str):
        """
        Format: YYYY-MM-DD-HH.MM.SS.microseconds
        """
        try:
            return datetime.strptime(
                time_str, "%Y-%m-%d-%H.%M.%S.%f"
            ).isoformat()
        except Exception:
            return None

    def _map_severity(self, severity: str) -> str:
        if severity in ["FATAL", "ERROR"]:
            return "ERROR"
        if severity in ["WARN", "WARNING"]:
            return "WARN"
        return "INFO"

    def _infer_error_class(self, message: str):
        msg = message.lower()

        if "parity error" in msg:
            return "parity_error"
        if "alignment exception" in msg:
            return "alignment_exception"
        if "generating core" in msg:
            return "core_dump"
        if "ce sym" in msg:
            return "correctable_error"
        if "failed to read" in msg:
            return "io_failure"
        return None
