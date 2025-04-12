import os
import sys
import time
import signal

sys.path.append(os.path.abspath("../.."))

from libs.services.mqtt_service import mqtt_service
from libs.services.gpio_service import gpio
from libs.services.data_logger_service import data_logger_service
from modules.camera.camera_service import camera_service

from libs.logger import Logger

# Set up logging
main_logger = Logger('take_pictures')

# Allow graceful shutdown on Ctrl+C
signal.signal(signal.SIGINT, lambda sig, frame: (print('[!] Ctrl+C pressed! Shutting down...'), mqtt_service.terminate(), exit()))

def setup():
    main_logger.info("Setting up photo-taking services...")

    # Start only what you need
    mqtt_service.setup()  # No on_mqtt_message needed if not decoding any MQTT data
    gpio.setup()
    data_logger_service.setup()
    camera_service.setup(use_calibration=False)

    time.sleep(3)  # Let the camera warm up

    main_logger.info("Setup complete.")

def teardown():
    print("Tearing down services...")
    camera_service.terminate()
    mqtt_service.terminate()
    data_logger_service.terminate()
    print("Done.")

def take_photos():
    NUM_OF_PICTURES = 10
    print("Taking photos...")

    for i in range(NUM_OF_PICTURES):
        image_path = camera_service.take_photo()

        if image_path:
            print(f"Photo {i+1}/{NUM_OF_PICTURES} saved at: {image_path}")
        else:
            print("Failed to take photo")

        time.sleep(2)

if __name__ == "__main__":
    try:
        setup()
        take_photos()
    finally:
        teardown()
