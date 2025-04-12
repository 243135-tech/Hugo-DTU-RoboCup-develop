from setproctitle import setproctitle
import signal
import os
import glob
from modules.line_follower.line_follower import line_follower
from libs.services.gpio_service import gpio
from libs.services.mqtt_service import mqtt_service
from libs.args import arg_parser
from libs.services.data_logger_service import data_logger_service
from libs.robot import robot
from libs.commands import *
from libs.state_machine import StateMachine
from libs.sensors.imu import imu
from libs.sensors.odometry import odometry
from libs.sensors.ir import ir
from libs.sensors.line import line_sensor
from libs.sensors.motor import motor
from modules.path.path import Path
from libs.logger import Logger
from modules.camera.camera_service import camera_service
from modules.golf_ball.golf_ball_follower import golf_ball_follower
from modules.hole.hole_follower import hole_follower


# Set title of process, so that it is not just called Python
setproctitle("my-mqtt-client")


def clean_log_folder():
  # List all files in the folder (excluding directories)
  files = glob.glob(os.path.join(Logger.LOG_DIR, "*"))
  # Loop through the files and remove them
  for file in files:
    try:
      if os.path.isfile(file):
        os.remove(file)
    except Exception as e:
        print(f"Error deleting {file}: {e}")


clean_log_folder()
main_logger = Logger('main')


############################################################


def on_mqtt_message(topic, msg):
  imu.decode(topic, msg)
  odometry.decode(topic, msg)
  ir.decode(topic, msg)
  robot.decode(topic, msg)
  motor.decode(topic, msg)
  if line_sensor.decode(topic, msg):
    line_follower.update()


def setup():
  main_logger.info("Starting")

  line_follower.setup()
  # Set location of MQTT data server
  mqtt_service.setup(on_mqtt_message)
  ROBOT_stop_movement()

  # Allow close down on ctrl-C
  signal.signal(signal.SIGINT, lambda sig, frame: (print('[!] You pressed Ctrl+C! Shutting down...'), mqtt_service.terminate(), ROBOT_stop_movement(), exit()))

  # Services
  main_logger.info("Setting up services...")
  data_logger_service.setup()
  gpio.setup()
  camera_service.setup()
  main_logger.info("Services done!")

  # Sensors
  main_logger.info("Setting up sensors...")
  ir.wait_for_data()
  odometry.wait_for_data()
  imu.wait_for_data() 
  motor.wait_for_data()
  line_sensor.wait_for_data()
  main_logger.info("Sensors done!")

  # Modules
  main_logger.info("Setting up modules...")
  golf_ball_follower.setup(camera_service)
  #hole_follower.setup(camera_service)
  main_logger.info("Modules done!")

  main_logger.info("Everything was successfully setup")
  LED_mission_restarting()

  if not arg_parser.get('now'):
    main_logger.info("Ready, press start button")
    LED_mission_waiting()



############################################################


def teardown():
  main_logger.error("NOOOOOOOOO, I'm stopping :(")
  LED_mission_off()
  gpio.pin(20).set(0) # ??

  ROBOT_stop_movement() # Stop moving

  mqtt_service.terminate()
  data_logger_service.terminate()
  line_follower.terminate()
  camera_service.terminate()

  main_logger.info("TERMINATED, now I'm dead, good job >:(")


############################################################


if __name__ == "__main__":
  try:
    setup()
    print('[+] Setup finished\n')

    path = Path()
    sm = StateMachine(path.handle_path)

    if mqtt_service.connected:
      sm.loop()
      teardown()

  except Exception as e:
    print(f"[!] ERROR {e}")
    mqtt_service.terminate()
    ROBOT_stop_movement() 
    LED_blink(LED_MISSION, 255, 0, 0, 0.1, 5)

    main_logger.error(f"ERROR! {e}")
    main_logger.error("Main Terminated (should not happen, unless robot is shut down)")

    raise

  main_logger.error("Main Terminated (should not happen, unless robot is shut down)")