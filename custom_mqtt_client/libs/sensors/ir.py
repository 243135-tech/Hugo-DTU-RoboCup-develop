from datetime import datetime
from typing import Literal
from libs.base.sensor import Sensor


class IrSensor(Sensor):
  ir = [0.0, 0.0]
  ir_update_counter = 0
  ir_time = datetime.now()
  ir_sampling_time = 0
  OBJECT_DETECTION_THRESHOLD = 0.3  #actually 27 cm


  def wait_for_data(self):
    super().wait_for_data('ir')


  def _is_no_data(self):
    return self.ir_update_counter == 0


  def is_object_detected_in_front(self):
    """
    Returns True if an object is detected in front
    """
    return self.ir[1] < self.OBJECT_DETECTION_THRESHOLD


  def is_object_detected_on_side(self):
    """
    Returns True if an object is detected on the side
    """
    return self.ir[0] < self.OBJECT_DETECTION_THRESHOLD


  def decode(self, topic, msg):
    parts = super().decode(topic, msg)

    if topic == "T0/ird" and len(parts) >= 3:
      self._print_mqtt_debug(topic, msg)

      prev_time = self.ir_time
      self.ir_time = datetime.fromtimestamp(float(parts[0]))
      self.ir[0] = float(parts[1])
      self.ir[1] = float(parts[2])

      self.ir_sampling_time = self._update_sampling_time(self.ir_time, prev_time, self.ir_update_counter, self.ir_sampling_time)
      self.ir_update_counter += 1


ir = IrSensor()

