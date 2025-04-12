from abc import ABC, abstractmethod
import time
from libs.services.mqtt_service import mqtt_service
from libs.logger import Logger


class Sensor(ABC):
  SLEEP_WAIT_SEC = 0.01
  PRINT_CYCLES = 0.5/SLEEP_WAIT_SEC


  def wait_for_data(self, name):
    self.logger = Logger(name)
    self.logger.info('Starting...')
    self.__wait_for_data()
    self.logger.info("Initiated")


  def __wait_for_data(self):
    # Wait for data
    loops = 0
    while not mqtt_service.stopped and self._is_no_data():
      time.sleep(self.SLEEP_WAIT_SEC)

      if loops % self.PRINT_CYCLES == 0:
        self.logger.error(f"No data received after {loops*self.SLEEP_WAIT_SEC:.2f}s (continues...)")
      loops += 1

  
  def _update_sampling_time(self, curr_time, prev_time, update_counter, prev_sampling_time):
    """
    Update sampling rate estimation
    """
    delta_t = (curr_time - prev_time).total_seconds()
    if update_counter == 2:
      return delta_t
    else:
      # Use exponential moving average to update delta_t
      return (prev_sampling_time * 99 + delta_t) / 100


  def _print_mqtt_debug(self, topic, msg):
    try:
      self.logger.debug(f"Decoding MQTT message: topic={topic}, msg={msg.rstrip()}")
    except:
      pass


  @abstractmethod
  def _is_no_data(self):
    """
    Should return true when no data has been received
    """
    pass


  @abstractmethod
  def decode(self, topic, msg):
    """
    Handle the reception of mqtt messages
    """
    return msg.split(" ")