# example of config.py file, input correct values and rename
WIFI_SSID = '<wifi_ssid>'
WIFI_PASS = '<wifi_password>'
WIFI_HOST = '<base_hostname>'

MQTT_CLIENT_ID = WIFI_HOST
MQTT_BROKER = 'xxx.xxx.xxx.xxx'
MQTT_PORT = 1883
MQTT_UNAME = WIFI_HOST
MQTT_PWD = '<mqtt_password>'

TOPIC_IN = (MQTT_CLIENT_ID + '/in').encode()
TOPIC_OUT = (MQTT_CLIENT_ID + '/out').encode()

LED = {'gpio': 13, 'on': 0}
RELAY = {'gpio': 12, 'on': 1}
BUTTON = {'gpio': 0, 'on': 0}
