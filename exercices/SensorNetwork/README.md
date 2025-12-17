# SensorNetwork - Smart Home Simulation

This exercise implements a small smart-home sensor network using MQTT and modular agents.

## Overview

Components:
- `mqtt_client.py` : lightweight MQTT wrapper (JSON serialization, background loop).
- `agents/` : agent implementations:
  - `room_agent.py` : RoomAgent that manages sensors and actuators (heating/window).
  - `sensor_factory.py` : Factory producing `SensorAgent` instances.
  - `averaging_agent.py` : computes rolling averages per room/measurement.
  - `detection_agent.py` : detects anomalies and publishes alerts.
  - `interface_agent.py` : simple console UI listening to averages and alerts.
- `simulation.py` : integrated simulation that creates RoomAgent instances automatically and runs averaging/detection/interface agents.
- `exemples/` : example entry points and control scripts.

## Topics & Payloads

- Sensor readings:
  - Topic: `home/{room}/{measurement}/{sensor_id}`
  - Payload (JSON): `{"timestamp": <int>, "sensor_id": "<id>", "value": <float>}`

- Averages:
  - Topic: `home/{room}/{measurement}/average`
  - Payload: `{"timestamp": <int>, "room": "<room>", "measurement": "<measurement>", "room_average": <float>, "per_sensor": {...}}`

- Alerts:
  - Topic: `home/alerts/{room}`
  - Payload: alert JSON with context (value, mean, stddev, etc.)

- Control commands:
  - Topic: `home/{room}/control/command` (RoomAgent subscribes to `home/{room}/control/#`)
  - Examples:
    - `{"command": "heating", "value": true}`
    - `{"command": "window", "value": true}`
    - `{"command": "add_sensor", "measurement": "temperature", "sensor_id": "bedroom1_temp_03", "baseline": 22.0}`
    - `{"command": "remove_sensor", "sensor_id": "bedroom1_temp_03"}`

## How to run

1. Ensure MQTT broker is running (default: localhost,shiftr.io).

2. Run the integrated simulation:
cd exercices/SensorNetwork
use the convenience runner:
python exemples/run_simulation.py

3. To send control commands from another terminal:

python exemples/publish_control.py --room bedroom1 --command heating --value true

## Notes

- The simulation shares a single MQTT client instance for efficiency.
- RoomAgent applies actuator effects to sensor baselines (heating/window) to model environment changes.
- For more realistic runs, start agents in separate processes or containers to better emulate networked devices.


