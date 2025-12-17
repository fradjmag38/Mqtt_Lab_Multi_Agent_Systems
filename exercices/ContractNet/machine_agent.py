"""
Machine agent implementation for Contract Net.

Each machine has a capability table mapping job_name -> processing_time_seconds.
When receiving a CfP it either rejects (cannot do job) or sends a proposal with estimated time.
When accepted, it executes the job (sleep) and publishes completion.
"""

import logging
import time
from threading import Thread, Event

from exercices.ContractNet.mqtt_client import MQTTClient


LOG = logging.getLogger("machine_agent")


class MachineAgent:
    """
    Machine agent that subscribes to CfP and replies with proposals.

    Args:
        broker: broker host
        machine_id: unique id
        capabilities: dict str->int mapping job_name to duration (seconds)
    """

    def __init__(self, broker: str, machine_id: str, capabilities: dict):
        self.mqtt = MQTTClient(broker_host=broker, client_id=machine_id)
        self.machine_id = machine_id
        self.capabilities = capabilities
        self._busy = False
        self._stop = Event()
        self.mqtt.set_message_callback(self._on_message)

    def start(self):
        self.mqtt.start()
        self.mqtt.subscribe("contractnet/cfp")
        self.mqtt.subscribe(f"contractnet/accept/{self.machine_id}")
        self.mqtt.subscribe(f"contractnet/reject/{self.machine_id}")
        LOG.info("Machine %s started with capabilities %s", self.machine_id, self.capabilities)

    def stop(self):
        self._stop.set()
        self.mqtt.stop()

    def _on_message(self, topic: str, payload: dict):
        # CfP handling
        if topic == "contractnet/cfp":
            if self._busy:
                # do not reply if busy
                LOG.debug("Machine %s busy; ignoring CfP", self.machine_id)
                return
            job = payload.get("job")
            job_name = job.get("name")
            # If we can do job, send proposal
            if job_name in self.capabilities:
                duration = self.capabilities[job_name]
                proposal = {
                    "machine_id": self.machine_id,
                    "job": job,
                    "time": duration
                }
                LOG.info("Machine %s sending proposal for job %s -> %s", self.machine_id, job_name, duration)
                self.mqtt.publish("contractnet/proposal", proposal)
            else:
                # send explicit reject if desired 
                reject = {"machine_id": self.machine_id, "job": job, "reason": "cannot_do"}
                self.mqtt.publish("contractnet/reject", reject)
        elif topic == f"contractnet/accept/{self.machine_id}":
            # we received the accept for the job
            job = payload.get("job")
            LOG.info("Machine %s accepted job %s", self.machine_id, job)
            # start job execution in background thread
            Thread(target=self._execute_job, args=(job,), daemon=True).start()
        elif topic == f"contractnet/reject/{self.machine_id}":
            LOG.info("Machine %s was rejected for job: %s", self.machine_id, payload)

    def _execute_job(self, job: dict):
        """
        Execute job (simulate by sleeping for the declared duration).
        Publish completion to contractnet/done.
        """
        job_name = job.get("name")
        duration = self.capabilities.get(job_name, 0)
        self._busy = True
        LOG.info("Machine %s starting job %s for %s seconds", self.machine_id, job_name, duration)
        time.sleep(duration)
        done = {"machine_id": self.machine_id, "job": job, "duration": duration, "timestamp": int(time.time())}
        self.mqtt.publish("contractnet/done", done)
        LOG.info("Machine %s completed job %s", self.machine_id, job_name)
        self._busy = False
