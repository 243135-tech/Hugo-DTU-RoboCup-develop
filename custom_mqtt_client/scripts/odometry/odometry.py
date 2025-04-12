import csv
import os
from datetime import datetime

def log_odometry_data(odometry, filename="odometry_log.csv"):
    # Define the header for the CSV if the file doesn't exist yet
    header = [
        "timestamp",
        "motor_vel_left", "motor_vel_right",
        "wheel_vel_left", "wheel_vel_right",
        "pose_x", "pose_y", "pose_heading", "pose_tilt",
        "trip_dist", "trip_heading", "trip_time_passed",
        "total_dist", "total_heading", "total_time_passed"
    ]

    # Ensure the log file exists and has a header
    file_exists = os.path.isfile(filename)

    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(header)

        # Collect the data to log
        row = [
            datetime.now().isoformat(),
            odometry.motor_velocities[0],
            odometry.motor_velocities[1],
            odometry.wheel_velocities[0],
            odometry.wheel_velocities[1],
            odometry.pose[0],
            odometry.pose[1],
            odometry.pose[2],
            odometry.pose[3],
            odometry.trip_dist,
            odometry.trip_heading,
            odometry.trip_time_passed(),
            odometry.total_dist,
            odometry.total_heading,
            odometry.total_time_passed()
        ]

        writer.writerow(row)

        
