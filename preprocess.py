from adapters.generic_adapter import GenericAdapter

ADAPTERS = {
    "apache": ApacheAdapter(),
    "hdfs": HDFSAdapter(),
    "bgl": BGLAdapter(),
    "linux": LinuxAdapter(),
    "mac": MacAdapter()
}

def route_log(raw_log: str, source: str = None):
    if source and source in ADAPTERS:
        return ADAPTERS[source].parse(raw_log)
    else:
        return GenericAdapter().parse(raw_log)