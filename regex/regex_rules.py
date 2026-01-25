REGEX_RULES = [
    # -------- Security --------
    {
        "label": "AUTH_FAILURE",
        "pattern": r"authentication failure;",
        "confidence": 0.95,
        "sources": ["linux"]
    },
    {
        "label": "UNKNOWN_USER_LOGIN",
        "pattern": r"check pass; user unknown",
        "confidence": 0.96,
        "sources": ["linux"]
    },

    # -------- Core dumps --------
    {
        "label": "CORE_DUMP",
        "pattern": r"generating core\.\d+",
        "confidence": 0.98,
        "sources": ["bgl"]
    },

    # -------- HDFS --------
    {
        "label": "HDFS_BLOCK_TERMINATION",
        "pattern": r"packetresponder \d+ for block blk_.* terminating",
        "confidence": 0.90,
        "sources": ["hdfs"]
    },
    {
        "label": "HDFS_BLOCK_STORED",
        "pattern": r"block\* namesystem\.addstoredblock",
        "confidence": 0.88,
        "sources": ["hdfs"]
    },
    {
        "label": "HDFS_BLOCK_RECEIVED",
        "pattern": r"received block blk_",
        "confidence": 0.87,
        "sources": ["hdfs"]
    },
    {
        "label": "HDFS_BLOCK_ALLOCATED",
        "pattern": r"block\* namesystem\.allocateblock",
        "confidence": 0.87,
        "sources": ["hdfs"]
    },

    # -------- Apache --------
    {
        "label": "APACHE_WORKER_INIT",
        "pattern": r"found child \d+ in scoreboard slot \d+",
        "confidence": 0.92,
        "sources": ["apache"]
    }
]
