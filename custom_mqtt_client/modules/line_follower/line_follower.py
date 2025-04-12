from libs.logger import Logger
from libs.services.mqtt_service import mqtt_service
from time import time, sleep
import numpy as np
from modules.line_follower.line_detector import LineDetector
from modules.camera.camera_service import camera_service

class LineFollower1:
    # Control limits
    U_LIMIT = 5  # Slightly reduced to prevent oversteering
    
    # Default parameters
    LINE_KP = 2.5  # Proportional gain - slightly reduced to prevent oscillation
    LINE_KI = 0.035  # Integral gain - increased for better steady-state error elimination
    LINE_KD = 1.3   # Derivative gain - increased to dampen oscillations
    
    # Default speeds
    #BASE_SPEED = 0.4
    # tune the velocity through path.py
    MIN_SPEED = 0
    
    # Anti-windup limits
    MAX_INTEGRAL = 2.0

    
    def __init__(self):
        self.reset()
    
    def setup(self):
        self.logger = Logger('line_follower')
        # active sensors variable from line detector
        self.line_detector = LineDetector('logger')
        detect_results = self.line_detector.detect()
        self.active_sensors = detect_results['active_sensors']
        self.set_line_control(0)
        
        # Create log file
        self.log_data_file = open('logs/line_follower.csv', 'w', encoding="utf-8")
        self.log_data_file.write("timestamp_sec,position,error,p,i,d,u\n")
        
        self.logger.info('Line follower started')
        
    def terminate(self):
        self.set_line_control(0)
        mqtt_service.send_cmd("ti/rc", f"0 0 {time()}")
        if hasattr(self, 'log_data_file'):
            self.log_data_file.close()
        self.logger.info('Line follower terminated')
    
    def reset(self):
        self.position = 0
        self.position_ref = 0
        self.velocity = 0
        self.sampling_time = 0.1
        
        # PID controller reset
        self.error_old = 0
        self.integral = 0
        self.last_derivative = 0
        self.u = 0.0
        self.u_old = 0.0
        
        # Runtime tracking
        self.last_update_time = time()
        self.last_line_center_time = time()
        self.straight_line_time = 0
        
        # State flags
        self.is_line_valid = False
        self.is_crossing_line = False
        
    def is_line_still_valid(self):
        if self.line_detector:
            return self.line_detector.is_line_still_valid()
        return False
    
    def set_line_control(self, velocity, position_ref=0):
        # Reset PID when activating line follower
        if self.velocity == 0 and velocity != 0:
            self.reset()
        
        #self.logger.info(f"SET vel={velocity}, position_ref={position_ref}")
        self.velocity = velocity
        self.position_ref = position_ref
    
    def update(self):
        if not self.line_detector:
            return
        
        # Calculate actual sampling time
        current_time = time()
        real_dt = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # Update sampling time for calculations (constrained to reasonable values)
        if 0.001 <= real_dt <= 0.5:
            self.sampling_time = real_dt
        
        # Detect line position
        detect_results = self.line_detector.detect()
        position = detect_results['position']
        self.is_line_valid = detect_results['is_line_valid']
        self.is_crossing_line = detect_results['is_crossing_line']
        self.active_sensors = detect_results['active_sensors']
        
        # Keep last known position in case of no data
        if not np.isnan(position):
            self.position = position
        
        # Use to control, if active
        if self.velocity > 0:
            self.follow_line()
        
        # Log data
        if hasattr(self, 'log_data_file'):
            p_term = self.LINE_KP * (self.position_ref - self.position)
            i_term = self.LINE_KI * self.integral
            d_term = self.LINE_KD * self.last_derivative
            self.log_data_file.write(f"{current_time},{self.position},{self.position_ref - self.position},{p_term},{i_term},{d_term},{self.u}\n")
    
    def follow_line(self):
        # Calculate error (reference - actual position)
        error = self.position_ref - self.position
        
        # Calculate PID terms
        p_term = self.LINE_KP * error
        
        # Update integral with anti-windup
        self.integral += error * self.sampling_time
        if self.integral > self.MAX_INTEGRAL:
            self.integral = self.MAX_INTEGRAL
        elif self.integral < -self.MAX_INTEGRAL:
            self.integral = -self.MAX_INTEGRAL
        i_term = self.LINE_KI * self.integral
        
        # Calculate derivative with filtering
        derivative = (error - self.error_old) / self.sampling_time
        # Low-pass filter for derivative term (to reduce noise)
        alpha = 0.2  # Filter coefficient (0-1, lower means more filtering)
        filtered_derivative = alpha * derivative + (1 - alpha) * self.last_derivative
        self.last_derivative = filtered_derivative
        d_term = self.LINE_KD * filtered_derivative
        
        # Calculate total control signal
        self.u = p_term + i_term + d_term
        
        # Apply slew rate limiting to control signal
        max_change = 2.0 * self.sampling_time  # Maximum change per second
        if abs(self.u - self.u_old) > max_change:
            self.u = self.u_old + np.sign(self.u - self.u_old) * max_change
        
        # Limit control output
        self.u = max(min(self.u, self.U_LIMIT), -self.U_LIMIT)
        
        # Update stored values for next iteration
        self.error_old = error
        self.u_old = self.u
        
        # Adjust forward velocity based on line characteristics
        forward_velocity = self.calculate_adaptive_velocity()
        
        # Send command to robot
        mqtt_service.send_cmd("ti/rc", f"{forward_velocity} {self.u} {time()}")
        
        # Debug output
        #self.logger.debug(f"Position: {self.position:.3f}, Error: {error:.3f}, Control: {self.u:.3f}, Velocity: {forward_velocity:.3f}")
    
    def calculate_adaptive_velocity(self):
        # Reduce speed in curves, maintain higher speed on straight sections
        base_velocity = self.velocity
        
        # Ideal case: both central sensors (indexes 3 and 4) are active
        if self.active_sensors[3] == 1 and self.active_sensors[4] == 1:
            return min(base_velocity * 2.0, 0.5)  # Double speed, up to a maximum limit

        # Curve penalty: more peripheral sensors are active -> sharper curve -> slower speed
        weights = [3, 2, 1, 0, 0, 1, 2, 3]  # Higher weights for outer sensors
        curve_severity = sum([w for i, w in enumerate(weights) if self.active_sensors[i] == 1])

        # Normalize penalty: 6 is the maximum possible penalty (all outer sensors active)
        velocity_factor = max(0.1, 1.0 - curve_severity / 6.0)

        return base_velocity * velocity_factor
    
    def handle_intersection(self, direction=None):
        """
        Handle intersection when a crossing line is detected.
        """
        if direction is None:
            return
            
        if direction == 'left':
            # Stop the robot
            #mqtt_service.send_cmd("ti/rc", f"0 0 {time()}")
            
            turn_speed = 1.0 # Turn rate
            turn_duration = 0.8 # Estimated time for a little left turn
            mqtt_service.send_cmd("ti/rc", f"{0.1} {turn_speed} {time()}")
            start_time = time()
            while time() - start_time < turn_duration:
                # Ensure the robot turns for at least the specified duration
                pass
            
        
        elif direction == 'right':
            # Stop the robot
            #mqtt_service.send_cmd("ti/rc", f"0 0 {time()}")
            turn_speed = 1.0  # Turn rate
            turn_duration = 0.8 # Estimated time for a small right turn
            mqtt_service.send_cmd("ti/rc", f"{0.1} {-turn_speed} {time()}")
            start_time = time()
            while time() - start_time < turn_duration:
                # Ensure the robot turns for at least the specified duration
                pass
            

        elif direction == '90left':
            # Stop the robot
            mqtt_service.send_cmd("ti/rc", f"{-0.1} 0 {time()}")
            back_duration = 0.5
            start_time = time()
            while time() - start_time < back_duration:
                # Ensure the robot turns for at least the specified duration
                pass

            turn_speed = 1.4  # Turn rate
            turn_duration = 1.1  # Estimated time for a 90-degree turn
            mqtt_service.send_cmd("ti/rc", f"0 {turn_speed} {time()}")
            start_time = time()
            while time() - start_time < turn_duration:
                # Ensure the robot turns for at least the specified duration
                pass
            
        elif direction == '90right':
            # Stop the robot
            mqtt_service.send_cmd("ti/rc", f"{-0.1} 0 {time()}")
            back_duration = 0.5
            start_time = time()
            while time() - start_time < back_duration:
                # Ensure the robot turns for at least the specified duration
                pass
            
            # Perform a 90-degree right turn
            turn_speed = 1.4  # Turn rate
            turn_duration = 1.1  # Estimated time for a 90-degree turn
            mqtt_service.send_cmd("ti/rc", f"0 {-turn_speed} {time()}")
            start_time = time()
            while time() - start_time < turn_duration:
                pass

        elif direction == 'basket':
            # Stop the robot
            mqtt_service.send_cmd("ti/rc", f"{-0.1} 0 {time()}")
            back_duration = 0.5
            start_time = time()
            while time() - start_time < back_duration:
                # Ensure the robot turns for at least the specified duration
                pass
            
            # Perform a 90-degree right turn
            turn_speed = 1.4  # Turn rate
            turn_duration = 1.1  # Estimated time for a 90-degree turn
            mqtt_service.send_cmd("ti/rc", f"0 {-turn_speed} {time()}")
            start_time = time()
            while time() - start_time < turn_duration:
                pass

        elif direction == 'back':
            # going back
            mqtt_service.send_cmd("ti/rc", f"{-0.1} 0 {time()}")
            back_duration = 2.0
            start_time = time()
            while time() - start_time < back_duration:
                pass
   
        elif direction == '180':
            # Stop the robot
            #mqtt_service.send_cmd("ti/rc", f"0 0 {time()}")
            
            # Perform a 180-degree right turn
            turn_speed = 1.7  # Turn rate
            turn_duration = 1.8  # Estimated time for a 180-degree turn
            mqtt_service.send_cmd("ti/rc", f"0 {-turn_speed} {time()}")
            start_time = time()
            while time() - start_time < turn_duration:
                pass


        elif direction == 'axe':
            # Stop the robot
            mqtt_service.send_cmd("ti/rc", f"{-0.1} 0 {time()}")
            back_duration = 0.5
            start_time = time()
            while time() - start_time < back_duration:
                # Ensure the robot turns for at least the specified duration
                pass
            
            # Perform a 90-degree right turn
            turn_speed = 1.4  # Turn rate
            turn_duration = 1.1  # Estimated time for a 90-degree turn
            mqtt_service.send_cmd("ti/rc", f"0 {-turn_speed} {time()}")
            start_time = time()
            while time() - start_time < turn_duration:
                pass
        
        elif direction == 'search_ball':
            # Stop the robot
            mqtt_service.send_cmd("ti/rc", f"{-0.1} 0 {time()}")
            back_duration = 0.5
            start_time = time()
            while time() - start_time < back_duration:
                # Ensure the robot turns for at least the specified duration
                pass

            turn_speed = 1.3  # Turn rate
            turn_duration = 1.1  # Estimated time for a 90-degree turn
            mqtt_service.send_cmd("ti/rc", f"0 {turn_speed} {time()}")
            start_time = time()
            while time() - start_time < turn_duration:
                # Ensure the robot turns for at least the specified duration
                pass
            
        elif direction == 'approach_hole':
            # Stop the robot
            mqtt_service.send_cmd("ti/rc", f"0 0 {time()}")
            
            # Go straight for turn_duration seconds
            turn_speed = -0.03
            straight_duration = 2.9
            mqtt_service.send_cmd("ti/rc", f"{0.2} {turn_speed} {time()}")
            start_time = time()
            while time() - start_time < straight_duration:
                # Ensure the robot moves for at least the specified duration
                #print(time()-start_time)
                pass
            
        elif direction == 'wiggle':
            #WIGGLE
            turn_speed = 1.0 # Turn rate
            mqtt_service.send_cmd("ti/rc", f"{0.06} {0} {time()}")
            #start_time = time()
            #toggle = True
            while (camera_service.ball['is_ball_grabbed']):
                print('wiggling')
                # Wiggle direction
                #wiggle_turn = -turn_speed if toggle else turn_speed
                mqtt_service.send_cmd("ti/rc", f"{0.02} {turn_speed} {time()}")
                turn_speed = -turn_speed
                #toggle = not toggle
                sleep(0.7)

            # Finish wiggle with a compensatory rotation
            # If the last wiggle was right (turn_speed positive), rotate left
            #last_wiggle = -turn_speed if toggle else turn_speed
            #mqtt_service.send_cmd("ti/rc", f"0 {-last_wiggle} {time()}")
            #sleep(0.7)

            # Stop completely before returning to next logic (e.g., line search)
            #mqtt_service.send_cmd("ti/rc", f"0 0 {time()}")


        elif direction == 'turn_to_hole':
            # Stop the robot
            mqtt_service.send_cmd("ti/rc", f"0 0 {time()}")
            
            # Perform a 90-degree left turn
            turn_speed = 1.5  # Turn rate
            turn_duration = 1.5 # Estimated time for a 90-degree turn
            mqtt_service.send_cmd("ti/rc", f"0 {-turn_speed} {time()}")
            start_time = time()
            while time() - start_time < turn_duration:
                # Ensure the robot turns for at least the specified duration
                pass
        
        elif direction == 'back_to_line':
            # going back
            mqtt_service.send_cmd("ti/rc", f"{0.2} {0} {time()}")
            centered = False
            while not centered:
                if self.active_sensors[3] == 1 or self.active_sensors[4] == 1:
                    print('WE ARE ON THE LINE')
                    # If the line is detected, break the loop
                    centered = True
                    mqtt_service.send_cmd("ti/rc", f"0 0 {time()}")
                    #rotate a bit right
                    mqtt_service.send_cmd("ti/rc", f"0 {-0.2} {time()}")
                pass                
            

        elif direction == 'big_int':
            # for processing big intercection near the stop
            turn_speed = 1.5 # Turn rate
            turn_duration = 1.6 # Estimated time 
            mqtt_service.send_cmd("ti/rc", f"0 {turn_speed} {time()}")
            start_time = time()
            while time() - start_time < turn_duration:
                # Ensure the robot turns for at least the specified duration
                pass

            # straight to avoid all the lines 
            str_duration = 1.0
            mqtt_service.send_cmd("ti/rc", f"{0.15} {0} {time()}")
            start_time = time()
            while time() - start_time < str_duration:
                # Ensure the robot turns for at least the specified duration
                pass
        
        # Resume line following
        self.reset()
        self.set_line_control(self.velocity)

# Create the line follower instance
line_follower = LineFollower1()
