from time import time
import numpy as np
from libs.sensors.line import line_sensor


class LineDetector:
  LINE_CROSSING_THRESHOLD = 800  # average above this is assumed to be crossing line
  LINE_VALID_THRESHOLD = 700      # 1000 is calibrated white
  MIN_MAX_DELTA_THRESHOLD = 200   # if the difference between min and max is below this, we assume we're not on a line
  MAX_TIME_LINE_LOST = 1          # seconds


  position = 0
  last_valid_timestamp = time()


  def __init__(self, logger):
    self.logger = logger


  def reset(self):
    self.position = 0
    self.last_valid_timestamp = time()


  def time_passed_since_last_valid(self):
    return time() - self.last_valid_timestamp


  def is_line_still_valid(self):
    return self.time_passed_since_last_valid() < self.MAX_TIME_LINE_LOST
  

  def activated_sensors(self, sensor_values=None):
    if sensor_values is None:
      sensor_values = line_sensor.values
    active_sensors = [1 if val >= self.LINE_CROSSING_THRESHOLD else 0 for val in sensor_values]
    return active_sensors


  def detect(self, sensor_values=None):
    if sensor_values is None:
      sensor_values = line_sensor.values


    avg_val = np.mean(sensor_values)

    # Count the number of sensors that exceed the threshold
    #active_sensors = np.sum(sensor_values >= self.LINE_CROSSING_THRESHOLD)

    # Detect if more than 2 sensors are activated
    #is_crossing_line = active_sensors > 2

    # Update active sensor vector (1 if sensor is above threshold, 0 otherwise)
    active_sensors = self.activated_sensors()


    # Detect if we have a crossing line
    is_crossing_line = avg_val >= self.LINE_CROSSING_THRESHOLD
    # Is line valid (highest value above threshold)
    is_line_valid = np.max(sensor_values) >= self.LINE_VALID_THRESHOLD
    # Useful to check wether the value chart has a peak or not (no peak = no line or we're just on a white floor)
    min_max_delta = np.abs(np.max(sensor_values) - np.min(sensor_values))    

    if min_max_delta > self.MIN_MAX_DELTA_THRESHOLD:
      # Weighted sum of the positions (by the sensor values)
      sum = 0
      pos_sum = 0
      for i in range(line_sensor.NUM_OF_SENSORS):
        v = sensor_values[i] - avg_val
        if v > 0:
          sum += v
          pos_sum += (i + 1) * v  # do i+1, otherwise we get 0*sensor_values[i] = 0

      # pos_sum/sum is the weighted mean of the indices of the sensors (1..8), weighted by the sensor values
      # subtracting (1+line_sensor.NUM_OF_SENSORS)/2 gives us the position relative to the middle sensor, (min+max)/2
      if sum > 0 and is_line_valid:
        position = pos_sum / sum - (1+line_sensor.NUM_OF_SENSORS) / 2
      else:
        position = np.NAN

      # Normalize position to +-1
      position = position / (line_sensor.NUM_OF_SENSORS / 2)

    else:
      position = np.NAN

    # sum = 0
    # pos_sum = 0
    # for i in range(line_sensor.NUM_OF_SENSORS):
    #   v = sensor_values[i]
    #   if v > 0:
    #     sum += v
    #     pos_sum += (i + 1) * v  # do i+1, otherwise we get 0*sensor_values[i] = 0
    
    # # pos_sum/sum is the weighted mean of the indices of the sensors (1..8), weighted by the sensor values
    # # subtracting (1+line_sensor.NUM_OF_SENSORS)/2 gives us the position relative to the middle sensor, (min+max)/2
    # if sum > 0 and is_line_valid:
    #   position = pos_sum / sum - (1+line_sensor.NUM_OF_SENSORS) / 2
    # else:
    #   position = 0



    if is_line_valid:
        self.position = position
        self.last_valid_timestamp = time()

    #self.logger.debug(f"is_crossing_line={is_crossing_line}, is_line_valid={is_line_valid}, position={position}, avg_sensor_values={avg_val}, max_sensor_values={np.max(sensor_values)}")

    return { 'is_crossing_line': is_crossing_line, 'is_line_valid': is_line_valid, 'position': self.position, 'active_sensors': active_sensors}


  def is_intersection_detected(self):
    """
      Detects an intersection if:
    - the center sensors (3, 4) are off
    - at least one sensor on the left (0, 1, 2) is active
    - at least one sensor on the right (5, 6, 7) is active    
    """
    sensors = self.activated_sensors()
    if len(sensors) < 8:
        return False  

    # central sensors
    center_off = sensors[3] == 0 or sensors[4] == 0

    # At least one right and one left sensor
    left_on = any(sensors[i] == 1 for i in range(0, 2))
    right_on = any(sensors[i] == 1 for i in range(5, 7))

    return center_off and left_on and right_on

  def is_90_intersection_detected(self):
    """
   Detects a 90-degree intersection if:
    - The center sensors (index 3 and 4) are active (the straight continuous line)
    - And all sensors on the left side (indexes 0, 1, 2) or all sensors on the right side (indexes 5, 6, 7) are active,
    indicating the presence of a line branching out at 90 degrees.
    """
    sensors = self.activated_sensors()
    if len(sensors) < 8:
        return False


    # Verifica se tutti i sensori a sinistra sono attivi
    left_all = all(sensors[i] == 1 for i in range(0, 2))
    # Verifica se tutti i sensori a destra sono attivi
    right_all = all(sensors[i] == 1 for i in range(5, 7))


    return (left_all or right_all)