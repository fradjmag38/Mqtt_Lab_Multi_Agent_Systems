"""
Factory producing sensor agent instances.

Design pattern: Factory. Allows creating different sensor types (temperature, humidity, light, presence).
"""

from typing import Dict, Any
import math
import time
import threading
import logging

from .base_agent import Agent

LOG = logging.getLogger("sensor_factory")


class SensorAgent(Agent):
    """
    Generic sensor that publishes periodic readings.

    It uses a simple sinusoidal function optionally combined with noise to simulate dynamics.
    """

    def __init__(self,
                 mqtt_client,
                 room: str,
                 measurement: str,
                 sensor_id: str,
                 period: float = 1.0,
                 amplitude: float = 1.0,
                 baseline: float = 20.0,
                 noise: float = 0.0):
        """
        Args:
            mqtt_client: MQTTClient instance.
            room: room identifier string.
            measurement: measurement type (temperature, humidity, etc).
            sensor_id: unique sensor id.
            period: seconds between published readings.
            amplitude: amplitude for simulated sinusoid.
            baseline: baseline value to center the sinusoid.
            noise: additive random noise amplitude.
        """
        super().__init__(mqtt_client, agent_id=sensor_id)
        self.room = room
        self.measurement = measurement
        self.sensor_id = sensor_id
        self.period = period
        self.amplitude = amplitude
        self.baseline = baseline
        self.noise = noise
        self._thread = None
        self._stop_event = threading.Event()
        # internal time counter used to compute sinusoid
        self._counter = 0.0

    def _compute_value(self) -> float:
        """Compute the simulated sensor value (sinus + small noise)."""
        t = self._counter
        # sinusoidal variation ensures different sensors produce different phases
        value = self.baseline + self.amplitude * math.sin(2 * math.pi * (t / 60.0))
        # optionally add small noise (simple uniform noise)
        if self.noise:
            import random
            value += (random.random() - 0.5) * 2 * self.noise
        # step the counter by period seconds
        self._counter += self.period
        return float(value)

    def start(self):
        """Start periodic publishing in a background thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name=f"Sensor-{self.sensor_id}")
        self._thread.start()
        LOG.info("Sensor %s started (room=%s measurement=%s)", self.sensor_id, self.room, self.measurement)

    def _loop(self):
        """Publishing loop executed in a separate thread."""
        topic = f"home/{self.room}/{self.measurement}/{self.sensor_id}"
        while not self._stop_event.is_set():
            value = self._compute_value()
            payload = {
                "timestamp": int(time.time()),
                "sensor_id": self.sensor_id,
                "value": value,
            }
            try:
                self.mqtt.publish(topic, payload)
            except Exception:
                LOG.exception("Failed to publish sensor reading")
            # wait for period seconds unless stopped
            stopped = self._stop_event.wait(timeout=self.period)
            if stopped:
                break

    def stop(self):
        """Stop the background thread gracefully."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        LOG.info("Sensor %s stopped", self.sensor_id)


class SensorFactory:
    """
    Factory for creating configured sensors.

    Use SensorFactory.create(...) to obtain a sensor instance with sensible defaults for
    measurement types.
    """

    @staticmethod
    def create(mqtt_client, room: str, measurement: str, sensor_id: str, **kwargs):
        """
        Create a SensorAgent configured for the given measurement.

        Args:
            mqtt_client: MQTT client wrapper.
            room: room id.
            measurement: measurement type string.
            sensor_id: unique id.
            kwargs: override defaults (period, amplitude, baseline, noise).
        Returns:
            SensorAgent instance.
        """
        # Provide measurement-specific sensible defaults
        defaults = {
            "temperature": {"baseline": 20.0, "amplitude": 2.5, "period": 2.0, "noise": 0.2},
            "humidity": {"baseline": 45.0, "amplitude": 10.0, "period": 3.0, "noise": 1.0},
            "luminosity": {"baseline": 300.0, "amplitude": 150.0, "period": 5.0, "noise": 5.0},
            "presence": {"baseline": 0.0, "amplitude": 1.0, "period": 10.0, "noise": 0.0},
        }
        cfg = defaults.get(measurement, {"baseline": 0.0, "amplitude": 1.0, "period": 2.0, "noise": 0.1})
        cfg.update(kwargs)
        return SensorAgent(
            mqtt_client=mqtt_client,
            room=room,
            measurement=measurement,
            sensor_id=sensor_id,
            period=cfg["period"],
            amplitude=cfg["amplitude"],
            baseline=cfg["baseline"],
            noise=cfg["noise"],
        )
