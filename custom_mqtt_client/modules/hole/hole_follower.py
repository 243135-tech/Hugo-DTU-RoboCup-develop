from statistics import median
from time import time
from libs.logger import Logger
from libs.services.mqtt_service import mqtt_service

class HoleFollower:

    KP = 1.5  # Proportional gain (tune as needed)
    KD = 0.0  # Derivative gain (if needed for a PD controller)
    gamma = 2.0
    
    def __init__(self):
        self.logger = Logger('hole_follower')
        self.last_error = 0.0  # For derivative control
        self.velocity = 0.0    # Forward speed of the robot
        self.turn_speed = 0.0  # Initial turn speed
        self.z_history = []    # Store last 10 z_mm positions

    def setup(self, camera_service):
        self.logger = Logger('hole_follower')
        self.set_hole_follower(0)
        self.camera_service = camera_service
        
        # Create log file
        self.log_data_file = open('logs/hole_follower.csv', 'w', encoding="utf-8")
        self.log_data_file.write("timestamp_sec,position,error,p,i,d,u\n")
        
        self.logger.info('Hole follower started')

    def stop(self):
        mqtt_service.send_cmd("ti/rc", f"{0} {0} {time()}")


    def follow_hole(self):
        self.calculate_turn_speed()
        mqtt_service.send_cmd("ti/rc", f"{self.velocity} {-self.turn_speed} {time()}")
        self.logger.info(f"Following hole: velocity={self.velocity}, turn_speed={-self.turn_speed}")

    def calculate_turn_speed(self):

        hole_detected = self.camera_service.hole['ok']
        hole_x = self.camera_service.hole['x']
        hole_z_mm = self.camera_service.hole['z_mm']

        print(f'Calculating turn speed x:{hole_x}; z_mm:{hole_z_mm}')

        if not hole_detected:
            print('Not detecting the hole')
            self.logger.info("No hole detected, rotating.")
            self.turn_speed = 0.05
            return
        
        # Update z_history with latest z_mm value
        self.z_history.append(hole_z_mm)
        if len(self.z_history) > 10:
            self.z_history.pop(0)

        # If we have 10 frames, use median to validate stability
        if len(self.z_history) == 10:
            z_median = median(self.z_history)
            if any(abs(z - z_median) > 10 for z in self.z_history):
                print("Z_mm values too inconsistent, skipping update.")
                return
            

        # Calculate turn speed normally if the hole is detected but not too close
        h, w = self.camera_service.last_frame.shape[:2]
        frame_center = w // 2
        error = (hole_x - frame_center) / frame_center  # Normalized error
        derivative = error - self.last_error

        #nonlinear_error = math.copysign(abs(error) ** self.gamma, error)
        self.turn_speed = self.KP * error + self.KD * derivative
        
        self.last_error = error  # Update for next derivative calculation
        

    def reset(self):
        self.velocity = 0.0
        self.turn_speed = 0.0
        self.last_error = 0.0
        self.KP = 1.5
        self.KD = 0.0
        self.gamma = 2.0
        self.z_history = []

    def set_hole_follower(self, velocity):
        if self.velocity == 0 and velocity != 0:
            self.reset()
        self.logger.info(f"SET vel={velocity}")
        self.velocity = velocity

hole_follower = HoleFollower()
