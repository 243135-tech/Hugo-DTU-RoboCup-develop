from datetime import datetime
import numpy as np
from datetime import datetime
from libs.base.sensor import Sensor
from libs.services.mqtt_service import mqtt_service


class Odometry(Sensor):
  # Motor velocities [left (rad/sec), right (rad/sec)]
  motor_velocities = [0.0, 0.0] # in radians/sec
  motor_velocity_time = datetime.now()
  motor_velocity_update_counter = 0
  motor_velocity_sampling_time = 1000 # sec

  # Wheel velocities [left (m/sec), right (m/sec)]
  wheel_velocities = [0.0, 0.0] # in m/sec - if gearing and wheel radius is correct
  wheel_velocity_time = datetime.now()
  wheel_velocity_update_counter = 0
  wheel_velocity_sampling_time = 1000 # sec

  # Pose [x (m), y (m), heading (rad), tilt (rad - if available)]
  pose = [0.0, 0.0, 0.0, 0.0]
  pose_time = datetime.now()
  pose_update_counter = 0
  pose_sampling_time = 1000 # sec

  # Total trip data
  total_dist = 0
  total_heading = 0
  total_time = datetime.now()

  # Partial trip data (can be reset to track parts of the track)
  trip_dist = 0
  trip_heading = 0
  trip_time = datetime.now()

  # Teensy configuration
  info_time = datetime.now()
  info_update_counter = 0
  tick_per_revolution = 68
  wheel_radius_left = 0.1
  wheel_radius_right = 0.1
  gear = 19
  wheel_base = 0.1
  encoder_reversed = False


  def wait_for_data(self):
    super().wait_for_data('odometry')

    # Reset pose
    mqtt_service.send_cmd("T0/enc0", "")
    # Send robot configuration: radius_left (m), radius_right (m), gear, encoder_tick, wheel_base (m)
    mqtt_service.send_cmd("T0/confw" ,"0.075 0.075 19 68 0.23")
    # Set encoder reversed
    mqtt_service.send_cmd("T0/encrev", "1")
    # Request new configuration from Teensy
    mqtt_service.send_cmd("T0/confi", "")


  def _is_no_data(self):
    return self.wheel_velocity_update_counter == 0 or self.motor_velocity_update_counter == 0 or self.pose_update_counter == 0


  def decode(self, topic, msg):
    parts = super().decode(topic, msg)

    if topic == "T0/vel" and len(parts) > 3:
      self._print_mqtt_debug(topic, msg)
      prev_time = self.wheel_velocity_time

      # Teensy time (parts[1]) is ignored
      self.wheel_velocity_time = datetime.fromtimestamp(float(parts[0]))
      self.wheel_velocities[0] = float(parts[2])
      self.wheel_velocities[1] = float(parts[3])

      self.wheel_velocity_sampling_time = self._update_sampling_time(self.wheel_velocity_time, prev_time, self.wheel_velocity_update_counter, self.wheel_velocity_sampling_time)
      self.wheel_velocity_update_counter += 1

      ds = (self.wheel_velocities[0] + self.wheel_velocities[1]) * self.wheel_velocity_sampling_time/2
      self.total_dist += ds
      self.trip_dist += ds

    elif topic == "T0/mvel" and len(parts) > 2:
      self._print_mqtt_debug(topic, msg)
      prev_time = self.motor_velocity_time

      self.motor_velocity_time = datetime.fromtimestamp(float(parts[0]))
      self.motor_velocities[0] = float(parts[1])
      self.motor_velocities[1] = float(parts[2])

      self.motor_velocity_sampling_time = self._update_sampling_time(self.motor_velocity_time, prev_time, self.motor_velocity_update_counter, self.motor_velocity_sampling_time)
      self.motor_velocity_update_counter += 1

    elif topic == "T0/pose" and len(parts) > 5:
      self._print_mqtt_debug(topic, msg)
      prev_time = self.pose_time

      # Teensy time (parts[1]) is ignored
      self.pose_time = datetime.fromtimestamp(float(parts[0]))
      self.pose[0] = float(parts[2])
      self.pose[1] = float(parts[3])

      # Calculate heading
      h = float(parts[4])
      dh = h - self.pose[2]
      # Saturate between +- 2pi
      if (dh > 2.0 * np.pi):
        dh -= 2.0 * np.pi
      elif (dh < -2.0 * np.pi):
        dh += 2.0 * np.pi
      self.trip_heading += dh
      self.total_heading += dh
      self.pose[2] = h
      # Tilt
      self.pose[3] = float(parts[5])

      self.pose_sampling_time = self._update_sampling_time(self.pose_time, prev_time, self.pose_update_counter, self.pose_sampling_time)
      self.pose_update_counter += 1

    elif topic == "T0/conf" and len(parts) > 7:
      self._print_mqtt_debug(topic, msg)
      self.info_time = datetime.fromtimestamp(float(parts[0]))
      self.wheel_radius_left = float(parts[1])
      self.wheel_radius_right = float(parts[2])
      self.gear = float(parts[3])
      self.tick_per_revolution = float(parts[4])
      self.wheel_base = float(parts[5])
      self.encoder_reversed = float(parts[7])
      self.info_update_counter += 1


  ####################################################################################################


  def reset_trip(self):
    self.trip_dist = 0
    self.trip_heading = 0
    self.trip_time = datetime.now()


  def total_time_passed(self):
    return (datetime.now() - self.total_time).total_seconds()


  def trip_time_passed(self):
    return (datetime.now() - self.trip_time).total_seconds()




odometry = Odometry()
