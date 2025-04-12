from datetime import datetime
from libs.base.sensor import Sensor

import time

class Imu(Sensor):
  gyro = [0.0, 0.0, 0.0]
  gryo_update_counter = 0
  gyro_time = datetime.now()
  gyro_sampling_time = 1

  acc  = [0.0, 0.0, 0.0]
  acc_time = datetime.now()
  acc_update_counter = 0
  acc_sampling_time = 1

  ######################################################
  # CALIBRATION

  acc_scale_factor = [1.0, 1.0, 1.0]  # Scaling factors for each axis
  is_calibrated = False
  
  
  def calibrate_accelerometer(self, gravity_axis=2, samples=10, expected_gravity=9.81):
    """
    Calibrate the accelerometer using gravity as reference
    
    Parameters:
    - gravity_axis: which axis (0=x, 1=y, 2=z) is aligned with gravity
    - samples: number of readings to average
    - expected_gravity: the expected gravity value (typically 9.81 m/s²)
    """ 
    # Collect samples
    acc_sum = [0.0, 0.0, 0.0]
    for _ in range(samples):
      for i in range(3):
        acc_sum[i] += self.acc[i]
      time.sleep(0.01)  # Small delay between readings
    
    # Calculate averages
    acc_avg = [sum_val / samples for sum_val in acc_sum]
    
    # Calculate scaling factor for gravity axis
    self.acc_scale_factor[gravity_axis] = expected_gravity / abs(acc_avg[gravity_axis])
    
    self.is_calibrated = True
  
  ####################################################################

  def wait_for_data(self):
    super().wait_for_data('imu')
    self.calibrate_accelerometer()


  def _is_no_data(self):
    return self.gryo_update_counter == 0 or self.acc_update_counter == 0


  def decode(self, topic, msg):
    parts = super().decode(topic, msg)

    if topic == "T0/gyro" and len(parts) >= 4:
      self._print_mqtt_debug(topic, msg)

      prev_time = self.gyro_time
      self.gyro_time = datetime.fromtimestamp(float(parts[0]))
      self.gyro[0] = float(parts[1])
      self.gyro[1] = float(parts[2])
      self.gyro[2] = float(parts[3])

      self.gyro_sampling_time = self._update_sampling_time(self.gyro_time, prev_time, self.gryo_update_counter, self.gyro_sampling_time)
      self.gryo_update_counter += 1

    elif topic == "T0/acc" and len(parts) >= 4:
      self._print_mqtt_debug(topic, msg)

      prev_time = self.acc_time
      self.acc_time = datetime.fromtimestamp(float(parts[0]))
      self.acc[0] = float(parts[1]) * self.acc_scale_factor[0]
      self.acc[1] = float(parts[2]) * self.acc_scale_factor[1]
      self.acc[2] = float(parts[3]) * self.acc_scale_factor[2]
      #print(self.acc)

      self.acc_sampling_time = self._update_sampling_time(self.acc_time, prev_time, self.acc_update_counter, self.acc_sampling_time)
      self.acc_update_counter += 1



imu = Imu()

