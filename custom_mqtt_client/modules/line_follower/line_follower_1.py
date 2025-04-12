from libs.logger import Logger
from libs.services.mqtt_service import mqtt_service
from time import time
from modules.line_follower.line_detector import LineDetector
from libs.sensors.line import line_sensor
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import math
from libs.sensors.motor import motor


def ROBOT_set_motors_voltage(left: float, right: float):
    """
    Sets the raw motor voltages
    """
    success = mqtt_service.send_cmd("T0/motv", f"{left} {right}")
    if success:
        print("MQTT command sent successfully.")
    else:
        print("Failed to send MQTT command!")


# ------------------------------------------------------------------

# PARAMETERS 
LINE_KP = 0.5
tauP = 0.0 #time constant of the system pole (filtering/stabilizing effect)
tauZ = 1.0 #the time constant of the zero of the system (anticipatory effect)
sampleTime = 0.1
U_LIMIT = 10
line_detector = None

# ------------------------------------------------------------------

class LineFollower:

  def __init__(self):
    self.logger = Logger('line_follower')
    self.line_detector = None
    self.sampling_time = 0.01
    self.position = 0
    self.velocity = 0
    self.position_ref = 0

    self.LINE_KP = 1.3
    self.ALPHA = 0.4
    self.TAU_Z = 1
    self.TAU_P = self.TAU_Z * self.ALPHA

    self.filtered_derivative = 0
    self.tauP2pT = 1.0
    self.tauP2mT = 0.0
    self.tauZ2pT = 1.0
    self.tauZ2mT = 0.0

    self.scaled_error_old = 0.0
    self.error_old = 0
    self.u_old = 0.0
    self.u = 0.0
    self.integral = 0


  def reset(self):
    self.set_line_control(0)
    self.position = 0
    self.velocity = 0
    self.sampling_time = 0.1
    if self.line_detector is not None:
      self.line_detector.reset()
    self.scaled_error_old = 0.0 
    self.u_old = 0.0            
    self.u = 0.0                
    self.tauP2pT = tauP*2.0 + sampleTime
    self.tauP2mT = tauP*2.0 - sampleTime
    self.tauZ2pT = tauZ * 2.0 + sampleTime
    self.tauZ2mT = tauZ * 2.0 - sampleTime
    self.position_ref = 0


  def setup(self):
    self.logger = Logger('line_follower')
    self.line_detector = LineDetector(self.logger)
    
    self.set_line_control(0)

    self.log_data_file = open('logs/line_follower.csv', 'w', encoding="utf-8")
    self.log_data_file.write("timestamp_sec,position,error,i,d,u\n")

    self.logger.info('Started')



  def is_line_still_valid(self):
    if self.line_detector:
      return self.line_detector.is_line_still_valid()
    return False

  def update(self):
    #if not self.line_detector:
    #  return 

    detect_results = self.line_detector.detect()
    position = detect_results['position']
    self.is_line_valid = detect_results['is_line_valid']
    self.is_crossing_line = detect_results['is_crossing_line']

    # Keep last known position is case of no data
    if not np.isnan(position):
      self.position = position

    # Use to control, if active
    if self.velocity > 0:
      mqtt_service.send_cmd("ti/rc", f"{self.velocity} 0 {time()}")
      self.follow_line()


  def set_line_control(self, velocity, position_ref=0):
    # Reset PID when activating line follower
    if self.velocity == 0 and velocity != 0:
      self.reset()

    self.logger.info(f"SET vel={velocity}, position_ref={position_ref}")
    self.velocity = velocity
    #ROBOT_set_motors_voltage(self.velocity, self.velocity)
    self.position_ref = position_ref

  def modified_error(self,e):
    return math.copysign(math.sqrt(abs(e)), e)

  def calculate_adaptive_velocity(self):
    # Reduce speed in curves, maintain higher speed on straight sections
    base_velocity = self.BASE_SPEED
        
    # Is the robot approximately centered on the line?
    is_centered = abs(self.position) < 0.2
        
    # Track time spent on straight sections
    if is_centered:
        if time() - self.last_line_center_time > 1.0:
            # We've been centered for a while, can gradually increase speed
            self.straight_line_time += self.sampling_time
            # Increase speed up to 150% of base speed for straight lines
            straight_bonus = min(0.5, self.straight_line_time / 10.0)  # Max 50% bonus after 10 seconds
            base_velocity *= (1.0 + straight_bonus)
    else:
        self.last_line_center_time = time()
        self.straight_line_time = 0
        
    # Reduce speed based on control effort (more steering = lower speed)
    turn_factor = abs(self.u) / self.U_LIMIT
    velocity = base_velocity * (1.0 - 0.7 * turn_factor**2)  # Quadratic reduction
        
    # Ensure minimum velocity
    return max(self.MIN_SPEED, velocity)

  
  def follow_line(self):
      if abs(line_sensor.sampling_time - self.sampling_time) > 2.0:  # ms
        self.PID_calculate()
        self.sampling_time = line_sensor.sampling_time

      error = self.position_ref - self.position
      self.scaled_error = self.LINE_KP * error

      self.u = (self.scaled_error * self.tauZ2pT - self.scaled_error_old * self.tauZ2mT + self.u_old * self.tauP2mT) / self.tauP2pT

      # Adjust velocity: keep moving forward when sensors 4-5 are active
      detect_results = self.line_detector.detect()
      active_sensors = detect_results['active_sensors']
      print(f'Active sensors: {active_sensors}')
      print(f'Error: {error}')
   
      if self.u > self.U_LIMIT:
        self.u = self.U_LIMIT
      elif self.u < -self.U_LIMIT:
        self.u = -self.U_LIMIT
      print(f'self.u: {self.u}')
      # Save old values
      self.scaled_error_old = self.scaled_error
      self.u_old = self.u

      # Adjust forward velocity based on line characteristics
      forward_velocity = self.calculate_adaptive_velocity()
        
      # Send command to robot
      mqtt_service.send_cmd("ti/rc", f"{forward_velocity} {self.u} {time()}")
        

      #ROBOT_set_motors_voltage(self.velocity - self.u, self.velocity + self.u);
      #lv,rv = motor.get_voltages()
      #print(f'voltages: {lv},{rv}')
      #avgv = (lv + rv)/2;
      #ROBOT_set_motors_voltage(avgv - self.u, avgv + self.u);



line_follower = LineFollower()
