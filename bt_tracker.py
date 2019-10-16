#!/usr/bin/python3
#
#   Bluetooth Dervice Tracking MQTT Client for Raspberry Pi (or others)
#
#   Version:    0.2.0
#   Status:     Development
#   Github:     https://github.com/robmarkoski/bt-mqtt-tracker

import os
import time
import logging
import json
import socket
from bt_rssi import BluetoothRSSI

try:
    import paho.mqtt.publish as publish
    import paho.mqtt.client as mqtt
except ImportError as error:
    raise ImportError("Can't Import Paho-Mqtt \n Install with \"pip3 install paho-mqtt\"\n {}".format(error))    

try:
    import bluetooth
except ImportError as error:
    raise ImportError("Can't Import bluetooth \n Install with \"pip3 install pybluez\"\n {}".format(error))
try:
    import yaml
except ImportError as error:
    raise ImportError("Can't Import PyYaml \n Install with \"pip3 install pyyaml\"\n {}".format(error))

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

try:
    ymlfile = open(SCRIPT_DIR + "/config.yaml", 'r') 
except IOError:
    raise IOError("Error: Cant open config file")
with ymlfile:
    cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)

try:
    ymlfile = open(SCRIPT_DIR + "/devices.yaml", 'r') 
except IOError:
    raise IOError("Error: Cant open devices file")
with ymlfile:
    dvc = yaml.load(ymlfile, Loader=yaml.FullLoader)

devices = dvc['devices']

LOCATION = cfg['general'].get('device_location', socket.gethostname())
DEVICE_NAME = cfg['general'].get('device_name', socket.gethostname())
SCAN_TIME = cfg['general'].get('status_update', 5)
BLU_TIMEOUT = cfg['bluetooth'].get('timeout', 3)

############### MQTT ######################
MQTT_USER = cfg['mqtt']['user']
MQTT_PASS = cfg['mqtt']['password']
MQTT_CLIENT_ID = "MQTT_" + DEVICE_NAME
MQTT_HOST_IP = cfg['mqtt']['host']
MQTT_PORT = cfg['mqtt'].get('port', 1883)
MQTT_QOS = cfg['mqtt'].get('qos', 0)
MQTT_AUTH = {
    'username': MQTT_USER,
    'password': MQTT_PASS
}
MQTT_STATE_PREFIX = cfg['mqtt']['state_prefix'] + "/" + LOCATION
MQTT_STATE_TOPIC = MQTT_STATE_PREFIX + "/{}/state"

########### LOGGING SETUP #############
LOG_FILE_NAME = cfg['logging']['file_name']
LOG_FILE = SCRIPT_DIR + "/" + LOG_FILE_NAME
LOG_LEVEL = cfg['logging'].get('level', "INFO")
LOG_LEVEL_NUM = getattr(logging, LOG_LEVEL.upper(), None)
# Set log level https://docs.python.org/3/howto/logging.html#logging-basic-tutorial
if not isinstance(LOG_LEVEL_NUM, int):
    raise ValueError("Invalid log level: %s" % LOG_LEVEL)
LOG_FORMAT = "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logFormatter = logging.Formatter(LOG_FORMAT)
if cfg['logging'].get('filename'):
    fileHandler = logging.FileHandler(LOG_FILE)
    fileHandler.setLevel(LOG_LEVEL_NUM)
    fileHandler.setFormatter(logFormatter)
    logger.addHandler(fileHandler)

if cfg['logging'].get('console'):
    consoleHandler = logging.StreamHandler()
    consoleHandler.setLevel(getattr(logging, cfg['logging']['console'].upper(), None))
    consoleHandler.setFormatter(logFormatter)
    logger.addHandler(consoleHandler)


def lookup_device(mac: str):
    """ Look for Bluetooth Device
        mac: Mac address of device
    """
    logger.debug("Looking for device: {}".format(mac))
    result = bluetooth.lookup_name(mac, timeout=BLU_TIMEOUT)
    logger.debug("Result of Lookup: {}".format(result))

    return result


def lookup_rssi(mac: str):
    """ Get Rssi of Device
        mac: mac address of device
    """
    logger.debug("Getting RSSI of: {}".format(mac))
    rssi = None
    client = BluetoothRSSI(mac)
    rssi = client.request_rssi()
    logger.debug("Raw RSS: {}".format(rssi))
    if rssi is None:
        logger.debug("No RSSI Information")
        return "None"
    else:
        logger.debug("Device RSSI: {}".format(rssi[0]))
        return rssi[0]
    client.close()

try:
    logger.info("Starting BLE Tracker Server")

    while True:
        for device in devices:
            mac = device['mac']
            result = lookup_device(mac)            
            if result:
                device['state'] = "home"
                logger.debug("Device Found!")
                rssi = lookup_rssi(mac)
                device['rssi'] = rssi

            else:
                device['rssi'] = "None"
                device['state'] = "not_home"
                logger.debug("Device Not Found!")
            try:
                logger.debug("Publishing to state topic: {}".format(MQTT_STATE_TOPIC.format(device['name'])))
                logger.debug("Data to be published:\n {}".format(json.dumps(device)))
                publish.single(MQTT_STATE_TOPIC.format(device['name']),
                               payload=json.dumps(device),
                               hostname=MQTT_HOST_IP,
                               client_id=MQTT_CLIENT_ID,
                               auth=MQTT_AUTH,
                               port=MQTT_PORT,
                               protocol=mqtt.MQTTv311)
            except:
                logger.exception("MQTT Publish Error")
        time.sleep(SCAN_TIME)
except KeyboardInterrupt:
    logger.info("KEY INTERRUPT - STOPPING SERVER")
except bluetooth.BluetoothError:
    logger.exception("BLUETOOTH ERROR")
