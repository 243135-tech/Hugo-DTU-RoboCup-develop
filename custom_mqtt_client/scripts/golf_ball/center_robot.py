from time import time, sleep
from libs.logger import Logger
from libs.services.mqtt_service import mqtt_service
import numpy as np

def center_robot(camera_service):
    
    ball_x = camera_service.ball['x']
    ball_z = camera_service.ball['z']

    if camera_service.ball['ok']: # If a golf ball is detected 

        if not _is_aligned(ball_x) and ball_z != 0: # If it is not in the center of the camera
          
            # Calculate turn angle using arcsin(ball_x / ball_z)
            turn_angle_rad = np.arcsin(ball_x / ball_z)
            turn_angle_deg = np.degrees(turn_angle_rad)
            
            # Convert angle to turn value since turning 90 degrees is equal to turn rate of 0.8
            turn = turn_angle_deg * 0.8 / 90
            
            # Send command to the robot (velocity = 0 for pure turning)
            velocity = 0  # No forward motion, just alignment
            mqtt_service.send_cmd("ti/rc", f"{velocity} {turn} {time()}")

            camera_service.aligned = True

def _is_aligned(ball_x):
    return abs(ball_x < 5)
