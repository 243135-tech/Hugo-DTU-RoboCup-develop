import math
from time import time
from libs.logger import Logger
from libs.services.mqtt_service import mqtt_service
from modules.camera.camera_service import CameraService
from threading import Thread


class GolfBallFollower:
    KP = 1.5  # Proportional gain (tune as needed)
    KD = 0.0  # Derivative gain (if needed for a PD controller)
    gamma = 2.0
    last_error = 0.0  # For derivative control
    velocity = 0.3  # Forward speed of the robot
    turn_speed = 0.0  # Initial turn speed
    counter = 0
    
    def __init__(self, camera_service):
        self.logger = Logger('golf_ball_follower')
        self.camera_service = CameraService
        self.ball = {'ok': False, 'x': 0, 'y': 0, 'z': 0, 'radius': 0, 'z_mm': 0}
        self.setup_done = False
        self.thread = Thread(target=self.run)
        self.thread.start()

    def run(self):
        self.calculate_turn_speed()
        mqtt_service.send_cmd("ti/rc", f"{self.velocity} {self.turn_speed} {time()}")
        self.logger.info(f"Following ball: velocity={self.velocity}, turn_speed={self.turn_speed}")

         
        

    def calculate_turn_speed(self):
        ball_detected = self.camera_service.ball['ok']
        ball_x = self.camera_service.ball['x']
        ball_z_mm = self.camera_service.ball['z_mm']
        if not ball_detected:
            self.logger.info("No ball detected, stopping rotation.")
            self.turn_speed = 0.0
            return
        
        # Stop the robot if the ball is too close
        if ball_z_mm < 200:
            self.logger.info(f"Ball is too close (z_mm={ball_z_mm}), stopping robot.")
            self.velocity = 0.0
            self.turn_speed = 0.0
            return
        
        h,w = self.camera_service.last_frame.shape[:2]
        frame_center = w // 2
        error = (ball_x - frame_center) / frame_center  # Normalized error
        derivative = error - self.last_error

        nonlinear_error = math.copysign(abs(error) ** self.gamma, error)
        self.turn_speed = self.KP * nonlinear_error + self.KD * derivative

        self.last_error = error  # Update for next derivative calculation

        
    def terminate(self):
        self.thread.join()
    
    def reset(self):
        self.velocity = 0.0
        self.turn_speed = 0.0
        self.last_error = 0.0
        self.KP = 2.0
        self.KD = 0.0
        self.gamma = 2.0

    def set_ball_follower(self, velocity):
        self.logger = Logger('ball_follower')
        if self.velocity == 0 and velocity != 0:
            self.reset_follower()

        self.logger.info(f"SET vel={velocity}")
        self.velocity = velocity


golf_ball_follower = GolfBallFollower()