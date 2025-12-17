"""
MQTT wrapper module.

Provides a small, reusable MQTTClient class to separate MQTT transport from agent logic.
"""

from typing import Callable, Optional
import json
import logging
import uuid
import threading
import time

import paho.mqtt.client as mqtt

LOG = logging.getLogger("mqtt_client")
LOG.setLevel(logging.INFO)


class MQTTClient:
    """
    Lightweight wrapper on top of paho-mqtt to separate transport from agent logic.

    This wrapper:
    - runs MQTT loop in background thread
    - provides subscribe/publish helpers with JSON serialization
    - allows registering high-level message callbacks
    """

    def __init__(self, broker_host: str = "localhost", client_id: Optional[str] = None):
        """
        Initialize the MQTT client

        Args:
            broker_host: MQTT broker hostname (default: "localhost").
            client_id: optional client identifier. If None, a random id is generated.
        """
        self.broker_host = broker_host
        self.client_id = client_id or f"agent_{uuid.uuid4().hex[:8]}"
        self._client = mqtt.Client(client_id=self.client_id)
        # Register callbacks
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        # user-level callback is stored here
        self._message_callback: Optional[Callable[[str, dict], None]] = None
        self._lock = threading.Lock()
        self._is_running = False

    def _on_connect(self, client, userdata, flags, rc):
        """Internal connect callback (logs status)."""
        if rc == 0:
            LOG.info("MQTT connected to %s (client=%s)", self.broker_host, self.client_id)
        else:
            LOG.error("MQTT connect failed rc=%s", rc)

    def _on_message(self, client, userdata, mqtt_msg):
        """Internal message callback; dispatch to user callback after deserializing JSON."""
        topic = mqtt_msg.topic
        try:
            payload_str = mqtt_msg.payload.decode("utf-8")
            payload = json.loads(payload_str)
        except Exception:
            # if not JSON, pass raw bytes
            payload = {"raw": mqtt_msg.payload}
        if self._message_callback:
            try:
                self._message_callback(topic, payload)
            except Exception as exc:
                LOG.exception("Error in message callback: %s", exc)

    def set_message_callback(self, callback: Callable[[str, dict], None]):
        """
        Set a callback to be called for every received message.

        Args:
            callback: function(topic, payload_dict).
        """
        with self._lock:
            self._message_callback = callback

    def start(self):
        """Connect to the broker and start the network loop in background thread."""
        with self._lock:
            if self._is_running:
                return
            self._client.connect(self.broker_host)
            self._client.loop_start()
            self._is_running = True
            LOG.debug("MQTT client loop started")

    def stop(self):
        """Stop the network loop and disconnect"""
        with self._lock:
            if not self._is_running:
                return
            self._client.loop_stop()
            self._client.disconnect()
            self._is_running = False
            LOG.debug("MQTT client loop stopped")

    def subscribe(self, topic: str, qos: int = 0):
        """
        Subscribe to a topic.

        Args:
            topic: topic string, may contain wildcards.
            qos: quality of service .
        """
        LOG.debug("Subscribing to %s (qos=%s)", topic, qos)
        self._client.subscribe(topic, qos=qos)

    def publish(self, topic: str, payload: dict, qos: int = 0, retain: bool = False):
        """
        Publish a JSON-encoded payload to a topic.

        Args:
            topic: destination topic
            payload: JSON-serializable object
            qos: quality of service
            retain: retain flag.
        """
        payload_str = json.dumps(payload)
        LOG.debug("Publishing to %s: %s", topic, payload_str)
        self._client.publish(topic, payload_str, qos=qos, retain=retain)
