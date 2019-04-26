#!/usr/bin/python3
#
#   Bluetooth Device Tracking MQTT Client for Raspberry Pi (or others)
#
#   Version:    0.1
#   Status:     Development
#   Github:     https://github.com/robmarkoski/bt-mqtt-tracker
# 

import os
import time
import logging

import bluetooth
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt

# Add the name and Mac address of the each device. The name will be used as part of the state topic.
devices = [
    {"name": "Device1", "mac": "aa:bb:cc:dd:ee:ff", "state": "not home"},
    {"name": "Device2", "mac": "aa:bb:cc:dd:ee:f2", "state": "not home"}
    ]

# Provide name of the location where device is (this will form part of the state topic)
LOCATION = "Location"

# The final state topic will therefore be: HomeAssistant/Presence/LOCATION/DEVICE_NAME

# Update the follow MQTT Settings for your system.
MQTT_USER = "mqtt"              # MQTT Username
MQTT_PASS = "mqtt_password"     # MQTT Password
MQTT_CLIENT_ID = "bttracker"    # MQTT Client Id
MQTT_HOST_IP = "127.0.0.1"      # MQTT HOST
MQTT_PORT = 1883                # MQTT PORT (DEFAULT 1883)


SCAN_TIME = 30  # Interval Between Scans
BLU_TIMEOUT = 3 # How long during scan before there is a timeout.

# Set up logging.
LOG_NAME = "bt_tracker.log"      # Name of log file
LOG_LEVEL = logging.NOTSET       # Change to DEBUG for debugging. INFO For basic Logging or NOTSET to turn off


# SHOULDNT NEED TO CHANGE BELOW
MQTT_AUTH = {
    'username': MQTT_USER,
    'password': MQTT_PASS
}
LOG_FORMAT = "%(asctime)-15s %(message)s"
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__)) + "/"
LOG_FILE = SCRIPT_DIR + LOG_NAME
logging.basicConfig(filename=LOG_FILE,
                    level=LOG_LEVEL,
                    format=LOG_FORMAT,
                    datefmt='%Y-%m-%d %H:%M:%S')

try:
    logging.info("Starting BLE Tracker Server")
    while True:
        for device in devices:
            mac = device['mac']
            logging.debug("Checking for {}".format(mac))
            result = bluetooth.lookup_name(mac, timeout=BLU_TIMEOUT)
            if result:
                device['state'] = "home"
                logging.debug("Device Found!")
            else:
                device['state'] = "not home"
                logging.debug("Device Not Found!")
            try:
                publish.single("HomeAssistant/Presence/" + LOCATION + "/" + device['name'],
                    payload=device['state'],
                    hostname=MQTT_HOST_IP,
                    client_id=MQTT_CLIENT_ID,
                    auth=MQTT_AUTH,
                    port=MQTT_PORT,
                    protocol=mqtt.MQTTv311)
            except:
                logging.exception("MQTT Publish Error")
        time.sleep(SCAN_TIME)
except KeyboardInterrupt:
    logging.info("KEY INTERRUPT - STOPPING SERVER")
except:
    logging.exception("BLUETOOTH SERVER ERROR")
