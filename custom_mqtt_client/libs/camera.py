from typing import Callable
import cv2 as cv
from threading import Thread
import time as t
from libs.services.mqtt_service import mqtt_service
from libs.logger import Logger


class Camera:
  failed = False
  frame_count = 0
  cap = None
  last_frame = None

  def __init__(self, on_frame: Callable):
    self.logger = Logger('camera_service')
    print("[*] Starting camera...")
    self.cap = cv.VideoCapture(f'http://{mqtt_service.host}:7123/stream.mjpg')
    print("[+] Camera started")
    self.on_frame = on_frame

    if self.cap.isOpened():
      self.thread = Thread(target = self.__handle)
      self.thread.start()
      self.logger.info("camera_service thread started")
    else:
      self.logger.error("Camera failed to open")
      self.failed = True


  def __handle(self):
    while self.cap.isOpened() and not mqtt_service.stopped:
      res, self.last_frame = self.cap.read()

      if not self.cap.isOpened() or not res:
        self.logger.error("Failed receive frame (stream ended?). Exiting...")
        self.terminate()

      self.on_frame(self.last_frame)
      self.frame_count += 1


  def __del__(self):
    try:
      self.thread.join()
    except:
      pass

    if isinstance(self.cap, cv.VideoCapture):
      self.cap.release()

    cv.destroyAllWindows()
    self.logger.info("Camera service terminated")
