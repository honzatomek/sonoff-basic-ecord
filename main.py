# ---------------------------------- micropython modules ---            # {{{1
import machine
import network
import uos
import ubinascii
from utime import sleep_ms
from umqtt.robust import MQTTClient

# --------------------------------------- custom modules ---            # {{{1
from config import *


# ---------------------------------------------- classes ---
class WiFi:                                                             # {{{1
    def __init__(self, ssid, password, hostname):                       # {{{2
        network.WLAN(network.AP_IF).active(False)

        self.ssid = ssid
        self.pwd = password

        self.sta = network.WLAN(network.STA_IF)
        self.mac = ubinascii.hexlify(network.WLAN().config('mac'),'').decode()
        self.hostname = hostname + self.mac[-4:]

        self.sta.config(dhcp_hostname=hostname + self.mac[-4:])

    def connect(self, delay=200, blink=None):                           # {{{2
        for i in range(5):
            if not self.sta.isconnected():
                if not self.sta.active():
                    self.sta.active(True)
                self.sta.connect(self.ssid, self.pwd)
                sleep_ms(delay)
            else:
                if blink is not None:
                    blink(3, 250)
                return True
        if blink is not None:
            blink(1, 2000)
        return False


class Sonoff:                                                           # {{{1
    def __init__(self, name='sonoff'):                                  # {{{2
        self.name = name

        self.led = machine.Pin(LED['gpio'],
                               machine.Pin.OUT,
                               value=(1 - LED['on']))

        self.button = machine.Pin(BUTTON['gpio'], machine.Pin.IN)
        self.button.irq(trigger=machine.Pin.IRQ_FALLING,
                        handler=self.button_cb)

        self.relay_value = self.load_state()
        self.relay = machine.Pin(RELAY['gpio'],
                                 machine.Pin.OUT,
                                 value=self.relay_value)

        self.timer = machine.Timer(0)
        self.timer.init(period=RTIMER_DELAY,
                        mode=machine.Timer.PERIODIC,
                        callback=self.check)

        self.wifi = None
        self.mqtt = None

    def blink(self, count=BLINK_COUNT, delay=BLINK_DELAY):  # {{{2
        for i in range(2 * count - 1):
            self.led.value(not self.led.value())
            sleep_ms(delay)
        self.led.value(1 - LED['on'])

    def button_cb(self, pin=None):                                      # {{{2
        bval = self.button.value()
        for i in range(11):
            sleep_ms(250)
            if self.button.value() != bval:
                self.blink()
                self.switch()
                return
        self.reset()

    def load_state(self):                                               # {{{2
        try:
            with open(RSAVE, 'r') as rst:
                return int(rst.readline().strip('\n'))
        except Exception as e:
            self.relay_value = 0
            self.save_state()
            return 0

    def save_state(self):                                               # {{{2
        with open(RSAVE, 'w') as rst:
            rst.write(str(self.relay_value))

    def check(self, timer=None):                                                    # {{{2
        if self.relay.value() != self.relay_value:
            self.relay.value(self.relay_value)

    def switch(self, value=None):                                       # {{{2
        if value is None or value == 2:
            self.relay.value(not self.relay.value())
        elif value == 1:
            self.relay.value(RELAY['on'])
        elif value == 0:
            self.relay.value(1 - RELAY['on'])
        self.relay_value = self.relay.value()
        if self.mqtt is not None:
            mqtt_publish(self.relay_value)

    def reset(self):                                                    # {{{2
        self.save_state()
        self.blink(3)
        machine.reset()

    def connect(self):
        pass


# -------------------------------------------- functions ---
def mqtt_subscribe(topic, msg):                                         # {{{1
    global s
    msg = msg.decode()
    if msg in [0, 1, 2]:
        s.switch(msg)
    elif msg == 'state':
        mqtt_publish(s.relay_value)
    elif msg == 'blink':
        s.blink(3, 250)
    elif msg == 'reset':
        s.reset()


def mqtt_publish(message):                                              # {{{1
    global s
    topic = s.mqtt.client_id + '/out'
    s.mqtt.publish(topic.encode(), message.encode())


# ---------------------------------------------- program ---            # }}}1
sleep_ms(1000)
s = Sonoff(NAME)
s.load_state()
w = WiFi(WIFI_SSID, WIFI_PASS, s.name)
w.connect(blink=s.blink)
WIFI_HOST = w.hostname
MQTT_CLIENT_ID = w.hostname

s.mqtt = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT,
                    user=MQTT_UNAME, password=MQTT_PASS)
s.mqtt.set_callback(mqtt_subscribe)
s.mqtt.connect(clean_session=False)
TOPIC_IN = s.mqtt.client_id + '/in'
s.mqtt.subscribe(TOPIC_IN.encode())

mqtt_publish(s.relay_value)
while True:
    try:
        s.mqtt.check_msg()
        sleep_ms(MQTT_DELAY)
    except Exception as e:
        break

s.reset()

# vim:fdm=marker:fdl=1:
