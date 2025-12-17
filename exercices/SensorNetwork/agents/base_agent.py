"""
Base classes for agents in the sensor network.

Provides Agent base class with lifecycle helpers.
"""

import logging
from typing import Optional
import threading
import time

LOG = logging.getLogger("base_agent")


class Agent:
    """
    Generic agent base class.

    Agents own an MQTT client (injected) and can start/stop themselves. Concrete agents
    should override the start() and stop() methods and register callbacks where required.
    """

    def __init__(self, mqtt_client, agent_id: Optional[str] = None):
        """
        Args:
            mqtt_client: an instance of MQTTClient wrapper.
            agent_id: optional identifier string.
        """
        self.mqtt = mqtt_client
        self.agent_id = agent_id or f"agent_{int(time.time()*1000)%10000}"
        self._running = False
        self._lock = threading.Lock()

    def start(self):
        """Start the agent; override in subclass."""
        raise NotImplementedError

    def stop(self):
        """Stop the agent; override in subclass."""
        raise NotImplementedError
