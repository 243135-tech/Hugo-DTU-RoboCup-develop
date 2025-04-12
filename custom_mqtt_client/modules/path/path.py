from enum import auto
import numpy as np
import math
from time import sleep
from matplotlib.pylab import Enum
from modules.map.waypoints_creator import WaypointsCreator
from modules.map.pure_pursuit import PurePursuit
from libs.logger import Logger
from libs.commands import *
from libs.sensors.ir import ir
from modules.line_follower.line_follower import line_follower
from modules.line_follower.line_detector import LineDetector
from modules.golf_ball.golf_ball_follower import golf_ball_follower
# from modules.hole.hole_follower import hole_follower


class State(Enum):
    FOLLOWING_LINE = auto()
    FINISHED = auto()
    PURE_PURSUIT = auto()
    GOLF_BALL_FOLLOWING = auto()
    GRABBING_BALL = auto()
    HEAD_TO_HOLE = auto()


class Path:
    intersection_map = [
        'straight', # the first one is skipped
        #'search_ball', # this is the ACTUAL first direction
        #'straight',
        #'right',
        'big_int',
        'straight',
        'straight',
        'straight',
        'straight',
        'straight',
        'basket',
        '90right',
        'axe'
    ]


    def __init__(self):
        self.state: State = State.FOLLOWING_LINE
        #self.state: State = State.PURE_PURSUIT
        #self.state: State = State.GOLF_BALL_FOLLOWING
        self.finished = False

        self.old_state = self.state
        self.line_detector = LineDetector('logger')
        self.path_logger = Logger('path')
        self.intersection_counter = 0.5
        # self.pure_pursuit = PurePursuit(save_animation=True)
        # self.pure_pursuit_waypoints_creator = WaypointsCreator()
        # distance sensor initialization

        self.just_handled_intersection = True


    def __log(self, state):
        if self.old_state != state:
            print(f"[+] PATH  - State change to {state}")
            self.path_logger.info(f"State change from {self.old_state} to {state}")
            self.old_state = state


    def handle_path(self):
        # Reset here stuff if needed (this will run once after the 1st finish)
        if self.finished:
            # self.pure_pursuit.reset()
            line_follower.reset()
            self.finished = False

        ############################################################
        
        if self.state == State.PURE_PURSUIT:
            self.pure_pursuit.handle()

        ############################################################

        if self.state == State.FOLLOWING_LINE:

            # self.pure_pursuit_waypoints_creator.handle()

            line_follower.set_line_control(0.23)
            line_follower.follow_line()

            detect_results = self.line_detector.detect()
            active_sensors = detect_results['active_sensors']

            if not active_sensors:
                self.state = State.FINISHED

            # normal intersection
            if self.line_detector.is_intersection_detected():
                # first intersection, turn right
                self.intersection_counter += 0.5
                print(f'INTERSECTION: {self.intersection_counter}')
            # 90 degree intersection
            elif self.line_detector.is_90_intersection_detected():
                self.intersection_counter += 0.5
                print(f'90 INTERSECTION: {self.intersection_counter}')
                
            if self.intersection_counter == int(self.intersection_counter) and self.intersection_counter > 0 and self.intersection_counter < len(self.intersection_map) and self.just_handled_intersection:
                line_follower.handle_intersection(self.intersection_map[int(self.intersection_counter)])
                print(f'Direction: {self.intersection_map[int(self.intersection_counter)]}')

                if self.intersection_map[int(self.intersection_counter)] == 'search_ball':
                    self.state: State = State.GOLF_BALL_FOLLOWING

                if self.intersection_map[int(self.intersection_counter)] == 'basket':
                    self.just_handled_intersection = False

                    mqtt_service.send_cmd("ti/rc", f"0 0 {time()}")
                    sleep(0.5)
                    SERVO_set(0) #lower the servo but not on the ground
                    
                    # move in front for 1 sec to bump the basket
                    str_duration = 0.8
                    line_follower.set_line_control(0.1)
                    start_time = time()
                    while time() - start_time < str_duration:
                        pass
                    #putting the servo back
                    sleep(0.5)
                    SERVO_set(90)
                    sleep(0.5)
                    SERVO_off()

                    # do a turn around
                    line_follower.handle_intersection('back')
                    line_follower.handle_intersection('180')
                    # move in front for a bit then turn right
                    str_duration = 0.8
                    line_follower.set_line_control(0.1)
                    start_time = time()
                    while time() - start_time < str_duration:
                        pass
                    line_follower.handle_intersection('90right')

                    print('resume line following')
                    self.just_handled_intersection = True

                if self.intersection_map[int(self.intersection_counter)] == 'axe':
                    self.just_handled_intersection = False
                    #print('go slow')
                    line_follower.set_line_control(0.07)
                    #mqtt_service.send_cmd("ti/rc", f"{0.05} 0 {time()}")
                    while not ir.is_object_detected_in_front():
                        print('OBJ not detected')
                    
                    while ir.is_object_detected_in_front():
                        mqtt_service.send_cmd("ti/rc", f"0 0 {time()}")
                        print('STOP')

                    #print('Go Fast')
                    str_duration = 1.0
                    line_follower.set_line_control(0.3)
                    start_time = time()
                    while time() - start_time < str_duration:
                        pass
                
                #######################
                # delete if we don't wanna do the axe also the way back
                    ## turning back
                    line_follower.handle_intersection('180')
                    ## check again for the axe
                    
                    line_follower.set_line_control(0.05)
                    #mqtt_service.send_cmd("ti/rc", f"{0.05} 0 {time()}")
                    while not ir.is_object_detected_in_front():
                        print('OBJ2 not detected')
                    
                    while ir.is_object_detected_in_front():
                        mqtt_service.send_cmd("ti/rc", f"0 0 {time()}")
                        print('STOP2')

                    print('Go Fast Second time')
                    str_duration = 0.8
                    line_follower.set_line_control(0.3)
                    start_time = time()
                    while time() - start_time < str_duration:
                        pass
                    self.just_handled_intersection = True


                self.intersection_counter += 0.5

        ############################################################

        if self.state == State.GOLF_BALL_FOLLOWING:
            # it should go here after passing the ramp and after seeing the golf ball
            # then it would center the robot with the ball
            # then catch the ball and put it on the hole
            # then go back to line following
            SERVO_set(90)

            line_follower.set_line_control(0)
            #line_follower.handle_intersection('left')

            if golf_ball_follower is not None:
                print("GOLF_BALL_FOLLOWING")
                golf_ball_follower.set_ball_follower(0.2)
                golf_ball_follower.follow_ball()
            else:
                print("golf_ball_follower is not set!")

            print("Distance to the ball: ", golf_ball_follower.camera_service.ball['z_mm'])
            if golf_ball_follower.camera_service.ball['z_mm'] < 240 and golf_ball_follower.camera_service.ball['z_mm'] > 0:
                golf_ball_follower.stop_ball_follower()

                print('Going into grabbing ball state')
                sleep(1.5)
                self.state: State = State.GRABBING_BALL

        if self.state == State.GRABBING_BALL:
            self.path_logger.info('Grabbing the ball with servo arm')
            # Stop the robot first
            line_follower.set_line_control(0)
            golf_ball_follower.set_ball_follower(0)
            golf_ball_follower.stop_ball_follower()

            # Lower the arm to grab the ball
            self.path_logger.info('Lowering the servo')
            SERVO_set(-15)
            # Wait for the arm to lower
            sleep(2)
            
            # Transition to next state after grabbing
            self.state = State.HEAD_TO_HOLE

        if self.state == State.HEAD_TO_HOLE:
            # Turn around 180 degrees
            self.path_logger.info('Head to hole state started')
            line_follower.handle_intersection("turn_to_hole")
            line_follower.handle_intersection("approach_hole")
            line_follower.handle_intersection("wiggle")
            sleep(0.5)
            SERVO_set(90)
            sleep(0.5)
            SERVO_off()
            line_follower.handle_intersection('90left')
            line_follower.handle_intersection('back_to_line')
            
            # Go back to line following
            self.state = State.FOLLOWING_LINE
            #self.state = State.FINISHED


        ############################################################

        self.__log(self.state)

        # If finished, robot returns to waiting state
        self.finished = self.state == State.FINISHED
        if self.finished:
            print("Path:: finished")
            self.path_logger.info("Path finished")

        return self.finished
