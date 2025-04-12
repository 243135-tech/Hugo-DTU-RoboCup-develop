from libs.services.mqtt_service import mqtt_service
from modules.line_follower.line_follower import line_follower
from time import sleep, time
# from threading import Thread


def LED_set_color(number: int, r: int, g: int, b: int):
    """
    Sets the desired led to the desired color.
    Example: set_led(LED_MISSION, 30, 30, 0), sets the LED 16 to yellow
    """
    mqtt_service.send_cmd("T0/leds", f"{number} {r} {g} {b}")


def LED_off(number):
    LED_set_color(number, 0, 0, 0)


def LED_blink(number: int, r: int, g: int, b: int, dt: float, count: int):
  for _ in range(count):
    LED_set_color(number, r, g, b)
    sleep(dt)
    LED_off(number)
    sleep(dt)


# def LED_blink(number: int, r: int, g: int, b: int, dt: float, count: int):
#     blink_thread = Thread(target=LED_blink, args=(number, r, g, b, dt, count))
#     blink_thread.daemon = True  # This ensures the thread ends when the main program ends
#     blink_thread.start()



LED_MISSION = 16

def LED_mission_off():
    LED_off(16)

def LED_mission_waiting():
    LED_set_color(LED_MISSION, 255, 0, 255) # fuchsia

def LED_mission_running():
    LED_set_color(LED_MISSION, 0, 0, 255) # blue

def LED_mission_finished():
    LED_set_color(LED_MISSION, 255, 0, 0) # red

def LED_mission_pulling_git():
    LED_blink(LED_MISSION, 241, 76, 40, 0.1, 4)

def LED_mission_restarting():
    LED_blink(LED_MISSION, 255, 255, 255, 0.1, 3)





def ROBOT_set_movement(forward_velocity: float, turnrate: float, time: float = 0):
    """
    Moves the robot with the desired forward velocity and turnrate.
    Example: move(0.1, 0.5), moves the robot forward with 0.1 m/s and turns left with 0.5 rad/s
    """
    mqtt_service.send_cmd("ti/rc", f"{forward_velocity} {turnrate} {'' if time == 0 else time}")

def ROBOT_stop_movement():
    print("[!] Stopped robot movement")
    ROBOT_set_movement(0, 0)
    line_follower.set_line_control(0)

def ROBOT_set_motors_voltage(left: float, right: float):
    """
    Sets the raw motor voltages
    """
    mqtt_service.send_cmd("T0/motv", f"{left} {right}")

def ROBOT_send_alive():
    """
    Tell interface that we are alive
    """
    mqtt_service.send_cmd("ti/alive", str(mqtt_service.start_time))

def ROBOT_shutdown():
    print("[!] Sent shutdown signal")
    LED_blink(LED_MISSION, 255, 0, 0, 0.2, 5)
    mqtt_service.send_cmd("shutdown", f"{time()}")




def SERVO_set(angle_deg: int, servo_num: int = 1):
    """
    Set the specified servo to the desired angle (+-90°)
    """
    if angle_deg > 90:
        angle_deg = 90
    elif angle_deg < -90:
        angle_deg = -90

    ang_min = -90
    ang_max = 90
    out_min = 800
    out_max = -900
    position = out_min + (angle_deg - ang_min) * (out_max - out_min) / (ang_max - ang_min)

    velocity = 200
    mqtt_service.send_cmd("T0/servo", f"{servo_num} {position} {velocity}")

def SERVO_off(servo_num = 1):
    SERVO_set(9999, servo_num)