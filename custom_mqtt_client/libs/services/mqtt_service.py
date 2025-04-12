
import time
from paho.mqtt import client as mqtt_client
from datetime import datetime
from threading import Thread
from libs.args import arg_parser
from libs.robot import robot
from libs.logger import Logger


class MqttService:
  SLEEP_WAIT_SEC = 0.1
  PRINT_CYCLES = 0.5/SLEEP_WAIT_SEC

  port = 1883
  topic = "robobot/drive/"
  cmd_topic = "robobot/cmd/" # send to Teensy T0, T1, or teensy_interface
  connected = False
  start_time = datetime.now()
  stopped = False
  recv_msg_counter = 0
  sent_msg_counter = 0
  failed_msg_counter = 0
  terminating = False
  is_confirmed_master = False
  is_not_master = False
  host = 'localhost'


  def setup(self, on_custom_message = None, mqtt_host = 'localhost'):
    self.logger = Logger('mqtt_service')
    self.logger.info("Starting service...")

    self.on_custom_message = on_custom_message
    self.host = mqtt_host
    self.connect_mqtt()

    # start listening to incomming
    self.mqtt_thread = Thread(target=self.handle_mqtt)
    self.mqtt_thread.start()

    # Wait for connection to be established
    self.__wait_for_data()

    # Do the setup and check of data streams, enable/disable interface logging (into teensy_interface/build/log_2025...)
    self.send("robobot/cmd/ti/log", "0")

    self.logger.info(f"Setup finished, connected = {self.connected}")


  def __wait_for_data(self):
    # Wait for data
    loops = 0
    while not self.connected:
      time.sleep(self.SLEEP_WAIT_SEC)

      if loops % self.PRINT_CYCLES == 0:
        self.logger.error(f"No data received after {loops*self.SLEEP_WAIT_SEC:.2f}s (continues...)")
      loops += 1

  
  def connect_mqtt(self):
    self.client = mqtt_client.Client()
    self.client.on_connect = self.on_connect

    try:
      self.client.connect(self.host, self.port)
    except:
      self.logger.error(f"Failed to connect to {self.host} on {self.port}. Won't work without MQTT connection, terminating...")
      raise Exception("Failed to connect to MQTT server")


  def handle_mqtt(self):
    self.client.subscribe(self.topic + "#")
    self.client.on_message = self.on_message

    while not self.stopped:
      self.client.loop()

    self.logger.error("Thread stopped")



  ##### EVENTS #####   

  def on_connect(self, client, userdata, flags, rc):
    if rc == 0:
      self.logger.info(f"Connected to MQTT Broker {self.host} on {self.port}")
      self.connected = True


  def on_message(self, client, userdata, msg):
    msg_decoded = msg.payload.decode()
    self.decode(msg.topic, msg_decoded)
    self.recv_msg_counter += 1



  ##### METHODS #####   

  def decode(self, topic, msg):
    if not topic.startswith(self.topic):
      return

    subtopic = topic[len(self.topic):]

    if subtopic == "T0/info" and arg_parser.get('print_teensy_info'):
      print(f"mqtt_service - Teensy info {msg}", end="")

    elif subtopic == "master":
      # skip timestamp to get real masters starttime
      real_master_time = msg[msg.find(" ")+1:]

      if str(self.start_time) == real_master_time:
        if not self.is_confirmed_master:
          self.logger.info(f"This mqtt client is the the only master for this robot {robot.robot_name.rstrip()}, good :)")
        self.is_confirmed_master = True
      else:
        self.is_not_master = True
        self.logger.error("This mqtt client is not the master, quitting!")

    elif self.on_custom_message is not None:
      self.logger.debug(f"Decoding custom MQTT message: topic={subtopic}, msg={msg.rstrip()}")
      self.on_custom_message(subtopic, msg)


  def send(self, topic, data):
    if not self.client:
      return

    if self.is_not_master:
      self.logger.error("Tried to send but I'm not master, terminating...")
      self.terminate()
      return False

    if len(data) == 0:
      data = " "

    res = self.client.publish(topic, data)
    is_success = res[0] == 0

    self.logger.debug(f"SENDING {topic} {data}")

    if is_success:
      self.sent_msg_counter += 1
      self.logger.debug(f"mqtt_service:: SENT")
      if self.sent_msg_counter > 100 and self.recv_msg_counter < 2:
        self.logger.error(f"Seems like there is no connection to Teensy (tx:{self.sent_msg_counter}, rx:{self.recv_msg_counter}); is Teensy_interface running?")
        self.stopped = True

    else:
      self.logger.error(f"failed to publish {topic} with {data}")
      self.failed_msg_counter += 1
      if self.failed_msg_counter > 10:
        self.logger.error("Lost contact to MQTT server - terminating")
        self.terminate()

    return is_success


  def send_cmd(self, topic, data = ""):
    return self.send(self.cmd_topic + topic, data)


  def terminate(self):
    # Skip if termination process is already in progress
    if self.terminating:
      return

    self.logger.info("Shutting down")

    if self.connected and not self.is_not_master:
      self.send_cmd("T0/stop")
      self.send_cmd("T0/leds", "14 0 0 0") # Turn off led 14
      time.sleep(0.01)

      self.send_cmd("T0/leds", "15 0 0 0")
      self.send_cmd("T0/leds", "16 0 0 0")
      time.sleep(0.01)

      # Stop interface logging
      self.send("robobot/cmd/ti/log", "0")

    self.terminating = True
    self.stopped = True

    # Wait for the thread to finish
    try:
      self.mqtt_thread.join()
    except:
      pass
   


# create the service object
mqtt_service = MqttService()