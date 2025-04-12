#!/bin/bash

# Default: Run the process in the background and without DEBUG log level
background=true
log_level=""
now=""

# Parse command-line arguments
while getopts "idn" opt; do
    case $opt in
        i)
            # If -i is passed, do not run in the background
            background=false
            ;;
        d)
            # If -d is passed, add --log-level DEBUG
            log_level="--log-level DEBUG"
            ;;
        n)
            now="--now"
            ;;
        *)
            echo "Usage: $0 [-i] [-d]"  # Display usage if incorrect arguments
            exit 1
            ;;
    esac
done

# Kill the current Python program by name or PID
pkill my-mqtt-client

# Wait for the current process to end
wait

SVN_FOLDER=/home/local/svn
LOG_FOLDER=$SVN_FOLDER/log
REBOOT_INFO_FILE=$LOG_FOLDER/reboot_log.txt

# Check if teensy_interface is running
teensy_running=$(pgrep -l teensy_i | wc -l)
if [ "$teensy_running" -eq 0 ]; then
    echo "[+] Teensy interface not running, starting it..." >> $REBOOT_INFO_FILE
    # Start teensy_interface
    cd $SVN_FOLDER/robobot/teensy_interface/build
    ./teensy_interface -d -l 2>$LOG_FOLDER/teensy_interface.err >$LOG_FOLDER/teensy_interface.out &
    sleep 0.1
    echo "[+] teensy_interface started with PID: $(pgrep -l teensy_i)" >> $REBOOT_INFO_FILE
    # Return to original directory path
fi


cd /home/local/custom_mqtt_client

# Prepare the command to run the Python script

command="/usr/bin/python3 main.py $log_level $now"

################### Testing line following in teensy: ######################
#command="/usr/bin/python3 main_new.py $log_level $now"

if [ "$background" = true ]; then
    # Run in the background
    stdbuf -o0 -e0 $command >$LOG_FOLDER/custom_mqtt_client.out 2>$LOG_FOLDER/custom_mqtt_client.err &
    sleep 1.5
    echo "[+] restarted MQTT client with PID: $(pgrep -l my-mqtt-client)" >> $REBOOT_INFO_FILE
else
    # Run interactively (not in the background)
    $command
    # python /home/local/custom_mqtt_client/scripts/line_sensor/line_sensor_pid.py
fi
