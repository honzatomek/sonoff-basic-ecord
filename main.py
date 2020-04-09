# ---------------------------------- micropython modules ---
import machine
import network
from utime import sleep_ms
from umqtt.simple import MQTTClient


# --------------------------------------- custom modules ---
from config import *


# -------------------------------------------- functions ---
def gpio(gpio_pin=13, value='toggle', count=3, sleep=500):
    if isinstance(gpio_pin, int):
        pin = gpio_pin
        on = 0
    elif isinstance(gpio_pin, dict):
        pin = gpio_pin['gpio']
        on = gpio_pin['on']

    p = machine.Pin(pin, machine.Pin.OUT, value=machine.Pin(pin).value())
    if value == 'on':
        p.value(on)
    elif value == 'toggle':
        p.value(not p.value())
    elif value == 'blink':
        p.value(on)
        for i in range(count * 2 - 1):
            sleep_ms(sleep)
            p.value(not p.value())
    else:
        p.value(1 - on)

    return 'on' if p.value() == on else 'off'


def isconnected():
    return network.WLAN(network.STA_IF).isconnected()


def connect():
    network.WLAN(network.AP_IF).active(False)
    sta = network.WLAN(network.STA_IF)
    sta.config(dhcp_hostname=WIFI_HOST)
    sta.active(True)
    sta.connect(WIFI_SSID, WIFI_PASS)
    
#     for t in range(10):
#         sleep_ms(10 * t)
#         if sta.isconnected():
#             gpio(LED, 'blink', 3, 500)
#             return True
#     
#     gpio(LED, 'on')
#     return False


def relay_state():
    return 'on' if machine.Pin(RELAY['gpio']).value() == RELAY['on'] else 'off'


def reset(pin=None):
    with open('relay_state', 'w') as rst:
        rst.write(relay_state())

    gpio(LED, 'blink', 1, 1000)
    machine.reset()


def timeout_callback(t):
    if isconnected():
        gpio(LED, 'blink', 1, 250)
    else:
        gpio(LED, 'on')
        connect()


def subscribe_callback(topic, msg):
    retval = None
    msg = msg.decode()
    if msg == 'blink':
        gpio(LED, 'blink')
    elif msg in ['on', 'off', 'toggle']:
        retval = gpio(RELAY, msg)
    elif msg == 'state':
        retval = relay_state()
    elif msg == 'reset':
        reset()

    if retval is not None:
        publish(retval)


def publish(value):
    global mqtt
    mqtt.publish(TOPIC_OUT, value.encode())

    
# ---------------------------------------------- program ---
with open('relay_state', 'r') as rst:
    gpio(RELAY, rst.readline().strip('\n'))

sleep_ms(1000)

connect()
while not isconnected():
    sleep_ms(100)
gpio(LED, 'blink')

t = machine.Timer(0)
t.init(period=5000, mode=machine.Timer.PERIODIC, callback=timeout_callback)

r = machine.Pin(BUTTON['gpio'], machine.Pin.IN)
r.irq(trigger=machine.Pin.IRQ_FALLING, handler=reset)

mqtt = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER)
mqtt.set_callback(subscribe_callback)
mqtt.connect()
mqtt.subscribe(TOPIC_IN)

publish(relay_state())
while True:
    try:
        mqtt.check_msg()
        sleep_ms(100)
    except Exception as e:
        reset()

