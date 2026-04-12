"""
log_cleaner.py
==============
Two clearly separated cleaning functions:

  clean_for_regex(log)  → preserves structure regex patterns depend on
  clean_for_ml(log)     → strips noise, keeps semantic signal for SentenceTransformer
"""

import re

_REGEX_NOISE = [
    (re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?\b'), '<IP>'),      # IP:port
    (re.compile(r'\bblk_-?\d+\b'),                          '<BLK>'),    # HDFS block IDs
    (re.compile(r'\b[0-9a-f]{8,}\b'),                       '<HEX>'),    # hex addresses
    (re.compile(r'(?<!\w)/[\w./-]+'),                        '<PATH>'),   # file paths
    (re.compile(r'\s{2,}'),                                  ' '),        # extra whitespace
]

def clean_for_regex(log: str) -> str:
    """
    Minimal cleaning before RegexEngine.
    Preserves numbers, brackets, dots — all needed by regex patterns.
    """
    if not isinstance(log, str):
        return ""
    for pattern, replacement in _REGEX_NOISE:
        log = pattern.sub(replacement, log)
    return log.strip()

_ML_NOISE = [
    (re.compile(r'\[\d+\]'),           ''),      # PIDs like [2915], [1682]
    (re.compile(r'\b\d{5,}\b'),        ''),      # long standalone numbers (timestamps, ports)
    (re.compile(r'\b\d+\.\d+\b'),      ''),      # version numbers like 3.0.1, 2.6.0
    (re.compile(r'(.)\1{3,}'),         r'\1\1\1'), # ****...*** → ***  (BGL noise)
    (re.compile(r'[^\w\s<>_\-\./:]'),  ' '),     # punctuation except meaningful separators
    (re.compile(r'\s{2,}'),            ' '),      # re-collapse whitespace after substitutions
]

def clean_for_ml(log: str) -> str:
    """
    Deeper cleaning before SentenceTransformer.
    Call this AFTER clean_for_regex — works on already-tokenised text.
    Lowercases, strips numeric noise, keeps all semantic words intact.
    """
    if not isinstance(log, str):
        return ""
    log = log.lower()
    for pattern, replacement in _ML_NOISE:
        log = pattern.sub(replacement, log)
    return log.strip()


#  Combined convenience function (for ml_node.py at inference time)
def prepare_for_ml(raw_log: str) -> str:
    """
    Full pipeline: raw log → ready for SentenceTransformer.encode()
    Use this in ml_node.py at inference time.
    """
    return clean_for_ml(clean_for_regex(raw_log))

