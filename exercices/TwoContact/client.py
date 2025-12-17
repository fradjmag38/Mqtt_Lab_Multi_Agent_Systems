#!/usr/bin/env python3
"""
FirstContact client

This script implements a simple MQTT client that can act as 'ping' or 'pong'
It demonstrates connection, subscription and publication to verify the MQTT setup.

Usage:
    python client.py --role ping
    python client.py --role pong
"""

import argparse
import logging
import json
import time
import uuid
from threading import Event

import paho.mqtt.client as mqtt

# Configure logging globally for this module
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
LOG = logging.getLogger("firstcontact")

DEFAULT_BROKER = "localhost"
DEFAULT_TOPIC = "lab/first_contact/hello"


class SimpleClient:
    """Simple MQTT wrapper used for the first contact exercise."""

    def __init__(self, client_id: str = None, broker: str = DEFAULT_BROKER):
        """
        Initialize wrapper.

        Args:
            client_id: optional client id; if None, a random UUID is used.
            broker: MQTT broker hostname.
        """
        self.client_id = client_id or f"client_{uuid.uuid4().hex[:8]}"
        self.broker = broker
        # Create MQTT client instance
        self._client = mqtt.Client(client_id=self.client_id)
        # Events to allow graceful stops in examples
        self._stop_event = Event()
        # Attach callbacks
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, rc):
        """MQTT connect callback."""
        if rc == 0:
            LOG.info("Connected to MQTT broker '%s' as %s", self.broker, self.client_id)
        else:
            LOG.error("Connection failed with rc=%s", rc)

    def _on_message(self, client, userdata, msg):
        """MQTT message received callback."""
        try:
            payload = msg.payload.decode("utf-8")
        except Exception:
            payload = msg.payload
        LOG.info("Received message on %s: %s", msg.topic, payload)

    def start(self):
        """Connect to broker and start the loop in a background thread."""
        LOG.debug("Starting client loop")
        self._client.connect(self.broker)
        self._client.loop_start()

    def stop(self):
        """Stop MQTT loop and disconnect."""
        LOG.debug("Stopping client loop")
        self._client.loop_stop()
        self._client.disconnect()

    def subscribe(self, topic: str):
        """Subscribe to a topic."""
        LOG.info("Subscribing to topic %s", topic)
        self._client.subscribe(topic)

    def publish(self, topic: str, payload: dict):
        """Publish a JSON payload to a topic."""
        payload_str = json.dumps(payload)
        LOG.info("Publishing to %s: %s", topic, payload_str)
        self._client.publish(topic, payload_str)


def run_role(role: str, broker: str = DEFAULT_BROKER, topic: str = DEFAULT_TOPIC):
    """
    Run the ping/pong behavior.

    Args:
        role: 'ping' or 'pong'
        broker: MQTT broker host.
        topic: topic used for exchanges.
    """
    client = SimpleClient(broker=broker)
    client.start()
    client.subscribe(topic)

    try:
        # Main loop: ping sends 'ping' and waits for 'pong'; pong responds to any ping
        if role == "ping":
            for i in range(1, 6):
                message = {"type": "ping", "seq": i}
                client.publish(topic, message)
                time.sleep(1)  # wait for responses
            LOG.info("Ping finished")
        else:  # pong
            LOG.info("Pong ready: will respond automatically when ping arrives")
            # Keep running to respond; messages are logged by _on_message
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        LOG.info("Interrupted by user")
    finally:
        client.stop()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", choices=("ping", "pong"), required=True)
    parser.add_argument("--broker", default=DEFAULT_BROKER)
    parser.add_argument("--topic", default=DEFAULT_TOPIC)
    args = parser.parse_args()
    run_role(args.role, broker=args.broker, topic=args.topic)


if __name__ == "__main__":
    main()
