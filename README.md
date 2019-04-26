# Raspberry Pi Bluetooth Device Tracker and MQTT Client

This is a small script that turns a [Raspberry Pi 3](https://amzn.to/2PmapoY) into a MQTT device tracker for use with Home Assistant (or other IOT) equipment.

This is useful if you have a bunch of Pi's around the home anyway, and want to increase the accuracy of the presence detection.

- [Raspberry Pi Bluetooth Device Tracker and MQTT Client](#raspberry-pi-bluetooth-device-tracker-and-mqtt-client)
  - [How to install](#how-to-install)
    - [Requirements](#requirements)
    - [Update Settings](#update-settings)
    - [(OPTIONAL) Add a service](#optional-add-a-service)
  - [How to use new Sensor with Home Assistant](#how-to-use-new-sensor-with-home-assistant)
  - [Troubleshooting](#troubleshooting)

## How to install

### Requirements
On the hardware side of things, make sure bluetooth is working.

On the software side, you need to install the following;
```bash
$ sudo apt install bluetooth libbluetooth-dev
$ pip3 install pybluez
$ pip3 install paho-mqtt
```

### Update Settings

Update the settings install bt_tracker.py with your own configuration.

Add your devices as per below. Note that these will form part of the state topic of the MQTT signal.

```python
devices = [
    {"name": "Device1", "mac": "aa:bb:cc:dd:ee:ff", "state": "not home"},
    {"name": "Device2", "mac": "aa:bb:cc:dd:ee:f2", "state": "not home"}
    ]
```
Also, provide a location for your device by changing the location variable:
```python
LOCATION = "Bedroom"
```
Based on the above settings, the device topic for mqtt messages will be:
```
HomeAssistant/Presence/Bedroom/Device1
```
AND
```
HomeAssistant/Presence/Bedroom/Device2
```

Next, update the MQTT settings:

```python

# Update the follow MQTT Settings for your system.
MQTT_USER = "mqtt"              # MQTT Username
MQTT_PASS = "mqtt_password"     # MQTT Password
MQTT_CLIENT_ID = "bttracker"    # MQTT Client Id
MQTT_HOST_IP = "127.0.0.1"      # MQTT HOST
MQTT_PORT = 1883                # MQTT PORT (DEFAULT 1883)
```

There are also settings you can mess around with, such as timeout of searching and scan intervals. Defaults work well for me, but feel free to change as required.

### (OPTIONAL) Add a service 
If you would like to have the Device Tracker to restart on startup, create the a file in the in the following location `/etc/systemd/system/bttracker.service`

```conf
[Unit]
Description=Raspberry Pi Device Tracker MQTT Service
After=network.target

[Service]
Type=idle
User=pi
ExecStart=/usr/bin/python3 /home/pi/bt-mqtt-tracker/bt_tracker.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Update the file location and other settings as required and then load the service as follows:

```shell
$ sudo systemctl daemon-reload
$ sudo systemctl enable bttracker.service
$ sudo systemctl start bttracker.service
```

## How to use new Sensor with Home Assistant

To add the sensor to Home Assistant use the [MQTT Sensor Component](https://www.home-assistant.io/components/sensor.mqtt/) a sample configuration is below (based on settings above):

```yaml
---
sensor:
  - platform: mqtt
    state_topic: "HomeAssistant/Presence/Bedroom/Device1"
    name: "Device 1 Bedroom Presence"

  - platform: mqtt
    state_topic: "HomeAssistant/Presence/Bedroom/Device2"
    name: "Device 2 Bedroom Presence"

```

Using the above sensor in conjuction with other device trackers and a [bayesian sensor](https://www.home-assistant.io/components/bayesian/), can make a pretty accurate device tracker.

## Troubleshooting
