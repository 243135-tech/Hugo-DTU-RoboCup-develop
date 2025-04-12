from datetime import datetime
import json
import os
import sys
import paho.mqtt.client as mqtt
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from collections import deque
import argparse
sys.path.append(os.path.abspath("../../"))
from modules.line_follower.line_detector import LineDetector
from libs.logger import Logger
line_detector = LineDetector(Logger('line_sensor_detector', 'logs', 'INFO'))


####################################################################################################


# Argument parser
parser = argparse.ArgumentParser(description="Line Sensor MQTT Client")
parser.add_argument('-s', '--save', action='store_true', help="Save the MQTT messages to a file")
args = parser.parse_args()


####################################################################################################

from scipy.interpolate import CubicSpline
from scipy.optimize import curve_fit

def weighted_average_peak(values):
    tot = np.sum(values)
    if tot == 0:
        return 0
    positions = np.arange(len(values))
    return np.sum(positions * values) / np.sum(values)

def quadratic_interpolation_peak(values):
    positions = np.arange(len(values))
    i_max = np.argmax(values)
    if 0 < i_max < len(values) - 1:
        x = positions[i_max - 1: i_max + 2]
        y = values[i_max - 1: i_max + 2]
        coeffs = np.polyfit(x, y, 2)
        return -coeffs[1] / (2 * coeffs[0])
    return i_max  # Return index if peak is at boundary


####################################################################################################




# MQTT Broker details
BROKER = "10.197.219.7"  # Change this
PORT = 1883
LINE_SENSORS_NUM = 8
TOPICS = [
    "robobot/drive/T0/livn"
]

# Data storage
window_size = 1000
line_values = deque(maxlen=window_size)
positions = deque(maxlen=window_size)
messages = []

# MQTT Callback
def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    if (args.save):
        timestamp = msg.timestamp if hasattr(msg, "timestamp") else None
        messages.append({"timestamp": timestamp, "payload": payload})

    parts = payload.split()
    sensor_values = [0] * LINE_SENSORS_NUM

    for i in range(LINE_SENSORS_NUM):
        sensor_values[i] = int(parts[i+1])
    
    if msg.topic in TOPICS:
        line_values.append(sensor_values)
        res = line_detector.detect(sensor_values)

        # Remove avg from sensor values
        # sensor_values = np.array(sensor_values) - np.mean(sensor_values)

        # weighted_avg_pos = weighted_average_peak(sensor_values) - 3.5
        # quadratic_interp_pos = quadratic_interpolation_peak(sensor_values) - 4.5
        
        # Choose one of the methods to use as the position
        pp = {
            'line_detector': res['position'],
            # 'weighted_avg_pos': weighted_avg_pos,
            # 'quadratic_interp_pos': quadratic_interp_pos,
        }

        positions.append(pp)



# Setup MQTT client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message
client.connect(BROKER, PORT, 60)
for topic in TOPICS:
    client.subscribe(topic)
client.loop_start()


fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 12))

def update(frame):
    ax1.clear()
    ax2.clear()
    
    if len(line_values) > 0:
        sensor_data = np.array(line_values)
        latest_values = sensor_data[-1]
        latest_positions = np.array(positions)
        
        # Plot sensor values
        ax1.bar(range(LINE_SENSORS_NUM), latest_values, tick_label=[f'Sensor {i+1}' for i in range(LINE_SENSORS_NUM)])
        ax1.set_ylim(0, 1000)
        ax1.set_xlabel("Sensor Position (mean subtracted)")
        ax1.set_ylabel("Sensor Values")
        ax1.set_title("Line Sensor Values")
        
        # Plot positions
        if len(latest_positions) > 0:
            # weighted_avg_positions = [pos['weighted_avg_pos'] for pos in latest_positions]
            # quadratic_interp_positions = [pos['quadratic_interp_pos'] for pos in latest_positions]
            line_detector_positions = [pos['line_detector'] for pos in latest_positions]

            # ax2.plot(weighted_avg_positions, range(len(weighted_avg_positions)), label='Weighted Average')
            # ax2.plot(quadratic_interp_positions, range(len(quadratic_interp_positions)), label='Quadratic Interpolation')
            ax2.plot(line_detector_positions, range(len(line_detector_positions)), label='Line Detector')

            ax2.set_xlim(-1.25, 1.25)
            ax2.set_xlabel("Position")
            ax2.set_ylabel("Time")
            ax2.set_title("Position Over Time")
            ax2.set_xticks(np.arange(-1, 1.1, 1/4))
            # ax2.legend()
            # ax2.legend(loc='center left')

            # Display latest positions as text annotations
            latest_position = latest_positions[-1]
            # ax2.text(0.05, 0.95, f'Weighted Avg: {latest_position["weighted_avg_pos"]:.2f}', transform=ax2.transAxes, fontsize=12, verticalalignment='top', horizontalalignment='left')
            # ax2.text(0.05, 0.90, f'Quadratic Interp: {latest_position["quadratic_interp_pos"]:.2f}', transform=ax2.transAxes, fontsize=12, verticalalignment='top', horizontalalignment='left')
            ax2.text(0.95, 0.95, f'Position: {latest_position["line_detector"]:.2f}', transform=ax2.transAxes, fontsize=12, verticalalignment='top', horizontalalignment='right')
            is_still_valid = line_detector.is_line_still_valid()
            ax2.text(0.95, 0.90, f'Valid: {'YES' if is_still_valid else 'NO'}', transform=ax2.transAxes, fontsize=12, verticalalignment='top', horizontalalignment='right')


ani = animation.FuncAnimation(fig, update, interval=100)
plt.show()

client.loop_stop()

# Save the bag to file
if (args.save):
    with open('line_sensor_bag.json', "w") as f:
        json.dump(messages, f)
    print(f"[+] Saved mqtt bag")