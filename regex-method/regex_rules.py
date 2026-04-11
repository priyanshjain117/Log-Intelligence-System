REGEX_RULES = [

    # ================= Security (linux) =================
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

    # ================= Core Dumps (bgl) =================
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

    # ================= Thunderbird =================
    #
    # Observed patterns (directly from Thunderbird_2k.log):
    #
    # INFO  — crond session open/close (routine scheduled job lifecycle)
    #   e.g. "crond(pam_unix)[2915]: session closed for user root"
    #   e.g. "crond(pam_unix)[2907]: session opened for user root by (uid=0)"
    {
        "level": "INFO",
        "pattern": r"crond.*session (opened|closed) for user",
        "confidence": 0.93,
        "sources": ["thunderbird"]
    },

    # INFO  — ntpd clock sync (healthy time synchronisation events)
    #   e.g. "ntpd[7467]: synchronized to 10.100.20.250, stratum 3"
    {
        "level": "INFO",
        "pattern": r"ntpd\[.*\]: synchronized to .*, stratum \d+",
        "confidence": 0.92,
        "sources": ["thunderbird"]
    },

    # WARNING — gmetad datasource unreachable (monitoring data gap)
    #   e.g. "gmetad[1682]: data_thread() got not answer from any [Thunderbird_A8] datasource"
    {
        "level": "WARNING",
        "pattern": r"data_thread\(\) got not answer from any \[.*\] datasource",
        "confidence": 0.91,
        "sources": ["thunderbird"]
    },

    # WARNING — sendmail relay deferred / connection refused
    #   e.g. "sendmail[11176]: jA9J1WSU011176: ... stat=Deferred: Connection refused by [127.0.0.1]"
    {
        "level": "WARNING",
        "pattern": r"sendmail.*stat=Deferred",
        "confidence": 0.89,
        "sources": ["thunderbird"]
    },

    # WARNING — sendmail domain qualification failure
    #   e.g. "sendmail[11176]: unable to qualify my own domain name (badmin1) -- using short name"
    {
        "level": "WARNING",
        "pattern": r"sendmail.*unable to qualify my own domain name",
        "confidence": 0.88,
        "sources": ["thunderbird"]
    },

    # ERROR  — sshd connection lost / disconnected
    #   e.g. "sshd[19023]: connection lost: 'Connection closed.'"
    #   e.g. "sshd[19023]: Local disconnected: Connection closed."
    {
        "level": "ERROR",
        "pattern": r"sshd.*connection lost|sshd.*local disconnected",
        "confidence": 0.87,
        "sources": ["thunderbird"]
    },

    # WARNING — ntpd kernel time sync disabled (clock discipline problem)
    #   e.g. "ntpd[1815]: kernel time sync disabled 0041"
    {
        "level": "WARNING",
        "pattern": r"ntpd.*kernel time sync disabled",
        "confidence": 0.90,
        "sources": ["thunderbird"]
    },

    # INFO  — InfiniBand sweep events (normal fabric management)
    #   e.g. "ib_sm.x[24904]: [ib_sm_sweep.c:1831]: **** NEW SWEEP ****"
    #   e.g. "ib_sm.x[24904]: [ib_sm_sweep.c:1455]: No topology change"
    {
        "level": "INFO",
        "pattern": r"ib_sm.*new sweep|ib_sm.*no topology change|ib_sm.*no configuration change",
        "confidence": 0.85,
        "sources": ["thunderbird"]
    },

    # WARNING — RRD update time collision (monitoring metric skipped)
    #   e.g. "gmetad[1682]: RRD_update (...): illegal attempt to update using time X when last update time is X"
    {
        "level": "WARNING",
        "pattern": r"rrd_update.*illegal attempt to update using time",
        "confidence": 0.88,
        "sources": ["thunderbird"]
    },

    # ================= Hadoop =================
    #
    # Observed patterns (directly from Hadoop_2k.log):
    #
    # INFO  — MRAppMaster job/task state transitions (normal job lifecycle)
    #   e.g. "JobImpl: job_1445144423722_0020 Job Transitioned from NEW to INITED"
    #   e.g. "TaskImpl: task_1445144423722_0020_m_000000 Task Transitioned from NEW to SCHEDULED"
    {
        "level": "INFO",
        "pattern": r"transitioned from \w+ to \w+",
        "confidence": 0.90,
        "sources": ["hadoop"]
    },

    # INFO  — Container allocated to task attempt
    #   e.g. "RMContainerAllocator: Assigned container container_... to attempt_..."
    {
        "level": "INFO",
        "pattern": r"assigned container container_\S+ to attempt_",
        "confidence": 0.88,
        "sources": ["hadoop"]
    },

    # INFO  — Reduce slow start threshold check (normal scheduling)
    #   e.g. "RMContainerAllocator: Reduce slow start threshold not met. completedMapsForReduceSlowstart 1"
    {
        "level": "INFO",
        "pattern": r"reduce slow start threshold not met",
        "confidence": 0.86,
        "sources": ["hadoop"]
    },

    # WARNING — HDFS lease renewal failure (NameNode temporarily unreachable)
    #   e.g. "LeaseRenewer: Failed to renew lease for [DFSClient_...] for 271 seconds. Will retry shortly ..."
    {
        "level": "WARNING",
        "pattern": r"failed to renew lease for \[dfsclient.*\] for \d+ seconds",
        "confidence": 0.93,
        "sources": ["hadoop"]
    },

    # WARNING — IPC client address change detected (RM/NN failover or DNS change)
    #   e.g. "ipc.Client: Address change detected. Old: msra-sa-41/10.190.173.170:8030 New: msra-sa-41:8030"
    {
        "level": "WARNING",
        "pattern": r"address change detected\. old:.*new:",
        "confidence": 0.91,
        "sources": ["hadoop"]
    },

    # ERROR  — ResourceManager contact failure (critical — job cannot progress)
    #   e.g. "RMContainerAllocator: ERROR IN CONTACTING RM."
    {
        "level": "ERROR",
        "pattern": r"error in contacting rm",
        "confidence": 0.97,
        "sources": ["hadoop"]
    },

    # INFO  — IPC server retry (transient, not yet an error)
    #   e.g. "ipc.Client: Retrying connect to server: msra-sa-41:8030. Already tried 0 time(s)..."
    {
        "level": "INFO",
        "pattern": r"retrying connect to server:.*already tried \d+ time",
        "confidence": 0.84,
        "sources": ["hadoop"]
    },
]