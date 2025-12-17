"""
Sensor factory and SensorAgent implementation.

Design patterns:
- Factory: SensorFactory.create(...) returns configured SensorAgent instances.
- SensorAgent publishes periodic readings to MQTT using the MQTTClient wrapper.

All docstrings are in English for Sphinx documentation.
"""

from typing import Optional, Dict
import math
import time
import threading
import logging
import random

from .base_agent import Agent

LOG = logging.getLogger("sensor_factory")


class SensorAgent(Agent):
    """
    Generic sensor agent that periodically publishes simulated readings.

    The simulation uses a sinusoidal base component (to emulate daily/periodic
    variations) plus optional uniform noise. The sensor publishes JSON payloads
    containing 'timestamp', 'sensor_id' and 'value' on topic:
        home/{room}/{measurement}/{sensor_id}

    Attributes:
        room: logical room id (e.g. "bedroom1").
        measurement: measurement type (temperature, humidity, luminosity, presence).
        sensor_id: unique sensor identifier.
        period: publishing period in seconds.
        amplitude: amplitude of sinusoidal variation.
        baseline: baseline value around which sinusoid oscillates.
        noise: max amplitude of uniform random noise.
    """

    def __init__(
        self,
        mqtt_client,
        room: str,
        measurement: str,
        sensor_id: str,
        period: float = 1.0,
        amplitude: float = 1.0,
        baseline: float = 20.0,
        noise: float = 0.0,
    ):
        super().__init__(mqtt_client, agent_id=sensor_id)
        self.room = room
        self.measurement = measurement
        self.sensor_id = sensor_id

        # Simulation parameters
        self.period = max(0.1, float(period))  # enforce minimal positive period
        self.amplitude = float(amplitude)
        self.baseline = float(baseline)
        self.noise = float(noise)

        # internal thread control
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # phase offset so sensors are not perfectly synchronized
        self._phase = random.random() * 2 * math.pi

        # internal time counter used to compute value
        self._internal_time = 0.0

    def _compute_value(self) -> float:
        """
        Compute a simulated value.

        Uses a sinusoidal function with period 60s (configurable by adjusting
        the divisor), plus uniform noise. The result is clamped to a sensible
        numeric range by the caller if needed.
        """
        t = self._internal_time
        # sinusoid with period ~60s scaled by amplitude
        sinus = math.sin(2 * math.pi * (t / 60.0) + self._phase)
        value = self.baseline + self.amplitude * sinus

        # add uniform noise in [-noise, +noise]
        if self.noise:
            value += (random.random() - 0.5) * 2.0 * self.noise

        # increment internal time by period for next call
        self._internal_time += self.period
        return float(value)

    def start(self):
        """Start the periodic publishing loop in a background thread."""
        # If thread already running, nothing to do
        if self._thread and self._thread.is_alive():
            LOG.debug("Sensor %s already running", self.sensor_id)
            return

        # Clear stop flag and start thread
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._loop, name=f"Sensor-{self.sensor_id}", daemon=True
        )
        self._thread.start()
        LOG.info(
            "SensorAgent started: id=%s room=%s measurement=%s period=%.2fs",
            self.sensor_id,
            self.room,
            self.measurement,
            self.period,
        )

    def _loop(self):
        """Main loop executed by the background thread to publish periodic readings."""
        topic = f"home/{self.room}/{self.measurement}/{self.sensor_id}"
        while not self._stop_event.is_set():
            try:
                value = self._compute_value()
                payload = {"timestamp": int(time.time()), "sensor_id": self.sensor_id, "value": value}
                # publish with the MQTTClient wrapper (serialises to JSON)
                self.mqtt.publish(topic, payload)
                LOG.debug("Sensor %s published to %s: %s", self.sensor_id, topic, payload)
            except Exception:
                LOG.exception("Error while computing/publishing sensor value for %s", self.sensor_id)
            # Wait for the period or until stopped
            if self._stop_event.wait(timeout=self.period):
                break

    def stop(self):
        """Stop the sensor's background thread and wait for it to finish."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        LOG.info("SensorAgent stopped: %s", self.sensor_id)


class SensorFactory:
    """
    Factory responsible for creating sensors configured with sensible defaults
    according to the measurement type.

    Usage:
        sensor = SensorFactory.create(mqtt_client, "bedroom1", "temperature", "t1")
    """

    # sensible defaults per measurement type
    _DEFAULTS = {
        "temperature": {"baseline": 20.0, "amplitude": 2.5, "period": 2.0, "noise": 0.2},
        "humidity": {"baseline": 45.0, "amplitude": 10.0, "period": 3.0, "noise": 1.0},
        "luminosity": {"baseline": 300.0, "amplitude": 150.0, "period": 5.0, "noise": 5.0},
        "presence": {"baseline": 0.0, "amplitude": 1.0, "period": 10.0, "noise": 0.0},
    }

    @staticmethod
    def create(
        mqtt_client,
        room: str,
        measurement: str,
        sensor_id: str,
        **overrides,
    ) -> SensorAgent:
        """
        Create and return a SensorAgent instance configured for the given measurement.

        Args:
            mqtt_client: MQTTClient wrapper instance (transport).
            room: room identifier string.
            measurement: measurement type (e.g., "temperature").
            sensor_id: unique sensor id string.
            **overrides: optional parameters to override defaults, e.g. baseline=22.0.
        Returns:
            SensorAgent instance.
        """
        # pick defaults for measurement if available
        cfg: Dict[str, float] = dict(SensorFactory._DEFAULTS.get(measurement, {}))
        # apply overrides (period, amplitude, baseline, noise)
        cfg.update(overrides)

        # Ensure keys exist with fallback values
        period = float(cfg.get("period", 2.0))
        amplitude = float(cfg.get("amplitude", 1.0))
        baseline = float(cfg.get("baseline", 0.0))
        noise = float(cfg.get("noise", 0.0))

        sensor = SensorAgent(
            mqtt_client=mqtt_client,
            room=room,
            measurement=measurement,
            sensor_id=sensor_id,
            period=period,
            amplitude=amplitude,
            baseline=baseline,
            noise=noise,
        )
        LOG.debug(
            "Created sensor %s (%s/%s) cfg=%s",
            sensor_id,
            room,
            measurement,
            {"period": period, "amplitude": amplitude, "baseline": baseline, "noise": noise},
        )
        return sensor
