import math
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import patches
from datetime import datetime
from libs.logger import Logger
from libs.sensors.odometry import odometry
from libs.commands import ROBOT_set_movement



class PurePursuit:
    def __init__(self, k_pp = 0.5, lookahead_dist_range=(0.3, 1.5), max_turnrate=1, max_velocity=1, save_animation=False):
        self.LOOKAHEAD_DIST_RANGE = lookahead_dist_range  # (min, max)
        self.MAX_TURNRATE = max_turnrate
        self.MAX_VELOCITY = max_velocity
        self.SAVE_ANIMATION = save_animation
        self.K_PP = k_pp  # Pure Pursuit gain

        self.stop = False
        self.waypoints = self.read_waypoints()
        self.logger = Logger('pure_pursuit')

        self.v_prev_error = 0.0
        self.prev_time = datetime.now()
        self.sampling_time = 1000
        self.update_counter = 0
        self.curr_waypoint_index = 0

        package_path = os.path.dirname(os.path.abspath(__file__))
        self.ANIMATION_FIGURE_PATH = os.path.join(package_path, 'pure_pursuit_animation.png')
        self.animation_pose = []


    def reset(self):
        self.stop = False
        self.prev_time = datetime.now()
        self.sampling_time = 1000
        self.update_counter = 0
        self.animation_pose = []


    def read_waypoints(self):
        file_name = 'waypoints.csv'
        package_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(package_path, file_name)

        with open(file_path) as f:
            path_points = np.loadtxt(f, delimiter=',', skiprows=1)

        return path_points[:, :2]


    def _update_sampling_time(self):
        """
        Update sampling rate estimation
        """
        delta_t = (datetime.now() - self.prev_time).total_seconds()
        self.prev_time = datetime.now()

        if self.update_counter == 2:
            res = delta_t
        else:
            # Use exponential moving average to update delta_t
            res = (self.sampling_time * 99 + delta_t) / 100

        self.update_counter += 1
        return res

    
    def get_pose(self, key):
        pose = {
            # 'x': odometry.pose[0],
            # 'y': odometry.pose[1],
            'y': odometry.pose[0],
            'x': -odometry.pose[1],
            'heading': odometry.pose[2],
            'velocity': math.sqrt(odometry.wheel_velocities[0]**2 + odometry.wheel_velocities[1]**2),
        }

        return pose[key]


    def get_distance_to(self, x, y):
        dx = x - self.get_pose('x')
        dy = y - self.get_pose('y')
        return np.hypot(dx, dy)


    def get_target_waypoint2(self, lookahead):
        min_distance = float('inf')
        best_index = -1

        for i in range(self.curr_waypoint_index + 1, len(self.waypoints)):
            x_wp, y_wp = self.waypoints[i]
            distance = self.get_distance_to(x_wp, y_wp)

            if distance < min_distance:
                min_distance = distance
                best_index = i

        if best_index != -1:
            self.current_index = best_index  # update current_index
            x_wp, y_wp = self.waypoints[best_index]
            return True, [x_wp, y_wp]

        return False, [0, 0]
    

    def get_target_waypoint(self, lookahead):
        x, y = self.get_pose('x'), self.get_pose('y')

        # Search through segments of the self.waypoints
        for i in range(len(self.waypoints) - 1):
            p1 = np.array(self.waypoints[i])
            p2 = np.array(self.waypoints[i + 1])
            d = p2 - p1

            # Coefficients for quadratic intersection
            f = p1 - np.array([x, y])
            a = np.dot(d, d)
            b = 2 * np.dot(f, d)
            c = np.dot(f, f) - lookahead**2

            discriminant = b**2 - 4*a*c

            if discriminant < 0:
                continue  # No intersection

            sqrt_discriminant = np.sqrt(discriminant)
            t1 = (-b + sqrt_discriminant) / (2 * a)
            t2 = (-b - sqrt_discriminant) / (2 * a)

            for t in [t1, t2]:
                if 0 <= t <= 1:
                    intersection = p1 + t * d
                    return True, intersection  # Found TP

        return False, [0,0]  # No valid target point found

    
    def __saturate(self, val, limit):
        if val > limit:
            return limit
        elif val < -limit:
            return -limit
        else:
            return val


    def is_stopping_condition(self, lookahead):
        #  (nearest_idx == len(self.waypoints)-1 and lookahead < 0.2) or (lookahead > 2):
        # Check if the robot is close to the last waypoint
        # return self.waypoints[-1, 0] - self.get_pose('x') < lookahead and self.waypoints[-1, 1] - self.get_pose('y') < lookahead
        return self.get_distance_to(self.waypoints[-1, 0], self.waypoints[-1, 1]) < lookahead



    def pure_pursuit(self):
        self.sampling_time = self._update_sampling_time()
        epsilon = 0.00001  # to avoid division by zero

        # Set the lookahead distance depending on the speed
        lookahead = np.clip(self.K_PP * self.get_pose('velocity'), self.LOOKAHEAD_DIST_RANGE[0], self.LOOKAHEAD_DIST_RANGE[1]) 

        # ok, target_x, target_y, _, velocity, nearest_idx = self.get_target_waypoint(lookahead)
        velocity = 0.2
        ok, intersection = self.get_target_waypoint2(lookahead)

        if not ok:
            return velocity, 0
        
        # Calculate the delta between the target point and the current position
        target_x, target_y = intersection[0], intersection[1]
        x_delta = target_x - self.get_pose('x')
        y_delta = target_y - self.get_pose('y')
        alpha = np.arctan(y_delta / (x_delta + epsilon)) - self.get_pose('heading')

        #print(f'PurePursuit:: delta = ({x_delta},{y_delta}), alpha = {alpha}')

        # front of the vehicle is 0 degrees right +90 and left -90 hence we need to convert our alpha
        if alpha > np.pi / 2:
            alpha -= np.pi
        if alpha < -np.pi / 2:
            alpha += np.pi

        # Calculate steering angle
        steering_angle = np.arctan((2 * odometry.wheel_base * np.sin(alpha)) / (lookahead + epsilon))
        # Set max wheel turning angle
        # steering_angle = -self.__saturate(steering_angle, 0.5)
        steering_angle = -steering_angle

        # Convert steering angle to turn rate
        turnrate = self.get_pose('velocity') * np.tan(steering_angle) / odometry.wheel_base

        # print(f"PurePursuit:: theta = {np.rad2deg(steering_angle):.3f}°, turnrate = {turnrate:.3f}, current_vel = {self.get_pose('velocity'):.3f}, dt = {self.sampling_time:.3f}, lookahead = {lookahead:.3f}")

        # Limit the turn rate and velocity
        turnrate = self.__saturate(turnrate, self.MAX_TURNRATE)
        velocity = self.__saturate(velocity, self.MAX_VELOCITY)

        # Plot map progression
        if self.SAVE_ANIMATION:
            plt.cla()
            self.animation_pose.append([self.get_pose('x'), self.get_pose('y')])

            cx = self.waypoints[:, 0]
            cy = self.waypoints[:, 1]
            plt.plot(cx, cy, "-r", label = "course")

            x_vals, y_vals = zip(*self.animation_pose)  # Unpack into x and y values
            plt.plot(x_vals, y_vals, "-b", label="trajectory")
            # TODO plot circle of radius lookahead distance

            plt.plot(target_x, target_y, "xg", label = "target", markersize=10, markeredgewidth=3)

            circle = patches.Circle((self.get_pose('x'), self.get_pose('y')), lookahead, color='g', fill=False, linestyle='--', label="lookahead")
            plt.gca().add_patch(circle)

            plt.axis("equal")
            plt.grid(True)
            plt.legend()
            plt.title("Pure Pursuit Control" + str(1))
            plt.savefig(self.ANIMATION_FIGURE_PATH)
            plt.pause(0.001)

        if self.is_stopping_condition(lookahead):
            self.stop = True
            return 0, 0
        

        return velocity, turnrate



    def handle(self):
        if self.stop:
            self.logger.info("STOPPED")
            return

        velocity, turnrate = self.pure_pursuit()
        self.logger.debug(f"OUTPUT: velocity = {velocity:.3f}, turnrate = {turnrate:.3f}")
        ROBOT_set_movement(velocity, turnrate)
