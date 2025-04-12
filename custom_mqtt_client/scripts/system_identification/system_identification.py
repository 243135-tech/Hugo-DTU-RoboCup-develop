from time import time, sleep
import paho.mqtt.client as mqtt
import sys
import os
from collections import deque
# Add the directories to the Python path
sys.path.append(os.path.abspath("../custom_mqtt_client"))
# Import LineDetector and Logger
from modules.line_follower.line_detector import LineDetector
from libs.logger import Logger
line_detector = LineDetector(Logger('line_sensor_detector', 'logs', 'INFO'))
import matplotlib.pyplot as plt



# MQTT Broker details
BROKER = "10.197.219.7"  # Change this
PORT = 1883
LINE_SENSORS_NUM = 8
TOPICS = [
    "robobot/drive/T0/livn"
]


forward_velocity = 0.1
turnrate = 0

f = open("sys_id_data.txt", "w")


positions = deque(maxlen=10000)

# MQTT Callback
def on_message(client, userdata, msg):
    parts = msg.payload.decode().split()
    sensor_values = [0] * LINE_SENSORS_NUM

    for i in range(LINE_SENSORS_NUM):
        sensor_values[i] = int(parts[i+1])
    
    if msg.topic in TOPICS:
        res = line_detector.detect(sensor_values)
        positions.append((time(), turnrate, res['position']))
        f.write(f"{time()} {turnrate} {res['position']}\n")


# Setup MQTT client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message
client.connect(BROKER, PORT, 60)
for topic in TOPICS:
    client.subscribe(topic)
client.loop_start()


def send_cmd():
    client.publish("robobot/cmd/ti/rc", f"{forward_velocity} {turnrate} {time()}")


sleep(1)
turnrate = 0.1
send_cmd()
sleep(1)
turnrate = 0
forward_velocity = 0
send_cmd()
