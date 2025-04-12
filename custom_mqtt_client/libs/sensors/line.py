from datetime import datetime
from libs.base.sensor import Sensor


class Line(Sensor):
  NUM_OF_SENSORS = 8
  CALIBRATED_WHITE_LEVEL = 1000

  # Normalized values after calibration (black=0 - white=1000)
  values = [0] * NUM_OF_SENSORS
  update_count = 0
  sensor_time = datetime.now()
  sampling_time = 0


  def wait_for_data(self):
    super().wait_for_data('line')


  def _is_no_data(self):
    return self.update_count == 0


  def decode(self, topic, msg):
    parts = super().decode(topic, msg)

    # Line sensor with normalized values
    if topic == "T0/livn" and len(parts) >= 4:
      self._print_mqtt_debug(topic, msg)

      prev_time = self.sensor_time
      self.sensor_time = datetime.fromtimestamp(float(parts[0]))

      for i in range(self.NUM_OF_SENSORS):
        self.values[i] = int(parts[i+1])

      self.sampling_time = self._update_sampling_time(self.sensor_time, prev_time, self.update_count, self.sampling_time)
      self.update_count += 1

      return True

    return False





line_sensor = Line()