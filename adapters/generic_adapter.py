from adapters.base_adapter import BaseAdapter

class GenericAdapter(BaseAdapter):
    """
    Fallback adapter for unknown or unsupported logs.
    """

    def __init__(self):
        super().__init__(source_name="generic")

    def parse(self, raw_log: str) -> dict:
        clean_message = self.normalize_text(raw_log)
        log_level = self.detect_log_level(raw_log)

        return self.base_output(
            raw_log=raw_log,
            clean_message=clean_message,
            log_level=log_level
        )
