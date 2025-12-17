# SensorNetwork Examples

This folder contains runnable examples for the SensorNetwork exercise.

## Files

- `run_simulation.py` : entry point that calls `simulation.run_demo()`.
- `publish_control.py` : small CLI utility to publish control commands to rooms.

## Examples

Start the simulation:
python run_simulation.py

Send a control command (example: turn heating ON):

python publish_control.py --room bedroom1 --command heating --value true


Add a new temperature sensor dynamically:

python publish_control.py --room bedroom1 --command add_sensor --measurement temperature --sensor_id bedroom1_temp_03 --baseline 22.0


