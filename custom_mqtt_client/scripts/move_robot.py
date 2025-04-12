import time
from paho.mqtt import client as mqtt_client

# MQTT Broker settings
BROKER = 'localhost'  # Change to your MQTT broker IP if not running locally
PORT = 1883
CMD_TOPIC = "robobot/cmd/ti/rc"  # Topic for controlling the robot wheels

# Initialize MQTT Client
client = mqtt_client.Client()
client.connect(BROKER, PORT)

def send_wheel_command(velocity, turn_rate):
    """ Sends a command to control the wheels. """
    timestamp = time.time()
    command = f"{velocity} {turn_rate} {timestamp}"
    client.publish(CMD_TOPIC, command)
    print(f"Sent: {command}")

# Example usage:
send_wheel_command(0, 0.8)  # Turn 90 degrees on the right
time.sleep(2)  # Wait for 2 seconds
send_wheel_command(0, 0)  # Stop the robot


