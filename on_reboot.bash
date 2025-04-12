#!/bin/bash
# Script to start applications after a reboot. This is started by crontab
# p.s. PID = process ID

SVN_FOLDER=/home/local/svn
LOG_FOLDER=$SVN_FOLDER/log
REBOOT_INFO_FILE=$LOG_FOLDER/reboot_log.txt

mkdir -p $LOG_FOLDER

# Save the last reboot date
echo "================ Rebooted ================" > $REBOOT_INFO_FILE
date >> $REBOOT_INFO_FILE

# Start ip_disp (app to show Raspberry's IP on the Teensy display)
# stdbuf -o0 -e0 $SVN_FOLDER/robobot/ip_disp/build/ip_disp 2>$LOG_FOLDER/ip_disp.err >$LOG_FOLDER/ip_disp.out &
$SVN_FOLDER/robobot/ip_disp/build/ip_disp 2>$LOG_FOLDER/ip_disp.err >$LOG_FOLDER/ip_disp.out &
sleep 0.1
echo "[+] ip_disp started with PID: $(pgrep -l ip_disp)" >> $REBOOT_INFO_FILE

# Start camera server
cd $SVN_FOLDER/robobot/stream_server
/usr/bin/python3 stream_server.py 2>stream_server.err >stream_server.out &
sleep 0.1
echo "[+] python3 cam streamer started with PID: $(pgrep -l python)" >> $REBOOT_INFO_FILE

# Start teensy_interface
cd $SVN_FOLDER/robobot/teensy_interface/build
./teensy_interface -d -l 2>$LOG_FOLDER/teensy_interface.err >$LOG_FOLDER/teensy_interface.out &
sleep 0.1
echo "[+] teensy_interface started with PID: $(pgrep -l teensy_i)" >> $REBOOT_INFO_FILE

cd /home/local/custom_mqtt_client
stdbuf -o0 -e0 /usr/bin/python3 main.py >$LOG_FOLDER/custom_mqtt_client.out 2>$LOG_FOLDER/custom_mqtt_client.err &
sleep 2.5
echo "[+] MQTT client started with PID: $(pgrep -l my-mqtt-client)" >> $REBOOT_INFO_FILE

# Print new line and exit
echo '' >> $REBOOT_INFO_FILE
exit 0
