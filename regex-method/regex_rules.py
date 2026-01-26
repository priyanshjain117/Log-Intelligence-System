REGEX_RULES = [
    # ================= Security =================
    {
        "level": "ERROR",
        "pattern": r"authentication failure",
        "confidence": 0.95,
        "sources": ["linux"]
    },
    {
        "level": "WARNING",
        "pattern": r"check pass; user unknown",
        "confidence": 0.96,
        "sources": ["linux"]
    },

    # ================= Core Dumps =================
    {
        "level": "CRITICAL",
        "pattern": r"generating core\.\d+",
        "confidence": 0.98,
        "sources": ["bgl"]
    },

    # ================= HDFS =================
    {
        "level": "INFO",
        "pattern": r"packetresponder \d+ for block blk_.* terminating",
        "confidence": 0.90,
        "sources": ["hdfs"]
    },
    {
        "level": "INFO",
        "pattern": r"block\* namesystem\.addstoredblock",
        "confidence": 0.88,
        "sources": ["hdfs"]
    },
    {
        "level": "INFO",
        "pattern": r"received block blk_",
        "confidence": 0.87,
        "sources": ["hdfs"]
    },
    {
        "level": "INFO",
        "pattern": r"block\* namesystem\.allocateblock",
        "confidence": 0.87,
        "sources": ["hdfs"]
    },
]
