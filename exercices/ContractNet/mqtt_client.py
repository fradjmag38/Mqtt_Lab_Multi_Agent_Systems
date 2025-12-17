
from typing import Optional, Callable
import json
import logging
import uuid
import threading
import paho.mqtt.client as mqtt

LOG = logging.getLogger("contractnet_mqtt")
LOG.setLevel(logging.INFO)


class MQTTClient:
    """Simplified wrapper"""

    def __init__(self, broker_host: str = "localhost", client_id: Optional[str] = None):
        self.broker_host = broker_host
        self.client_id = client_id or f"cn_{uuid.uuid4().hex[:8]}"
        self._client = mqtt.Client(client_id=self.client_id)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._message_callback: Optional[Callable[[str, dict], None]] = None
        self._running = False

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            LOG.info("Connected to broker as %s", self.client_id)
        else:
            LOG.error("Connect rc=%s", rc)

    def _on_message(self, client, userdata, mqtt_msg):
        topic = mqtt_msg.topic
        try:
            payload = json.loads(mqtt_msg.payload.decode("utf-8"))
        except Exception:
            payload = {"raw": mqtt_msg.payload}
        if self._message_callback:
            self._message_callback(topic, payload)

    def set_message_callback(self, cb):
        self._message_callback = cb

    def start(self):
        self._client.connect(self.broker_host)
        self._client.loop_start()
        self._running = True

    def stop(self):
        if self._running:
            self._client.loop_stop()
            self._client.disconnect()
            self._running = False

    def subscribe(self, topic):
        self._client.subscribe(topic)

    def publish(self, topic, payload):
        self._client.publish(topic, json.dumps(payload))
