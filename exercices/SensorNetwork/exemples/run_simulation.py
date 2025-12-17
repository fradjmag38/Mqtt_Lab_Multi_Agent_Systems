#!/usr/bin/env python3
"""
Entry point for the SensorNetwork example.

Run this script to start the simulation. Ensure an MQTT broker is running on localhost.
"""

from simulation import run_demo  # noqa: E402 (module-level import after path)
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
if __name__ == "__main__":
    run_demo()
