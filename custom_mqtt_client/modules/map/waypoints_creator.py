from datetime import datetime
from time import time
import math
from libs.logger import Logger
from libs.sensors.odometry import odometry


class WaypointsCreator:
  WRITE_DT_TIME = 0.5 # seconds

  def __init__(self):
    self.logger = Logger('waypoint_creator')
    self.last_write_time = datetime.now()

    try:
      self.file = open('modules/map/waypoints.csv', 'w', encoding="utf-8")
      self.logger.info("Waypoints file opened")
    except:
      self.logger.error("Failed to open file for writing")

    self.file.write("x,y,heading,velocity")


  def handle(self, state = None):
    delta_t = (datetime.now() - self.last_write_time).total_seconds()
    if delta_t < self.WRITE_DT_TIME:
      return

    self.last_write_time = datetime.now()

    self.logger.debug("Writing data to file")

    velocity = math.sqrt(odometry.wheel_velocities[0]**2 + odometry.wheel_velocities[1]**2),
    self.file.write(f"{odometry.pose[0]:.3f},{odometry.pose[1]:.3f},{odometry.pose[2]:.3f},{velocity}")
    self.file.flush()


  def __del__(self):
    self.file.close()
    self.logger.info("Waypoints file closed")

