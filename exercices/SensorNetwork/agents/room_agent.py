"""
Room agent that manages multiple sensors and room-level actuators (heating, window).

Responsibilities:
- Create and manage sensors for the room using SensorFactory.
- Respond to control commands received on MQTT (e.g., heating on/off, open/close window).
- Apply simple modulation to sensor baselines when actuators change (simulates effect of heating or window).
- Publish room-level state on topic: home/{room}/state

The RoomAgent uses the MQTTClient wrapper to separate transport concerns.
"""

from typing import Dict, Optional
import logging
import time

from .base_agent import Agent
from .sensor_factory import SensorFactory, SensorAgent

LOG = logging.getLogger("room_agent")


class RoomAgent(Agent):
    """
    RoomAgent orchestrates sensors and reacts to control commands.

    Control topics (subscribe):
        home/{room}/control/#

    State topic (publish):
        home/{room}/state
    """

    def __init__(self, mqtt_client, room: str):
        """
        Initialize a RoomAgent.

        Args:
            mqtt_client: MQTTClient wrapper instance shared by agents.
            room: room identifier string.
        """
        super().__init__(mqtt_client, agent_id=f"room_{room}")
        self.room = room

        # sensor registry: sensor_id -> SensorAgent
        self.sensors: Dict[str, SensorAgent] = {}

        # actuators state
        self.heating_on: bool = False
        self.window_open: bool = False

        # baseline modifiers applied when actuators change
        # heating adds +delta_temp to temperature baseline while active
        self._heating_temp_delta = 2.5
        # window increases humidity and reduces temperature slightly
        self._window_humidity_delta = 8.0
        self._window_temp_delta = -1.5

        # register callback for control messages
        self.mqtt.set_message_callback(self._on_message)

        # subscribe to control topics for this room
        control_topic = f"home/{self.room}/control/#"
        self.mqtt.subscribe(control_topic)
        LOG.info("RoomAgent subscribed to control topic: %s", control_topic)

    # ---- sensor management ----
    def add_sensor(self, measurement: str, sensor_id: str, **kwargs):
        """
        Create and start a sensor for this room.

        Args:
            measurement: measurement type string.
            sensor_id: unique sensor id.
            **kwargs: override defaults passed to SensorFactory (baseline, noise, etc).
        """
        if sensor_id in self.sensors:
            LOG.warning("Sensor %s already exists in room %s", sensor_id, self.room)
            return

        # Create sensor via factory with provided overrides
        sensor = SensorFactory.create(self.mqtt, self.room, measurement, sensor_id, **kwargs)
        # Modify baseline according to current actuator state to reflect environment
        self._apply_actuators_to_sensor(sensor)
        # Start the sensor loop
        sensor.start()
        # Register sensor
        self.sensors[sensor_id] = sensor
        LOG.info("Added sensor %s (measurement=%s) to room %s", sensor_id, measurement, self.room)
        # Publish state update
        self._publish_state()

    def remove_sensor(self, sensor_id: str):
        """Stop and remove sensor with given id if present."""
        sensor = self.sensors.pop(sensor_id, None)
        if sensor:
            sensor.stop()
            LOG.info("Removed sensor %s from room %s", sensor_id, self.room)
            self._publish_state()
        else:
            LOG.warning("Attempt to remove unknown sensor %s in room %s", sensor_id, self.room)

    def list_sensors(self) -> Dict[str, str]:
        """Return a mapping sensor_id -> measurement for current sensors."""
        return {sid: getattr(s, "measurement", "unknown") for sid, s in self.sensors.items()}

    # ---- actuator logic ----
    def set_heating(self, on: bool):
        """
        Turn heating on/off for the room.

        When heating changes, adjust temperature sensors' baseline accordingly.
        """
        if self.heating_on == on:
            LOG.debug("Heating already in state %s for room %s", on, self.room)
            return
        self.heating_on = on
        LOG.info("Heating set to %s in room %s", on, self.room)
        # adjust sensors' baselines to simulate effect
        for sensor in self.sensors.values():
            if getattr(sensor, "measurement", "") == "temperature":
                # update baseline by adding/removing delta
                if on:
                    sensor.baseline += self._heating_temp_delta
                else:
                    sensor.baseline -= self._heating_temp_delta
                LOG.debug("Adjusted baseline of sensor %s -> %.2f", sensor.sensor_id, sensor.baseline)
        self._publish_state()

    def set_window(self, open_: bool):
        """
        Open or close the window.

        When window state changes, modulate humidity and temperature baselines.
        """
        if self.window_open == open_:
            LOG.debug("Window already in state %s for room %s", open_, self.room)
            return
        self.window_open = open_
        LOG.info("Window set to %s in room %s", open_, self.room)
        for sensor in self.sensors.values():
            if getattr(sensor, "measurement", "") == "humidity":
                # increase humidity baseline when window opened
                if open_:
                    sensor.baseline += self._window_humidity_delta
                else:
                    sensor.baseline -= self._window_humidity_delta
                LOG.debug("Adjusted humidity baseline of %s -> %.2f", sensor.sensor_id, sensor.baseline)
            if getattr(sensor, "measurement", "") == "temperature":
                # window tends to cool the room a bit
                if open_:
                    sensor.baseline += self._window_temp_delta
                else:
                    sensor.baseline -= self._window_temp_delta
                LOG.debug("Adjusted temperature baseline of %s -> %.2f", sensor.sensor_id, sensor.baseline)
        self._publish_state()

    def _apply_actuators_to_sensor(self, sensor: SensorAgent):
        """
        Apply current actuator-induced baseline changes to a sensor.

        Used when a sensor is created while actuators are already active.
        """
        if getattr(sensor, "measurement", "") == "temperature" and self.heating_on:
            sensor.baseline += self._heating_temp_delta
        if getattr(sensor, "measurement", "") == "humidity" and self.window_open:
            sensor.baseline += self._window_humidity_delta
        if getattr(sensor, "measurement", "") == "temperature" and self.window_open:
            sensor.baseline += self._window_temp_delta

    # ---- MQTT message handling ----
    def _on_message(self, topic: str, payload: dict):
        """
        Handle control messages sent to home/{room}/control/*.

        Expected control payloads:
            {"command": "heating", "value": true}   -> toggles heating
            {"command": "window", "value": true}    -> open/close window
            {"command": "add_sensor", "measurement": "temperature", "sensor_id": "t3"}
            {"command": "remove_sensor", "sensor_id": "t3"}
        """
        # Quick guard: ensure message concerns this room
        if not topic.startswith(f"home/{self.room}/control/"):
            return

        command = payload.get("command")
        LOG.debug("RoomAgent received control command: %s", payload)

        try:
            if command == "heating":
                value = bool(payload.get("value", False))
                self.set_heating(value)
            elif command == "window":
                value = bool(payload.get("value", False))
                self.set_window(value)
            elif command == "add_sensor":
                measurement = payload.get("measurement")
                sensor_id = payload.get("sensor_id")
                if measurement and sensor_id:
                    # Optional sensor parameters forwarded via payload (e.g., baseline, noise)
                    overrides = {}
                    for key in ("baseline", "amplitude", "period", "noise"):
                        if key in payload:
                            overrides[key] = payload[key]
                    self.add_sensor(measurement, sensor_id, **overrides)
                else:
                    LOG.warning("add_sensor missing fields: %s", payload)
            elif command == "remove_sensor":
                sensor_id = payload.get("sensor_id")
                if sensor_id:
                    self.remove_sensor(sensor_id)
                else:
                    LOG.warning("remove_sensor missing sensor_id: %s", payload)
            else:
                LOG.warning("Unknown control command for room %s: %s", self.room, payload)
        except Exception:
            LOG.exception("Error while handling control command: %s", payload)

    def _publish_state(self):
        """
        Publish the current room state on topic home/{room}/state.

        The state message contains actuators and a list of sensors with their types.
        """
        topic = f"home/{self.room}/state"
        state = {
            "timestamp": int(time.time()),
            "room": self.room,
            "heating_on": self.heating_on,
            "window_open": self.window_open,
            "sensors": self.list_sensors(),
        }
        try:
            self.mqtt.publish(topic, state)
            LOG.debug("Published room state to %s: %s", topic, state)
        except Exception:
            LOG.exception("Failed to publish room state for %s", self.room)

    # ---- lifecycle (no background loop required) ----
    def start(self):
        """Start the RoomAgent. Does not spawn its own thread; sensors run separately."""
        LOG.info("RoomAgent started for room %s", self.room)
        # publish initial state
        self._publish_state()

    def stop(self):
        """Stop all managed sensors and perform cleanup."""
        LOG.info("Stopping RoomAgent for room %s", self.room)
        for sensor in list(self.sensors.values()):
            try:
                sensor.stop()
            except Exception:
                LOG.exception("Error stopping sensor %s", getattr(sensor, "sensor_id", "unknown"))
        self.sensors.clear()
        LOG.info("RoomAgent stopped for room %s", self.room)
