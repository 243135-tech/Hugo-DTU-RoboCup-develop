from libs.logger import Logger
from time import time
from libs.sensors.imu import imu
from libs.sensors.ir import ir
from libs.sensors.odometry import odometry
from modules.line_follower.line_follower import line_follower


class DataLoggerService:
  """
  Creates a csv file useful for debugging and data analysis.
  """

  COMMENT_SIMBOL = "#"
  state = 0


  def setup(self):
    self.logger = Logger('data_logger')

    try:
      self.file = open('logs/data_log.csv', 'w', encoding="utf-8")
      self.logger.info("Data logger file opened")
    except:
      self.logger.error("Failed to open file for writing")

    self.file.write("timestamp_sec, state, x, y, heading_rad, gyro_x, gyro_y, gyro_z, acc_x, acc_y, acc_z, ir0, ir1, line_pos, total_dist, total_heading, trip_dist, trip_heading\n")


  def write_comment(self, data):
    self.file.write(f"{self.COMMENT_SIMBOL} [INFO] {time()} {data}\n")


  def write(self, state = None):
    if state is not None:
      self.state = state

    self.logger.debug("Writing data to file")

    # Timestamp and state  
    self.file.write(f"{time()},{self.state},")
    # Pose (x, y, h)
    self.file.write(f"{odometry.pose[0]:.3f},{odometry.pose[1]:.3f},{odometry.pose[2]:.3f},")
    # Gyro data
    self.file.write(f"{imu.gyro[0]:.3f},{imu.gyro[1]:.3f},{imu.gyro[2]:.3f},")
    # Accelerometer data
    self.file.write(f"{imu.acc[0]:.3f},{imu.acc[1]:.3f},{imu.acc[2]:.3f},")
    # IR sensor data
    self.file.write(f"{ir.ir[0]:.3f},{ir.ir[1]:.3f},")
    # Line sensor detected position
    self.file.write(f"{line_follower.position:.2f},")
    # Trip A distance and heading change
    self.file.write(f"{odometry.total_dist:.3f},{odometry.total_heading:.3f},")
    # Trip B distance and heading change
    self.file.write(f"{odometry.trip_dist:.4f},{odometry.trip_heading:.4f}\n")

    self.file.flush()


  def terminate(self):
    self.file.close()
    self.logger.info("Data logger file closed")



data_logger_service = DataLoggerService()