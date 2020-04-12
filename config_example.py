# example of config.py file, input correct values and rename
NAME = 'sonoff'

WIFI_HOST = '<wifi_hostname>'
WIFI_SSID = '<wifi_ssid>'
WIFI_PASS = '<wifi_password>'

MQTT_CLIENT_ID = WIFI_HOST
MQTT_BROKER = 'xxx.xxx.xxx.xxx'
MQTT_PORT = 1883
MQTT_UNAME = None
MQTT_PASS = None
MQTT_DELAY = 1000

LED = {'gpio': 13, 'on': 0}
RELAY = {'gpio': 12, 'on': 1}
BUTTON = {'gpio': 0, 'on': 0}
RTIMER_DELAY = 250
BLINK_COUNT = 1
BLINK_DELAY = 250
RSAVE = 'relay.save'
WIFI_DELAY = 3000


