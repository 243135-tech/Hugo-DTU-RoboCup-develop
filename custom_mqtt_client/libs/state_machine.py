from enum import Enum, auto
from libs.logger import Logger
import subprocess
from time import sleep
from typing import Callable
from libs.services.gpio_service import gpio
from libs.commands import *
from libs.args import arg_parser
from libs.services.mqtt_service import mqtt_service
from libs.services.data_logger_service import data_logger_service
from libs.sensors.odometry import odometry
from threading import Thread


class State(Enum):
    NONE = auto()
    WAITING = auto()
    GOING = auto()
    FINISHED = auto()  # Shouldn't be used, otherise the python script will stop


class StateMachine:
    SLEEP_TIME_SEC = 0.1
    LOG_SLEEP_SEC = 0.01
    SHUTDOWN_BTN = 16
    AUTO_PULL_BTN = 12

    def __init__(self, handle_going_state: Callable[[], bool]) -> None:
        """
        handle_going_state() -> bool: function that handles the going state, sould return True when we intend to finish the mission (returns to waiting state, waiting for start button)
        """

        self.logger = Logger('state_machine')
        self.state: State = State.WAITING
        self.old_state: State = State.NONE
        self.handle_going_state = handle_going_state
        self.logger.info("State machine initialized")

        self.data_logger_thread = Thread(target = self.__log)
        self.data_logger_thread.start()
        self.logger.info("Data logger thread started")


    def __del__(self):
        try:
            self.data_logger_thread.join()
        except:
            pass


    def __handle_auto_pull_git(self) -> None:
        self.logger.info("AUTO_PULLER - Pulling git")
        LED_mission_pulling_git()

        result = subprocess.run(
            ["git", "-C", "/home/local/", "pull"],
            text=True,
            capture_output=True
        )
        # Print stdout and stderr
        self.logger.info(result.stdout)
        self.logger.info(result.stderr)

        LED_mission_off()

        # Run the restart script and quit current program
        self.logger.info("AUTO_PULLER - Pulled. Restarting the program")
        subprocess.run(["bash", "/home/local/restart_mqtt.bash"])
        exit()


    def __log(self) -> None:
        while not mqtt_service.stopped and self.state != State.FINISHED:
            if self.state == State.GOING:
                data_logger_service.write(self.state.name)

            # Print state change
            if self.state != self.old_state:
                self.logger.info(f"STATE CHANGED from {self.old_state.name} to {self.state.name}")
                data_logger_service.write_comment(f"STATE_MACHINE - State changed from {self.old_state.name} to {self.state.name}")
                self.old_state = self.state

            sleep(self.LOG_SLEEP_SEC)


    def __stop_robot(self) -> None:
        self.logger.info("Stopping robot")
        LED_mission_waiting()
        self.state = State.WAITING
        ROBOT_stop_movement()


    def __handle_extra_buttons(self) -> None:
        # Check for auto-pulling git
        if gpio.pin(self.AUTO_PULL_BTN).get():
            self.__handle_auto_pull_git()
        elif gpio.pin(self.SHUTDOWN_BTN).get():
            self.logger.info("Shutting down the robot")
            self.__stop_robot()
            ROBOT_shutdown()


    def __handle_states(self) -> None:
        # Wait for start signal
        if self.state == State.WAITING:
            # Check if start
            if gpio.is_start_pressed() or arg_parser.get("now"):
                if arg_parser.get("now"):
                    arg_parser.set("now", False)
                else:
                    self.logger.info("Starting mission (with 500ms delay)")
                    sleep(0.5)

                LED_mission_running()
                ROBOT_stop_movement()
                self.state = State.GOING
                odometry.reset_trip()

            else:
                self.__handle_extra_buttons()

        elif self.state == State.GOING:
            # Delegate the main logic to the handle_going_state function
            finished = self.handle_going_state()

            # If finished go to waiting state again, otherwise keep going
            if finished:
                self.__stop_robot()

        elif self.state == State.FINISHED:
            LED_mission_finished()
            self.logger.error("NOOOOOOOOOO this should never happend - I went to finished state, now I'm dead :(")


    def loop(self) -> None:
        while not mqtt_service.stopped and self.state != State.FINISHED:
            # Handle states
            self.__handle_states()

            if gpio.is_stop_pressed():
                self.__stop_robot()

            # Do not loop too fast
            sleep(self.SLEEP_TIME_SEC)
            # Tell interface that we are alive
            ROBOT_send_alive()
