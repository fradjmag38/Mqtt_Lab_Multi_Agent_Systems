"""
Averaging agent.

Listens to sensor topics for a room and measurement, keeps a sliding window and publishes averages.
"""

from collections import deque, defaultdict
import time
import logging

from .base_agent import Agent

LOG = logging.getLogger("averaging_agent")


class AveragingAgent(Agent):
    """
    Agent that computes rolling averages for a given room and measurement type.

    Example topic subscription: home/bedroom1/temperature/#
    Publishes averages at a specified frequency to: home/{room}/{measurement}/average
    """

    def __init__(self, mqtt_client, room: str, measurement: str, window_size: int = 10, publish_period: float = 5.0):
        """
        Args:
            mqtt_client: MQTTClient instance.
            room: room id to monitor.
            measurement: measurement type.
            window_size: number of samples in the rolling window.
            publish_period: seconds between average publications.
        """
        super().__init__(mqtt_client)
        self.room = room
        self.measurement = measurement
        self.window_size = window_size
        self.publish_period = publish_period
        # mapping sensor_id -> deque of recent values
        self._values = defaultdict(lambda: deque(maxlen=self.window_size))
        self._last_publish = 0.0
        # register callback
        self.mqtt.set_message_callback(self._on_message)
        # subscribe to relevant topics
        subscribe_topic = f"home/{self.room}/{self.measurement}/#"
        self.mqtt.subscribe(subscribe_topic)
        LOG.info("AveragingAgent subscribed to %s", subscribe_topic)

    def _on_message(self, topic: str, payload: dict):
        """
        Handle incoming sensor messages, update internal buffers and publish averages periodically.

        Args:
            topic: topic string.
            payload: parsed JSON payload.
        """
        # expected topic: home/{room}/{measurement}/{sensor_id}
        try:
            sensor_id = payload.get("sensor_id")
            value = float(payload.get("value"))
        except Exception:
            LOG.debug("Ignoring invalid payload on %s: %s", topic, payload)
            return

        # update store
        self._values[sensor_id].append(value)
        LOG.debug("AveragingAgent: appended value for %s -> %s", sensor_id, value)

        # calculate and publish aggregated average at publish_period
        now = time.time()
        if now - self._last_publish >= self.publish_period:
            self._publish_average()
            self._last_publish = now

    def _publish_average(self):
        """
        Compute averages across all sensors for the measurement and publish result.
        The published payload includes per-sensor averages and a room-level average.
        """
        per_sensor = {}
        # aggregate values
        all_values = []
        for sensor_id, values in self._values.items():
            if len(values):
                avg = sum(values) / len(values)
                per_sensor[sensor_id] = avg
                all_values.extend(values)
        if not all_values:
            LOG.debug("No data to publish for %s/%s", self.room, self.measurement)
            return
        room_avg = sum(all_values) / len(all_values)
        payload = {
            "timestamp": int(time.time()),
            "room": self.room,
            "measurement": self.measurement,
            "room_average": room_avg,
            "per_sensor": per_sensor,
        }
        topic = f"home/{self.room}/{self.measurement}/average"
        try:
            self.mqtt.publish(topic, payload)
            LOG.info("Published average to %s: %s", topic, payload)
        except Exception:
            LOG.exception("Failed to publish average")
