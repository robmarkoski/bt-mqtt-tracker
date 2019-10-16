# Raspberry Pi Bluetooth Device Tracker and MQTT Client

**VERSION:** 0.2.0

**NOTE:** This is a massive change to the original script and __everything will break__. May as well consider this a completely new script.

## Description

This is a small script that turns a [Raspberry Pi](https://amzn.to/2PmapoY) into a MQTT device tracker for use with Home Assistant (or other IOT) equipment.

This is useful if you have a bunch of Pi's around the home anyway, and want to increase the accuracy of the presence detection.

## Table of Contents

- [Raspberry Pi Bluetooth Device Tracker and MQTT Client](#raspberry-pi-bluetooth-device-tracker-and-mqtt-client)
  - [Description](#description)
  - [Table of Contents](#table-of-contents)
  - [New Features](#new-features)
  - [How to install](#how-to-install)
    - [Requirements](#requirements)
    - [Update Settings](#update-settings)
  - [How to use new Sensor with Home Assistant](#how-to-use-new-sensor-with-home-assistant)
  - [OPTIONAL ENHANCEMENTS](#optional-enhancements)
    - [Run as a service](#run-as-a-service)
    - [Remote Device File Updating](#remote-device-file-updating)

## New Features

This is a complete change to original setup but now has some handy new features:

- There is a separate config.yaml file you need to update. No more editing python file!
- Device file is a separate yaml file also. This allows for both easier/simpler updating of devices but also remote updating. [See Below](#optional-remote-device-file-updating)
- RSSI values are now sent as part of the MQTT Payload. If you have a few sensors around you can now very roughly triangulate your position in your home.

## How to install

### Requirements

On the hardware side of things, make sure bluetooth is working.

On the software side, you need to install the following;

```bash

$ sudo apt install bluetooth libbluetooth-dev python3-bluez
$ pip3 install pybluez
$ pip3 install paho-mqtt
$ pip3 install pyyaml

```

### Update Settings

Update the settings in config.yaml as required.

```yaml

general:
  device_name: AwesomePi    # Not required. Defaults to Hostname
  device_location: Lounge   # Not Required. Defaults to Hostname (Recommended Though)
  status_update: 5          # Not Required. How often to check. Defaults to 5 Seconds

mqtt:
  user: mqtt_user                           # Required. MQTT Username
  password: "mqtt_password"                 # Required MQTT Password
  host: "127.0.0.1"                         # Required. Ip Address of MQTT Server
  port: 1883                                # Not Required. Port of MQTT. Defaults to 1883
  state_prefix: "HomeAssistant/PRESENCE"    # Required. Topic Prefix for MQTT
  qos: 0                                    # Not Required. Defaults to 0

bluetooth:
  timeout: 3        # Not Required. Bluetooth Timeout Length (seconds). Defaults to 3

logging:
  file_name: "bttracker.log"    # File Name to log to
  level: error                  # Level of file logging
  #console: debug               # Level of console logging. (Not Required)

```

Add your devices as per below. Note that these will form part of the state topic of the MQTT signal.

```yaml
devices:
    - name: "Device 1"
      description: "iPhone"
      mac: "aa:bb:cc:dd:ee:ff"
    - name: "Device 2"
      description: "iPhone"
      mac: "aa:bb:cc:dd:ee:ff"
```

The state topic is built as follows:

```
state_prefix/location/device_name/state
```

Based on the above settings, the state topic for mqtt messages will be:

```
HomeAssistant/Presence/Lounge/Device1/state
```

and

```
HomeAssistant/Presence/Lounge/Device2/state
```

## How to use new Sensor with Home Assistant

To add the sensor to Home Assistant use the [MQTT Sensor Component](https://www.home-assistant.io/components/sensor.mqtt/) a sample configuration is below:

```yaml
---
sensor:
  - platform: mqtt
    state_topic: "HomeAssistant/PRESENCE/Bedroom/Device_Name1/state"
    name: "Device 1 Bedroom Presence"
    value_template: "{{ value_json.state }}"
    json_attributes_topic: "HomeAssistant/PRESENCE/Bedroom/Device_Name1/state"
    json_attributes_template: "{{ value_json | tojson  }}"

  - platform: mqtt
    state_topic: "HomeAssistant/PRESENCE/Bedroom/Device_Name2/state"
    name: "Device 2 Bedroom Presence"
    value_template: "{{ value_json.state }}"
    json_attributes_topic: "HomeAssistant/PRESENCE/Bedroom/Device_Name2/state"
    json_attributes_template: "{{ value_json | tojson  }}"

```

Using the above sensor in conjuction with other device trackers and a [bayesian sensor](https://www.home-assistant.io/components/bayesian/), can make a pretty accurate device tracker.

## OPTIONAL ENHANCEMENTS

### Run as a service

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

Update the file location under **ExecStart**. You can update other settings as required and then load the service as follows:

```shell
$ sudo systemctl daemon-reload
$ sudo systemctl enable bttracker.service
$ sudo systemctl start bttracker.service
```

Check the status via:

```shell
$ sudo systemctl status bttracker.service
```

### Remote Device File Updating
For even simpler updating you can store the yaml file with the device addresses on a central server somewhere. Then use a simple script on a cron schedule to update it at some interval.

For example create a file called update_devices.sh

```bash
#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
curl -s -o ${DIR}/devices.yaml http://some_local_server/devices.yaml

```

Then edit your ```crontab -e``` with a daily run via

```bash
* 0 * * * /home/pi/priv-ha-bt-tracker/update_devices.sh >/dev/null 2>&1

```

Then all you need to do is update that single file and you know it will be propagated to each other device.
