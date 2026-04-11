"""
Log Dataset Cleaner — Phase 1 / Phase 2 Splitter
=================================================
Parses HDFS, BGL, Thunderbird, Hadoop logs.
- Rows matched by RegexEngine  → regex_classified.csv  (Phase 1 done)
- Rows unmatched               → ml_training.csv        (Phase 2 training)
"""

import re
import csv
import os
from dataclasses import dataclass, field
from typing import Optional
from regex_engine import RegexEngine


# ─────────────────────────────────────────────
#  Data container
# ─────────────────────────────────────────────

@dataclass
class LogRecord:
    source: str
    raw_message: str
    clean_message: str
    level: Optional[str] = None          # ground-truth if extractable
    classified_by: Optional[str] = None
    confidence: float = 0.0


# ─────────────────────────────────────────────
#  Text normaliser  (shared by all parsers)
# ─────────────────────────────────────────────

# Tokens that carry no semantic value for an ML model
_NOISE_PATTERNS = [
    (r'\b(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?\b',  '<IP>'),        # IP:port
    (r'\bblk_-?\d+\b',                           '<BLK>'),       # HDFS block IDs
    (r'\b[0-9a-f]{8,}\b',                        '<HEX>'),       # hex addresses
    (r'\b\d{10,}\b',                              '<TS>'),        # unix timestamps
    (r'\b\d+\.\d+\.\d+\.\d+\b',                  '<VER>'),       # version numbers
    (r'(?<!\w)/[\w./-]+',                         '<PATH>'),      # file paths
    (r'\[\d+\]',                                  ''),            # PIDs like [2915]
    (r'\s{2,}',                                   ' '),           # extra whitespace
]

def normalise(text: str) -> str:
    for pattern, replacement in _NOISE_PATTERNS:
        text = re.sub(pattern, replacement, text)
    return text.strip()


# ─────────────────────────────────────────────
#  Per-source parsers
# ─────────────────────────────────────────────

# HDFS format:  081109 203615 148 INFO dfs.DataNode$...: <message>
_HDFS_RE = re.compile(
    r'^\d{6}\s+\d{6}\s+\d+\s+'          # date time threadid
    r'(?P<level>\w+)\s+'                  # INFO / WARN / ERROR
    r'[\w.$]+:\s*'                        # logger class
    r'(?P<msg>.+)$'
)

def parse_hdfs(line: str) -> Optional[LogRecord]:
    m = _HDFS_RE.match(line.strip())
    if not m:
        return None
    level_raw = m.group('level').upper()
    level_map = {'INFO': 'INFO', 'WARN': 'WARNING', 'WARNING': 'WARNING',
                 'ERROR': 'ERROR', 'FATAL': 'CRITICAL', 'DEBUG': 'INFO'}
    level = level_map.get(level_raw, 'INFO')
    msg   = m.group('msg')
    return LogRecord(
        source='hdfs',
        raw_message=msg,
        clean_message=normalise(msg),
        level=level
    )


# BGL format:  <flag> <secs> <date> <node> <datetime> <node> RAS <comp> <LEVEL> <message>
# flag is '-' for normal or an alert type like 'APPREAD'
_BGL_RE = re.compile(
    r'^(?P<flag>\S+)\s+'                 # - or APPREAD etc.
    r'\d+\s+'                            # unix timestamp
    r'\S+\s+'                            # date
    r'\S+\s+'                            # node
    r'\S+\s+'                            # datetime
    r'\S+\s+'                            # node repeat
    r'RAS\s+\S+\s+'                      # RAS KERNEL / RAS APP
    r'(?P<level>INFO|WARN|WARNING|ERROR|FATAL|FAILURE|SEVERE)\s+'
    r'(?P<msg>.+)$',
    re.IGNORECASE
)

def parse_bgl(line: str) -> Optional[LogRecord]:
    m = _BGL_RE.match(line.strip())
    if not m:
        return None
    level_raw = m.group('level').upper()
    level_map = {'INFO': 'INFO', 'WARN': 'WARNING', 'WARNING': 'WARNING',
                 'ERROR': 'ERROR', 'FATAL': 'CRITICAL',
                 'FAILURE': 'ERROR', 'SEVERE': 'ERROR'}
    # If flag is not '-', it's an alert — at least ERROR
    flag  = m.group('flag')
    level = level_map.get(level_raw, 'INFO')
    if flag != '-' and level == 'INFO':
        level = 'ERROR'
    msg = m.group('msg')
    return LogRecord(
        source='bgl',
        raw_message=msg,
        clean_message=normalise(msg),
        level=level
    )


# Thunderbird format: <flag> <secs> <date> <host> <Month Day HH:MM:SS> <host/host> <process>[pid]: <msg>
_TB_RE = re.compile(
    r'^(?P<flag>\S+)\s+'                 # - or alert type
    r'\d+\s+'                            # unix timestamp
    r'\S+\s+'                            # date
    r'\S+\s+'                            # hostname
    r'\S+\s+\d+\s+'                      # Month Day
    r'\S+\s+'                            # HH:MM:SS
    r'\S+\s+'                            # host/host
    r'(?P<proc>[\w.()\-]+)(?:\[\d+\])?:\s*'  # process[pid]:
    r'(?P<msg>.+)$'
)

# Thunderbird has no native level field → derive from keywords
_TB_LEVEL_HINTS = [
    (re.compile(r'\b(fatal|panic|emerg)\b',  re.I), 'CRITICAL'),
    (re.compile(r'\b(error|fail|denied|refused|invalid|unable|cannot|can\'t)\b', re.I), 'ERROR'),
    (re.compile(r'\b(warn|warning|deprecated|deferred)\b', re.I), 'WARNING'),
]

def parse_thunderbird(line: str) -> Optional[LogRecord]:
    m = _TB_RE.match(line.strip())
    if not m:
        return None
    msg  = m.group('msg')
    flag = m.group('flag')
    # Derive level
    level = 'INFO'
    if flag != '-':
        level = 'ERROR'
    else:
        for pattern, lvl in _TB_LEVEL_HINTS:
            if pattern.search(msg):
                level = lvl
                break
    return LogRecord(
        source='thunderbird',
        raw_message=msg,
        clean_message=normalise(msg),
        level=level
    )


# Hadoop format:  2015-10-18 18:01:47,978 INFO [thread] org.apache...: <msg>
_HADOOP_RE = re.compile(
    r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},\d+\s+'
    r'(?P<level>\w+)\s+'
    r'\[.*?\]\s+'
    r'[\w.$]+:\s*'
    r'(?P<msg>.+)$'
)

def parse_hadoop(line: str) -> Optional[LogRecord]:
    m = _HADOOP_RE.match(line.strip())
    if not m:
        return None
    level_raw = m.group('level').upper()
    level_map = {'INFO': 'INFO', 'WARN': 'WARNING', 'WARNING': 'WARNING',
                 'ERROR': 'ERROR', 'FATAL': 'CRITICAL', 'DEBUG': 'INFO'}
    level = level_map.get(level_raw, 'INFO')
    msg   = m.group('msg')
    return LogRecord(
        source='hadoop',
        raw_message=msg,
        clean_message=normalise(msg),
        level=level
    )


# ─────────────────────────────────────────────
#  Source registry
# ─────────────────────────────────────────────

SOURCES = {
    'hdfs':        parse_hdfs,
    'bgl':         parse_bgl,
    'thunderbird': parse_thunderbird,
    'hadoop':      parse_hadoop,
}


# ─────────────────────────────────────────────
#  Pipeline
# ─────────────────────────────────────────────

def process_file(filepath: str, source: str, engine: RegexEngine):
    """Parse every line, run regex engine, return (classified, unclassified)."""
    parser = SOURCES[source]
    classified   = []
    unclassified = []
    skipped      = 0

    with open(filepath, 'r', errors='replace') as f:
        for raw_line in f:
            record = parser(raw_line)
            if record is None:
                skipped += 1
                continue

            result = engine.classify({
                'clean_message': record.clean_message,
                'source': record.source
            })

            record.classified_by = result['classified_by']
            record.confidence    = result['confidence']

            # Override level with regex finding if matched
            if result['classified_by'] == 'regex':
                record.level = result['level']
                classified.append(record)
            else:
                unclassified.append(record)

    print(f"  [{source.upper():12s}]  parsed={len(classified)+len(unclassified):>5}  "
          f"regex_matched={len(classified):>5}  "
          f"for_ml={len(unclassified):>5}  "
          f"skipped={skipped:>4}")
    return classified, unclassified


def write_csv(records: list[LogRecord], path: str):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'source', 'level', 'confidence', 'classified_by',
            'clean_message', 'raw_message'
        ])
        writer.writeheader()
        for r in records:
            writer.writerow({
                'source':         r.source,
                'level':          r.level,
                'confidence':     r.confidence,
                'classified_by':  r.classified_by,
                'clean_message':  r.clean_message,
                'raw_message':    r.raw_message,
            })
    print(f"  → Saved {len(records):>6} rows to {os.path.basename(path)}")


# ─────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────

if __name__ == '__main__':

    LOG_FILES = {
        'hdfs':        'data/raw/hdfs/HDFS_2k.log',
        'bgl':         'data/raw/bgl/BGL_2k.log',
        'thunderbird': 'data/raw/thunderbird/Thunderbird_2k.log',
        'hadoop':      'data/raw/hadoop/Hadoop_2k.log',
    }

    OUT_REGEX = 'regex_classified.csv'
    OUT_ML    = 'ml_training.csv'

    engine = RegexEngine()

    all_classified   = []
    all_unclassified = []

    print("\n=== Processing Log Files ===\n")
    for source, filename in LOG_FILES.items():
        if not os.path.exists(filename):
            print(f"  [SKIP] {filename} not found")
            continue
        classified, unclassified = process_file(filename, source, engine)
        all_classified.extend(classified)
        all_unclassified.extend(unclassified)

    print(f"\n=== Summary ===")
    print(f"  Total parsed       : {len(all_classified) + len(all_unclassified)}")
    print(f"  Regex classified   : {len(all_classified)}")
    print(f"  For ML training    : {len(all_unclassified)}")

    print(f"\n=== Writing CSVs ===\n")
    write_csv(all_classified,   OUT_REGEX)
    write_csv(all_unclassified, OUT_ML)

    print(f"\n✓ Done.\n")