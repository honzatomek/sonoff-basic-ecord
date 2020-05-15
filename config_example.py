# example of config.py file, input correct values and rename
DEBUG = True                    # if false, most print commands will not be printed, only exception messages

WLAN_HOST = 'snf'               # wlan dhcp_hostname prefix, 4 last chars of mac address will be appended
WLAN_SSID = '<wifi_ssid>'       # wireless network ssid
WLAN_PASS = '<wifi_password>'   # wireless network password
WLAN_RTRY = 3                   # number of retries for wlan connection to WLAN_SSID
WLAN_DLAY = 5000                # delay in ms to wait for successful connection to WLAN_SSID in one try

MQTT_BRKR = 'xxx.xxx.xxx.xxx'   # mqtt broker ip address
MQTT_PORT = 1883                # mqtt broker port
MQTT_UNAM = None                # not yet implemented
MQTT_PASS = None                # not yet implemented

MQTT_TPIN = '/in'               # inbound topic suffix - resulting topic will be dhcp_hostname + MQTT_TPIN
MQTT_TPOU = '/out'              # outbound topic suffix - resulting topic will be dhcp_hostname + MQTT_TPOU
