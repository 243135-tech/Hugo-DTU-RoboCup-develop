from loguru import logger
from libs.args import arg_parser
import os



class Logger():
  LOG_DIR = "/home/local/custom_mqtt_client/logs/"
  LOG_LEVEL = arg_parser.get('log_level')
  FORMAT = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message}"

  __logger_initialized = False


  def __new__(cls, name, log_dir=None, log_level=None):
    if not cls.__logger_initialized:
      print("Logger:: Initialized for the first time")
      # Remove default stdout handler
      logger.remove()
      cls.__logger_initialized = True

    if log_dir is None:
      log_dir = cls.LOG_DIR
    if log_level is None:
      log_level = cls.LOG_LEVEL

    # Check if running on Raspberry Pi
    is_rpi = os.uname().machine.startswith("arm") or os.uname().machine.startswith("aarch64")
    if not is_rpi:
      print("Logger:: Non-Raspberry Pi environment detected")
      log_dir = os.path.join(os.path.dirname(__file__), "../../logs/")

    # Define the main log folder
    os.makedirs(log_dir, exist_ok=True)  # Ensure the directory exists
    
    # Set the log path
    log_path = os.path.join(log_dir, name + '.log')

    # This will clear the file
    with open(log_path, 'w'):
      pass

    def __make_filter(name):
      def filter(record):
        return record["extra"].get("name") == name
      return filter

    # logger.add(log_path, colorize=True, filter=__make_filter(name), rotation="500 MB")
    if cls.FORMAT is not None:
      logger.add(log_path, format=cls.FORMAT, level=log_level, filter=__make_filter(name), rotation="500 MB")
    else:
      logger.add(log_path, level=log_level, filter=__make_filter(name), rotation="500 MB")

    my_logger = logger.bind(name=name)
    my_logger.info("Logger started")
    return my_logger
