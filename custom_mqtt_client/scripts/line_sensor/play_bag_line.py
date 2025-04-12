import paho.mqtt.client as mqtt
import json
import time

LOG_FILE = "line_sensor_bag.json"
TOPIC = "robobot/drive/T0/livn"

with open(LOG_FILE, "r") as f:
    messages = json.load(f)

BROKER = "localhost"
client = mqtt.Client()
client.connect(BROKER)

previous_timestamp = None

for msg in messages:
    payload = msg["payload"]
    timestamp = msg["timestamp"]

    if previous_timestamp is not None:
        delta_t = timestamp - previous_timestamp
        time.sleep(delta_t)

    client.publish(TOPIC, payload)
    print(f"Replayed: {payload}")
    previous_timestamp = timestamp

client.disconnect()