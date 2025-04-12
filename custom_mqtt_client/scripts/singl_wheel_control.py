import time
from paho.mqtt import client as mqtt_client

# MQTT Broker settings
BROKER = 'localhost'  # Change if needed
PORT = 1883
CMD_TOPIC = "robobot/cmd/ti/rc"  # Your existing control topic

# Initialize MQTT Client
client = mqtt_client.Client()
client.connect(BROKER, PORT)

def send_wheel_command(velocity, turn_rate):
    """ Sends a command to control the wheels using velocity and turn rate. """
    timestamp = time.time()
    command = f"{velocity} {turn_rate} {timestamp}"
    client.publish(CMD_TOPIC, command)
    print(f"Sent: {command}")

def control_single_wheel(left_wheel_speed, right_wheel_speed):
    """ Converts left & right wheel speeds into velocity and turn rate. """
    velocity = (left_wheel_speed + right_wheel_speed) / 2
    print(velocity)
    turn_rate = (right_wheel_speed - left_wheel_speed) / 2
    print(turn_rate)
    send_wheel_command(velocity, turn_rate)

# Example: Simulate moving ONLY the left wheel (right wheel stays still)
control_single_wheel(0.5, 0)  # moving only the left wheel
time.sleep(2)
control_single_wheel(0, 0)  # Stop
