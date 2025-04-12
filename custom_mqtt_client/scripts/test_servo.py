from time import sleep
import paho.mqtt.client as mqtt
import os
import sys
from collections import deque
# sys.path.append(os.path.abspath(".."))
# from libs.commands import *
# from libs.services.mqtt_service import mqtt_service


# MQTT Broker details
BROKER = "10.197.219.7"  # Change this
PORT = 1883
TOPICS = [
    "robobot/drive/T0/pose",
    "robobot/drive/T0/vel"
]

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(BROKER, PORT, 60)
# client.loop_start()

# mqtt_service.setup(BROKER)
# SERVO_set(1, 0)

servo_num = 1

##############################
angle_deg = -15
# angle_deg = 90
##############################

if angle_deg > 90:
    angle_deg = 90
elif angle_deg < -90:
    angle_deg = -90

ang_min = -90
ang_max = 90
out_min = 800
out_max = -900
position = out_min + (angle_deg - ang_min) * (out_max - out_min) / (ang_max - ang_min)

velocity = 200
client.publish("robobot/cmd/T0/servo", f"{servo_num} {position} {velocity}")

sleep(2)
client.publish("robobot/cmd/T0/servo", f"{servo_num} {-900} {velocity}")
sleep(1)
client.publish("robobot/cmd/T0/servo", f"{servo_num} {9999} {velocity}")

