from datetime import datetime


class Robot:
  hbt_time = datetime.now()
  sampling_time = 30.0
  update_counter = 0
  robot_name = "unknown"


  def __update_sampling_time(self, prev_time):
    """
    Update sampling rate estimation
    """
    delta_t = (self.hbt_time - prev_time).total_seconds()
    if self.update_counter == 2:
      self.sampling_time = delta_t
    else:
      # Use exponential moving average to update delta_t
      self.sampling_time = (self.sampling_time * 99 + delta_t) / 100


  def decode(self, topic, msg):
    parts = msg.split(" ")

    if topic == "T0/hbt" and len(parts) >= 4:
      prev_time = self.hbt_time
      self.hbt_time = datetime.fromtimestamp(float(parts[0]))

      self.__update_sampling_time(prev_time)
      self.update_counter += 1

    elif topic == "T0/dname":
      if len(parts) >= 2:
        self.robot_name = parts[1]


robot = Robot()

