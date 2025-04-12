import time
import gpiod
from libs.logger import Logger


class GPIOPin:
  def __init__(self, pin: int, line: gpiod.Line, logger):
    self.logger = logger

    self.line = line
    self.pin = pin
    if line is None:
      self.logger.error(f"GPIO pin {line} is not reserved")


  def set(self, value) -> None:
    if self.line is None:
      return

    if self.line.direction() != self.line.DIRECTION_OUTPUT:
      self.logger.error(f"GPIO pin {self.pin} is set as input, cannot set output value: {self.line.direction()} != {self.line.DIRECTION_OUTPUT}")
      return

    self.line.set_value(value)


  def get(self) -> bool:
    if self.line is None:
      return False

    if self.line.direction() != self.line.DIRECTION_INPUT:
      self.logger.error(f"GPIO pin {self.pin} is not an input pin")
      return False

    v = self.line.get_value()

    if (v):
      self.logger.info(f"Pin {self.pin} is pressed/high")
    return v



class GPIOService:
    START_BTN = 13
    STOP_BTN = 6

    INPUTS = [STOP_BTN, START_BTN, 12, 16, 19]
    OUTPUTS = [20, 21, 26]
    gpio_pins = INPUTS + OUTPUTS


    def setup(self):
        self.logger = Logger('gpio')

        self.logger.info("Starting...")
        self.chip = gpiod.Chip('gpiochip4')

        # Create array with gpio lines (gpio_lines[13] is gpio 13)
        self.gpio_lines: list[gpiod.Line] = [None] * (max(self.gpio_pins) + 1)
        for pin in self.gpio_pins:
            self.gpio_lines[pin] = self.chip.get_line(pin)

        # Try to reserve all pins (try max 3 times)
        gpio_reservation_success = False
        reservation_tries_counter = 0
        while not gpio_reservation_success or reservation_tries_counter > 3:
          try: 
            # reserve all used pins
            for pin in self.gpio_pins:
                if self.gpio_lines[pin] is not None:
                    if pin in self.INPUTS:
                        self.gpio_lines[pin].request(consumer="robobot", type=gpiod.LINE_REQ_DIR_IN, flags=gpiod.LINE_REQ_FLAG_BIAS_PULL_DOWN)
                    elif pin in self.OUTPUTS:
                        self.gpio_lines[pin].request(consumer="robobot", type=gpiod.LINE_REQ_DIR_OUT)

            gpio_reservation_success = True
            reservation_tries_counter += 1
            time.sleep(0.05)

          except:
            self.logger.error("GPIO request for some pins failed");

        # Check result
        if not gpio_reservation_success:
          self.logger.error("GPIO pin reservation failed - another app is running already?")

          for line in self.gpio_lines:
            if line is not None:
              line.release()
        else:
          self.logger.info("GPIO pins successfully reserved")


    def is_start_pressed(self):
      v = self.gpio_lines[self.START_BTN].get_value()
      if (v):
        self.logger.info(f"MISSION STARTED - Button/pin {self.START_BTN} has been pressed")
      return v


    def is_stop_pressed(self):
      v = self.gpio_lines[self.STOP_BTN].get_value()
      if (v):
        self.logger.info(f"MISSION STOPPED - Button/pin {self.STOP_BTN} has been pressed")
      return v

    
    def pin(self, pin) -> GPIOPin:
      line = self.gpio_lines[pin]
      return GPIOPin(pin, line, self.logger)



# create the data object
gpio = GPIOService()