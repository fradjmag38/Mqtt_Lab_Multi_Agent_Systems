"""
First MQTT client example.

This script demonstrates a minimal MQTT client using the Eclipse Paho library.
The client:
    - connects to a local MQTT broker,
    - subscribes to a topic,
    - publishes several messages with delays,
    - prints all received messages to the console.

This file is used to validate the MQTT setup and basic publish/subscribe
mechanisms.
"""

import time
import paho.mqtt.client as mqtt


BROKER_HOST = "localhost"
BROKER_PORT = 1883
TOPIC = "hello"

def on_connect(client: mqtt.Client, userdata, flags, rc: int) -> None:
    """
    Callback executed when the client successfully connects to the MQTT broker.

    Args:
        client (mqtt.Client): The MQTT client instance.
        userdata: User-defined data (not used here).
        flags: Response flags sent by the broker.
        rc (int): Connection result code (0 means success).

    This function subscribes to the target topic once the connection is
    established.
    """
    print(f"Connected to broker with result code {rc}")
    client.subscribe(TOPIC)


def on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage) -> None:
    """
    Callback executed when a message is received on a subscribed topic.

    Args:
        client (mqtt.Client): The MQTT client instance.
        userdata: User-defined data (not used here).
        msg (mqtt.MQTTMessage): The received MQTT message.

    The payload is decoded from bytes to string before being displayed
    """
    payload = msg.payload.decode()
    print(f"Received message on topic '{msg.topic}': {payload}")

# Create the MQTT client instance
client = mqtt.Client()

# Register callback functions
client.on_connect = on_connect
client.on_message = on_message

# Connect to the local MQTT broker
client.connect(BROKER_HOST, BROKER_PORT)

# Start the MQTT network loop in a background thread
client.loop_start()


# Publish several messages with a delay between each publish
for i in range(5):
    message = f"Hello MQTT {i}"
    print(f"Publishing message: {message}")
    client.publish(TOPIC, message)
    time.sleep(1)

# Allow some time to receive messages before shutting down
time.sleep(2)

client.loop_stop()
client.disconnect()
