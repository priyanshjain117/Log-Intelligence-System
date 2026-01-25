import re
from datetime import datetime
from adapters.base_adapter import BaseAdapter


class HDFSAdapter(BaseAdapter):
    """
    Adapter for Hadoop HDFS logs (NameNode / DataNode).
    """

    HDFS_PATTERN = re.compile(
        r'(?P<date>\d{6})\s+'
        r'(?P<time>\d{6})\s+'
        r'(?P<thread>\d+)\s+'
        r'(?P<level>\w+)\s+'
        r'(?P<component>[^:]+):\s+'
        r'(?P<message>.*)'
    )

    BLOCK_PATTERN = re.compile(r'(blk_-?\d+)')
    IP_PATTERN = re.compile(r'(\d{1,3}(?:\.\d{1,3}){3})')

    def __init__(self):
        super().__init__(source_name="hdfs")

    def parse(self, raw_log: str) -> dict:
        match = self.HDFS_PATTERN.search(raw_log)

        if not match:
            # Safe fallback
            clean_message = self.normalize_text(raw_log)
            log_level = self.detect_log_level(raw_log)

            return self.base_output(
                raw_log=raw_log,
                clean_message=clean_message,
                log_level=log_level,
                service="hdfs"
            )

        data = match.groupdict()

        timestamp = self._parse_time(data["date"], data["time"])
        log_level = data["level"]
        component = data["component"]
        message = data["message"]

        service = self._extract_service(component)

        block_id = self._extract_block_id(message)
        datanode_ip = self._extract_ip(message)
        operation = self._infer_operation(message)

        clean_message = self.normalize_text(message)

        structured_fields = {
            "thread_id": data["thread"],
            "component": component
        }

        if block_id:
            structured_fields["block_id"] = block_id
        if datanode_ip:
            structured_fields["datanode_ip"] = datanode_ip
        if operation:
            structured_fields["operation"] = operation

        return self.base_output(
            raw_log=raw_log,
            clean_message=clean_message,
            log_level=log_level,
            service=service,
            timestamp=timestamp,
            structured_fields=structured_fields
        )

    # ---------- Helpers ----------

    def _parse_time(self, date_str, time_str):
        """
        date: YYMMDD, time: HHMMSS
        """
        try:
            dt = datetime.strptime(
                date_str + time_str, "%y%m%d%H%M%S"
            )
            return dt.isoformat()
        except Exception:
            return None

    def _extract_service(self, component: str) -> str:
        if "DataNode" in component:
            return "DataNode"
        if "FSNamesystem" in component:
            return "NameNode"
        if "DataXceiver" in component:
            return "DataXceiver"
        return "HDFS"

    def _extract_block_id(self, message: str):
        match = self.BLOCK_PATTERN.search(message)
        return match.group(1) if match else None

    def _extract_ip(self, message: str):
        match = self.IP_PATTERN.search(message)
        return match.group(1) if match else None

    def _infer_operation(self, message: str):
        msg = message.lower()
        if "received block" in msg:
            return "receive_block"
        if "addstoredblock" in msg:
            return "add_stored_block"
        if "allocateblock" in msg:
            return "allocate_block"
        if "terminating" in msg:
            return "packet_terminating"
        return None