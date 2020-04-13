from machine import Timer
from umqtt.simple import MQTTClient
from utime import sleep_ms
from config import *
from wifi import WiFi
from sonoff import Sonoff

def check_wifi(timer=None):
    global s
    global w
    if w.isconnected():
        s.blink()
    else:
        try:
            w.connect()
        except Exception as e:
            print(e)

def mqtt_callback(topic, msg):
    topic = topic.decode()
    msg = msg.decode()
    global s
    global m
    if msg == '0':
        s.switch(0)
    elif msg == '1':
        s.switch(1)
    elif msg == '2':
        s.switch()
    elif msg == 'state':
        m.publish(MQTT_TOPIC_OUT, str(s.state()).encode())
    elif msg == 'blink':
        s.blink()
    elif msg == 'reset':
        s.reset()

sleep_ms(2000)
s = Sonoff()
s.load()

w = WiFi(WIFI_SSID, WIFI_PASS)
w.set_hostname(WIFI_HOST, -4)
MQTT_TOPIC_IN = str(w.hostname() + MQTT_TOPIC_IN).encode()
MQTT_TOPIC_OUT = str(w.hostname() + MQTT_TOPIC_OUT).encode()
try:
    w.connect()
except Exception as e:
    print(e)

w_t = Timer(0)
w_t.init(period=5000, mode=Timer.PERIODIC, callback=check_wifi)

m = MQTTClient(w.hostname(), MQTT_BROKER, MQTT_PORT)
m.set_callback(mqtt_callback)
m.connect()
m.subscribe(MQTT_TOPIC_IN)

s.set_mqtt(MQTT_TOPIC_OUT, m.publish)

s_t = Timer(1)
s_t.init(period=500, mode=Timer.PERIODIC, callback=s.check_relay)

m.publish(MQTT_TOPIC_OUT, str(s.state()).encode())
while True:
    try:
        # m.wait_msg()
        m.publish(MQTT_TOPIC_OUT, str(s.state()).encode())
        m.check_msg()
        sleep_ms(100)
    except Exception as e:
        print(e)
        m.connect()
        m.subscribe(MQTT_TOPIC_IN)

s.reset()
