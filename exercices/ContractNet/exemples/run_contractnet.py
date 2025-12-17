#!/usr/bin/env python3
"""
Run a small Contract Net demo:
- Launch 3 machine agents (in separate processes ideally; for demo we run them in threads)
- Supervisor generates 5 jobs and calls for proposals
"""

import time
import logging
from threading import Thread

from exercices.ContractNet.machine_agent import MachineAgent
from exercices.ContractNet.supervisor import Supervisor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
LOG = logging.getLogger("run_contractnet")


def run_demo(broker="localhost"):
    # define machines and capabilities
    m1 = MachineAgent(broker, "machine_1", {"A": 2, "B": 5})
    m2 = MachineAgent(broker, "machine_2", {"A": 3, "C": 4})
    m3 = MachineAgent(broker, "machine_3", {"B": 4, "C": 6})

    # start machines (in this process; in larger scenarios prefer separate processes)
    for m in (m1, m2, m3):
        m.start()

    sup = Supervisor(broker, deadline=3.0)
    jobs = [{"name": "A"}, {"name": "B"}, {"name": "C"}, {"name": "A"}, {"name": "B"}]
    try:
        for job in jobs:
            LOG.info("Supervisor issuing job: %s", job)
            chosen = sup.call_for_proposals(job)
            LOG.info("Chosen proposal: %s", chosen)
            # wait a bit between CFPs
            time.sleep(2)
        # Let remaining jobs finish
        time.sleep(10)
    finally:
        LOG.info("Stopping machines")
        for m in (m1, m2, m3):
            m.stop()
        sup.mqtt.stop()


if __name__ == "__main__":
    run_demo()
