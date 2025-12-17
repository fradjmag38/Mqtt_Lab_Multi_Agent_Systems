#!/usr/bin/env python3
"""
Simple CLI script to publish control commands to a RoomAgent via MQTT.

Usage examples:
    # turn heating on in bedroom1
    python publish_control.py --room bedroom1 --command heating --value true

    # open window in living_room
    python publish_control.py --room living_room --command window --value true

    # add a sensor dynamically
    python publish_control.py --room bedroom1 --command add_sensor --measurement temperature --sensor_id bedroom1_temp_03 --baseline 22.0

    # remove a sensor
    python publish_control.py --room bedroom1 --command remove_sensor --sensor_id bedroom1_temp_03
"""

import argparse
import json
import logging
import sys
from mqtt_client import MQTTClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
LOG = logging.getLogger("publish_control")


def parse_bool(value: str):
    if value.lower() in ("1", "true", "yes", "on"):
        return True
    if value.lower() in ("0", "false", "no", "off"):
        return False
    raise ValueError(f"Invalid boolean string: {value}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--broker", default="localhost", help="MQTT broker host")
    parser.add_argument("--room", required=True, help="Room name (e.g. bedroom1)")
    parser.add_argument("--command", required=True, choices=("heating", "window", "add_sensor", "remove_sensor"))
    parser.add_argument("--value", help="Boolean value for heating/window (true/false)")
    parser.add_argument("--measurement", help="Measurement for add_sensor (temperature/humidity/...)")
    parser.add_argument("--sensor_id", help="Sensor id for add/remove sensor")
    parser.add_argument("--baseline", type=float, help="Baseline value for add_sensor (optional)")
    parser.add_argument("--period", type=float, help="Period for add_sensor (optional)")
    parser.add_argument("--amplitude", type=float, help="Amplitude for add_sensor (optional)")
    parser.add_argument("--noise", type=float, help="Noise for add_sensor (optional)")
    args = parser.parse_args()

    mqtt = MQTTClient(broker_host=args.broker, client_id="control_sender")
    mqtt.start()
    topic = f"home/{args.room}/control/command"
    payload = {"command": args.command}

    if args.command in ("heating", "window"):
        if args.value is None:
            LOG.error("Command heating/window requires --value true|false")
            sys.exit(1)
        payload["value"] = parse_bool(args.value)
    elif args.command == "add_sensor":
        if not args.measurement or not args.sensor_id:
            LOG.error("add_sensor requires --measurement and --sensor_id")
            sys.exit(1)
        payload["measurement"] = args.measurement
        payload["sensor_id"] = args.sensor_id
        # optional overrides
        for k in ("baseline", "period", "amplitude", "noise"):
            v = getattr(args, k)
            if v is not None:
                payload[k] = v
    elif args.command == "remove_sensor":
        if not args.sensor_id:
            LOG.error("remove_sensor requires --sensor_id")
            sys.exit(1)
        payload["sensor_id"] = args.sensor_id

    LOG.info("Publishing control payload to %s: %s", topic, payload)
    mqtt.publish(topic, payload)
    # short wait to ensure broker receives message, then exit
    import time
    time.sleep(0.5)
    mqtt.stop()


if __name__ == "__main__":
    main()
