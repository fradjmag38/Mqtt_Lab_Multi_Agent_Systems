"""
High-level simulation orchestrator for the Smart Home Sensor Network example.

This version creates a RoomAgent per room (e.g. "bedroom1", "living_room"),
registers sensors automatically at startup, and starts averaging/detection/interface
agents per room/measurement. It demonstrates dynamic behaviour and control via MQTT
control topics: home/{room}/control/*.

"""

import time
import logging
import threading
from typing import List

from mqtt_client import MQTTClient
from agents.sensor_factory import SensorFactory
from agents.averaging_agent import AveragingAgent
from agents.detection_agent import DetectionAgent
from agents.interface_agent import InterfaceAgent
from agents.room_agent import RoomAgent

LOG = logging.getLogger("simulation")
LOG.setLevel(logging.INFO)


def _create_room(mqtt: MQTTClient, room_name: str) -> RoomAgent:
    """
    Create a RoomAgent for the given room and populate it with default sensors.

    Args:
        mqtt: shared MQTTClient instance.
        room_name: name of the room (e.g "bedroom1").
    Returns:
        RoomAgent instance.
    """
    room = RoomAgent(mqtt, room=room_name)
    # Add sensible default sensors for typical rooms
    if "bedroom" in room_name or "room" in room_name:
        # two temperature sensors, one humidity sensor
        room.add_sensor("temperature", sensor_id=f"{room_name}_temp_01")
        room.add_sensor("temperature", sensor_id=f"{room_name}_temp_02", baseline=21.0, noise=0.15)
        room.add_sensor("humidity", sensor_id=f"{room_name}_hum_01")
    elif "living" in room_name or "living_room" in room_name:
        room.add_sensor("luminosity", sensor_id=f"{room_name}_light_01")
        room.add_sensor("temperature", sensor_id=f"{room_name}_temp_01")
    else:
        # fallback: one generic temperature sensor
        room.add_sensor("temperature", sensor_id=f"{room_name}_temp_01")
    return room


def run_demo(broker_host: str = "localhost", run_seconds: float = 60.0):
    """
    Run the integrated demo.

    - Creates a shared MQTT client
    - Creates RoomAgent instances for configured rooms
    - Starts averaging/detection/interface agents for each room/measurement
    - Demonstrates dynamic addition of a faulty sensor to generate alerts
    - Listens for control commands sent to home/{room}/control/*
    """

    logging.getLogger().setLevel(logging.INFO)
    mqtt = MQTTClient(broker_host=broker_host, client_id="sim_master")
    mqtt.start()
    LOG.info("Shared MQTT client started (broker=%s)", broker_host)

    # --- Rooms to create ---
    room_names: List[str] = ["bedroom1", "living_room"]

    # create room agents and populate with sensors
    rooms = {}
    for rn in room_names:
        rooms[rn] = _create_room(mqtt, rn)
        rooms[rn].start()

    # create averaging & detection & interface agents per room
    avg_agents = []
    detect_agents = []
    interface_agents = []
    for rn in room_names:
        # Temperature averaging & detection for each room
        avg_temp = AveragingAgent(mqtt, room=rn, measurement="temperature", window_size=20, publish_period=4.0)
        avg_hum = AveragingAgent(mqtt, room=rn, measurement="humidity", window_size=20, publish_period=6.0)
        avg_light = AveragingAgent(mqtt, room=rn, measurement="luminosity", window_size=20, publish_period=6.0)

        detect_temp = DetectionAgent(mqtt, room=rn, measurement="temperature", window_size=30)
        detect_hum = DetectionAgent(mqtt, room=rn, measurement="humidity", window_size=30)

        interface = InterfaceAgent(mqtt, room=rn)

        avg_agents.extend([avg_temp, avg_hum, avg_light])
        detect_agents.extend([detect_temp, detect_hum])
        interface_agents.append(interface)

    # Start dynamic events in background thread: remove a sensor, then add a bad sensor
    def dynamic_changes():
        # wait some time for system to stabilize
        time.sleep(12)
        LOG.info("Simulating sensor departure: removing %s_temp_02", "bedroom1")
        rooms["bedroom1"].remove_sensor("bedroom1_temp_02")
        time.sleep(8)
        LOG.info("Simulating faulty sensor: adding a high-baseline temperature sensor")
        rooms["bedroom1"].add_sensor("temperature", sensor_id="bedroom1_temp_bad", baseline=80.0, amplitude=0.0, noise=0.0, period=2.0)
        # simulate toggling heating after a while
        time.sleep(6)
        LOG.info("Simulating control command: turning heating ON in bedroom1 (simulated via RoomAgent API)")
        rooms["bedroom1"].set_heating(True)
        time.sleep(6)
        LOG.info("Simulating control command: opening window in bedroom1 (simulated via RoomAgent API)")
        rooms["bedroom1"].set_window(True)

    dyn_thread = threading.Thread(target=dynamic_changes, daemon=True)
    dyn_thread.start()

    try:
        # Let the demo run for run_seconds seconds
        elapsed = 0.0
        poll = 1.0
        while elapsed < run_seconds:
            time.sleep(poll)
            elapsed += poll
    except KeyboardInterrupt:
        LOG.info("Interrupted by user")
    finally:
        # Stop everything gracefully
        LOG.info("Stopping simulation: stopping sensors, rooms and MQTT client")
        for rn, room in rooms.items():
            try:
                room.stop()
            except Exception:
                LOG.exception("Error stopping room %s", rn)
        mqtt.stop()
        LOG.info("Simulation finished")


if __name__ == "__main__":
    # default run if called directly
    run_demo()
