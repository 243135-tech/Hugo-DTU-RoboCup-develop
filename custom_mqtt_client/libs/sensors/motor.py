from datetime import datetime
from libs.base.sensor import Sensor


class Motor(Sensor):
  data = [0.0, 0.0, 0.0, 0.0, 0.0]
  update_counter = 0
  time= datetime.now()
  sampling_time = 0


  def wait_for_data(self):
    super().wait_for_data('mot')


  def _is_no_data(self):
    return self.update_counter == 0


  def decode(self, topic, msg):
    parts = super().decode(topic, msg)

    if topic == "T0/mot" and len(parts) >= 6:
      self._print_mqtt_debug(topic, msg)

      prev_time = self.time
      self.time= datetime.fromtimestamp(float(parts[0]))
      self.data[0] = float(parts[1])
      self.data[1] = float(parts[2])
      self.data[2] = float(parts[3])
      self.data[3] = float(parts[4])
      self.data[4] = float(parts[5])

      self.sampling_time = self._update_sampling_time(self.time, prev_time, self.update_counter, self.sampling_time)
      self.update_counter += 1

  
  def get_voltages(self):
    return (self.data[0], self.data[1])


motor = Motor()

