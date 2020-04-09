# ---------------------------------- micropython modules ---
import machine
import network
from utime import sleep_ms


# --------------------------------------- custom modules ---
from config import *


# -------------------------------------------- functions ---
def gpio(gpio_pin=13, value='toggle', count=3, sleep=500):
    if isinstance(gpio_pin, int):
        pin = gpio_pin
        on = 0
    elif isinstance(gpio_pin, dict):
        pin = gpio_pin['GPIO']
        on = gpio_pin['ON']

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


def connect():
    network.WLAN(network.AP_IF).active(False)
    sta = network.WLAN(network.STA_IF)
    sta.config(dhcp_hostname=WIFI_HOST)
    sta.active(True)
    sta.connect(WIFI_SSID, WIFI_PASS)
    
    for t in range(10):
        sleep_ms(10 * t)
        if sta.isconnected():
            gpio(LED, 'blink', 3, 500)
            return True

    return False


def reset(pin=None):
    gpio(LED, 'blink', 1, 1000)
    machine.reset()

    
# ---------------------------------------------- program ---
r = machine.Pin(BUTTON['GPIO'], machine.Pin.IN)
r.irq(trigger=machine.Pin.IRQ_FALLING, handler=reset)

if not connect():
    gpio(LED, 'on')

