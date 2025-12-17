"""
Detection agent for anomalies.

Implements a simple detection: a reading that is more than 2 standard deviations from the room average
is considered anomalous. It publishes alerts to `home/alerts/{room}`.
"""

import logging
import time
from collections import deque
import math

from .base_agent import Agent

LOG = logging.getLogger("detection_agent")


class DetectionAgent(Agent):
    """
    Agent that subscribes to both sensor readings and averages, and publishes alerts when anomalies are detected.

    Approach:
    - Maintain circular buffer of recent values per measurement
    - When a reading arrives, compare to rolling average & stddev and publish an alert if > 2*stddev
    """

    def __init__(self, mqtt_client, room: str, measurement: str, window_size: int = 30):
        """
        Args:
            mqtt_client: MQTTClient instance.
            room: room id.
            measurement: measurement string.
            window_size: number of recent sensor readings kept to compute mean/stddev.
        """
        super().__init__(mqtt_client)
        self.room = room
        self.measurement = measurement
        self.window_size = window_size
        self._buffer = deque(maxlen=self.window_size)
        # subscribe to sensor topics for this measurement
        pattern = f"home/{self.room}/{self.measurement}/#"
        self.mqtt.subscribe(pattern)
        self.mqtt.set_message_callback(self._on_message)
        LOG.info("DetectionAgent subscribed to %s", pattern)

    def _compute_stats(self):
        """Compute mean and standard deviation of current buffer."""
        n = len(self._buffer)
        if n == 0:
            return None, None
        mean = sum(self._buffer) / n
        variance = sum((x - mean) ** 2 for x in self._buffer) / n
        stddev = math.sqrt(variance)
        return mean, stddev

    def _on_message(self, topic: str, payload: dict):
        """
        Handle incoming reading: update stats and publish alert if needed.
        """
        try:
            value = float(payload.get("value"))
            sensor_id = payload.get("sensor_id")
            timestamp = payload.get("timestamp", int(time.time()))
        except Exception:
            LOG.debug("Invalid payload in detection agent: %s", payload)
            return

        # Update rolling buffer
        self._buffer.append(value)
        mean, stddev = self._compute_stats()
        # If we don't have stats yet, skip detection
        if mean is None or stddev is None:
            return

        # Detect anomaly: > 2 * stddev away from mean
        threshold = 2 * (stddev if stddev > 0 else 0.0001)  # avoid zero stddev
        deviation = abs(value - mean)
        if deviation > threshold:
            # Build alert with suspected sensor id and context
            alert = {
                "timestamp": int(timestamp),
                "room": self.room,
                "measurement": self.measurement,
                "sensor_id": sensor_id,
                "value": value,
                "mean": mean,
                "stddev": stddev,
                "deviation": deviation,
                "reason": f"value deviates by {deviation:.2f} (> 2 * stddev={threshold:.2f})"
            }
            topic_alert = f"home/alerts/{self.room}"
            try:
                self.mqtt.publish(topic_alert, alert)
                LOG.warning("Published alert to %s: %s", topic_alert, alert)
            except Exception:
                LOG.exception("Failed to publish alert")
