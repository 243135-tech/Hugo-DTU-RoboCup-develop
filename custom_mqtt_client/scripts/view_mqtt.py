import paho.mqtt.client as mqtt
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from collections import deque

# MQTT Broker details
BROKER = "10.197.219.7"  # Change this
PORT = 1883
TOPICS = [
    "robobot/drive/T0/pose",
    "robobot/drive/T0/vel"
]

# Data storage
window_size = 10000  # Adjust for smoother display
timestamps = deque(maxlen=window_size)
x_pos = deque(maxlen=window_size)
y_pos = deque(maxlen=window_size)
velocities = deque(maxlen=window_size)
heading = deque(maxlen=window_size)
tilt = deque(maxlen=window_size)

# MQTT Callback
def on_message(client, userdata, msg):
    global timestamps, x_pos, y_pos, velocities, heading, tilt
    parts = msg.payload.decode().split()
    
    if msg.topic == "robobot/drive/T0/pose":
        # Expected format: timestamp x y heading tilt other values
        timestamps.append(float(parts[0]))
        x_pos.append(float(parts[2]))
        y_pos.append(float(parts[3]))
        heading.append(float(parts[4]))  # Heading value
        tilt.append(float(parts[5]))  # Tilt value

    elif msg.topic == "robobot/drive/T0/vel":
        # Expected format: timestamp velocity other values
        velocities.append(float(parts[2]))


# Setup MQTT client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message
client.connect(BROKER, PORT, 60)
for topic in TOPICS:
    client.subscribe(topic)
client.loop_start()


# Plotting
fig, ax = plt.subplots(3, 1, figsize=(8, 10), gridspec_kw={'height_ratios': [3, 1, 1]})

def update(frame):
    ax[0].clear()
    ax[1].clear()
    ax[2].clear()

    # print(x_pos[-1], y_pos[-1], velocities[-1], heading[-1], tilt[-1])

    if len(x_pos) > 0 and len(y_pos) > 0:
        ax[0].plot(x_pos, y_pos, 'b-', label="Position (X,Y)")
        ax[0].set_xlabel("X Position")
        ax[0].set_ylabel("Y Position")
        ax[0].legend()
        ax[0].grid()

    if velocities:
        ax[1].plot(velocities, 'r-', label="Velocity")
        ax[1].set_xlabel("Time")
        ax[1].set_ylabel("Velocity")
        ax[1].legend()
        ax[1].grid()

    if heading and tilt:
        ax[2].plot(heading, 'g-', label="Heading",)
        ax[2].plot(tilt, 'y--', label="Tilt")
        ax[2].set_xlabel("Time")
        ax[2].set_ylabel("Angle (degrees)")
        ax[2].legend()
        ax[2].grid()

ani = animation.FuncAnimation(fig, update, interval=10, save_count=10000)
plt.show()

client.loop_stop()

