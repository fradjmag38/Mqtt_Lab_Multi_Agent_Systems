"""
Supervisor implementing the Contract Net Protocol rounds.

The supervisor:
- publishes CfP on 'contractnet/cfp'
- waits for proposals on 'contractnet/proposal' for a deadline
- selects best proposal (min time) and notifies acceptance/rejection
"""

import logging
import time
from threading import Event

from exercices.ContractNet.mqtt_client import MQTTClient


LOG = logging.getLogger("supervisor")


class Supervisor:
    """
    Supervisor that coordinates job allocation rounds.
    """

    def __init__(self, broker: str, deadline: float = 5.0):
        """
        Args:
            broker: broker host
            deadline: time to wait for proposals (seconds)
        """
        self.mqtt = MQTTClient(broker_host=broker, client_id="supervisor")
        self.deadline = deadline
        self.proposals = []
        self._waiting = Event()
        self.mqtt.set_message_callback(self._on_message)
        self.mqtt.start()
        # subscribe to proposals and completions
        self.mqtt.subscribe("contractnet/proposal")
        self.mqtt.subscribe("contractnet/done")

    def _on_message(self, topic: str, payload: dict):
        """Handle proposals and completed notifications"""
        if topic == "contractnet/proposal":
            LOG.info("Supervisor received proposal: %s", payload)
            self.proposals.append(payload)
        elif topic == "contractnet/done":
            LOG.info("Job completed: %s", payload)

    def call_for_proposals(self, job: dict):
        """
        Issue a CfP and wait for proposals until deadline
        Then choose best proposal (lowest time) and send accept/reject messages
        """
        # Clear previous proposals
        self.proposals = []
        cfp = {"job": job, "timestamp": int(time.time())}
        LOG.info("Publishing CfP: %s", cfp)
        self.mqtt.publish("contractnet/cfp", cfp)
        # Wait for deadline
        LOG.info("Waiting %.2f seconds for proposals", self.deadline)
        time.sleep(self.deadline)
        # Evaluate
        if not self.proposals:
            LOG.warning("No proposals received for job %s", job)
            return None
        # pick proposal with min 'time'
        best = min(self.proposals, key=lambda p: p.get("time", float("inf")))
        LOG.info("Best proposal selected: %s", best)
        # send accept to the chosen machine
        machine_id = best.get("machine_id")
        accept_topic = f"contractnet/accept/{machine_id}"
        accept_message = {"job": job, "selected": machine_id}
        self.mqtt.publish(accept_topic, accept_message)
        # send rejects to others
        for p in self.proposals:
            m_id = p.get("machine_id")
            if m_id != machine_id:
                reject_topic = f"contractnet/reject/{m_id}"
                self.mqtt.publish(reject_topic, {"job": job, "rejected": m_id})
        return best
