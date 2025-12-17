"""
Interface agent.

Displays averages and alerts to the console (could be extended to a GUI).
"""

import logging

from .base_agent import Agent

LOG = logging.getLogger("interface_agent")


class InterfaceAgent(Agent):
    """
    InterfaceAgent subscribes to average and alert topics and prints nicely formatted logs.

    This is a simple console UI used for demonstrations.
    """

    def __init__(self, mqtt_client, room: str):
        """
        Args:
            mqtt_client: MQTTClient wrapper.
            room: room id to present data for.
        """
        super().__init__(mqtt_client)
        self.room = room
        # register callback
        self.mqtt.set_message_callback(self._on_message)
        # subscribe to averages and alerts
        self.mqtt.subscribe(f"home/{self.room}/+/average")
        self.mqtt.subscribe(f"home/alerts/{self.room}")

    def _on_message(self, topic: str, payload: dict):
        """Render received messages in a human-readable way."""
        if "/average" in topic:
            measurement = topic.split("/")[2]
            LOG.info("[Interface] Room=%s Measurement=%s Average=%.2f", payload.get("room"),
                     payload.get("measurement"), payload.get("room_average"))
        elif topic.startswith("home/alerts/"):
            LOG.warning("[Interface] ALERT for room %s: %s", self.room, payload)
        else:
            LOG.info("[Interface] Message on %s: %s", topic, payload)
