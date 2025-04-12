#!/bin/bash

# Kill the current Python program by name or PID
pkill my-mqtt-client
pkill mqtt-client

# Wait for the current process to end
wait

cd /home/local/svn/robobot/mqtt_python
/usr/bin/python3 mqtt-client.py --white