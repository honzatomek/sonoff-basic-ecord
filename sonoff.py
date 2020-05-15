import machine
import utime
from uos import listdir
from umqtt.robust import MQTTClient
import gc
from wlan import WLAN
import builtins

from config import DEBUG
from config import WLAN_SSID, WLAN_PASS, WLAN_DLAY
from config import MQTT_BRKR, MQTT_PORT, MQTT_TPIN, MQTT_TPOU


def print(*args, **kwargs):
    if DEBUG:
        builtins.print(*args, **kwargs)


def eprint(*args, **kwargs):
    builtins.print(*args, **kwargs)


def load(save_file='relay.save', default=0):
    try:
        if save_file in listdir('/'):
            with open(save_file, 'r', encoding='utf-8') as save:
                return int(save.readline())
        else:
            return default
    except Exception as e:
        eprint('[-] load: Exception occured\n    {0}'.format(e))
        return default


def save(value, save_file='relay.save'):
    try:
        with open(save_file, 'w', encoding='utf-8') as save:
            save.write(str(value))
        return True
    except Exception as e:
        eprint('[-] save: Exception occured\n    {0}'.format(e))
        return False


class SonoffException(Exception):
    pass


class Relay:
    def __init__(self, pin=12, on=1, value='load'):
        self.__on = on
        self.__off = 1 - on
        if value == 'load':
            self.__pin = machine.Pin(pin, machine.Pin.OUT,
                                     value=load(default=self.__off))
        elif value == 'state':
            self.__pin = machine.Pin(pin, machine.Pin.OUT,
                                     value=machine.Pin(pin).value())
        else:
            self.__pin = machine.Pin(pin, machine.Pin.OUT, value=value)
        self.__last_val = self.__pin.value()

    def state(self):
        if self.__pin.value() == self.__on:
            return 1
        else:
            return 0

    def store(self):
        self.__last_val = self.__pin.value()

    def save(self):
        save(self.__pin.value())

    def on(self):
        self.__pin.value(self.__on)
        self.store()
        return 1

    def off(self):
        self.__pin.value(self.__off)
        self.store()
        return 0

    def toggle(self):
        self.__pin.value(not self.__pin.value())
        self.store()
        return self.state()

    def check(self):
        if self.__pin.value() != self.__last_val:
            self.toggle()
#         print('[i] Relay.check: {0}.'.format(self.state()))
        return self.state()

    def switch(self, value):
        if value is None or value in [2, '2', 'toggle']:
            return self.toggle()
        elif value in [0, '0', 'off']:
            return self.off()
        elif value in [1, '1', 'on']:
            return self.on()
        return self.state()


class Led:
    def __init__(self, pin=13, on=0, value=1):
        self.__on = on
        self.__off = 1 - on
        self.__pin = machine.Pin(pin, machine.Pin.OUT, value=value)

    def on(self):
        self.__pin.value(self.__on)

    def off(self):
        self.__pin.value(self.__off)

    def toggle(self):
        self.__pin.value(not self.__pin.value())

    def blink(self, count=1, delay=250):
        self.off()
        for i in range((count - 1) * 2 + 1):
            self.toggle()
            utime.sleep_ms(delay)
        self.off()


class Button:
    def __init__(self, pin=0, on=0, callback=None):
        self.__on = on
        self.__off = 1 - on
        self.__pin = machine.Pin(pin, machine.Pin.IN)
        self.__callback = callback
        if self.__callback is not None:
            self.__pin.irq(trigger=machine.Pin.IRQ_FALLING,
                           handler=self.__callback)

    def set_callback(self, callback):
        self.__callback = callback
        if self.__callback is not None:
            self.__pin.irq(trigger=machine.Pin.IRQ_FALLING,
                           handler=self.__callback)

    def state(self):
        if self.__pin.value() == self.__on:
            return 1
        else:
            return 0


class Sonoff:
    def __init__(self, button_callback=None):
        self.led = Led()
        if button_callback is None:
            self.button = Button(callback=self.button_callback)
        else:
            self.button = Button(callback=button_callback)
        self.relay = Relay()

        self.wlan = WLAN(WLAN_SSID, WLAN_PASS)

        self.mqtt = None
        self.mqtt_topic_in = MQTT_TPIN
        self.mqtt_topic_out = MQTT_TPOU

    def reset(self, save_state=True):
        self.led.blink(1, 1000)
        if save_state:
            self.relay.save()
        machine.reset()

    def mqtt_publish(self, message):
        if self.mqtt is not None:
            try:
                print('[i] Sonoff.mqtt_publish: {0} - {1}'.format(self.mqtt_topic_out.decode('utf-8'), message))
                self.mqtt.publish(self.mqtt_topic_out, str(message).encode())
            except KeyboardInterrupt:
                raise
            except Exception as e:
                eprint('[-] Sonoff.mqtt_publish: {0}'.format(e))
                self.mqtt.reconnect()

    def button_callback(self, pin):
        bstart_ms = utime.ticks_ms()
        while self.button.state() == 1:
            utime.sleep_ms(100)
        if utime.ticks_diff(bstart_ms, utime.ticks_ms()) > 1000:
            self.reset()
        else:
            self.mqtt_publish(self.relay.toggle())

    def mqtt_subscribe_callback(self, topic, msg):
        topic = topic.decode('utf-8')
        msg = msg.decode('utf-8')
        print('[i] mqtt_subscribe_callback: {0} - {1}'.format(topic, msg))
        if msg == 'reset':
            self.reset()
        elif msg == 'blink':
            self.led.blink()
        elif msg == 'state':
            self.mqtt_publish(self.relay.state())
        else:
            self.mqtt_publish(self.relay.switch(msg))

    def mqtt_start(self, mqtt_broker, mqtt_client_id, mqtt_port=1883):
        self.mqtt_topic_in = str(self.wlan.get_hostname() + MQTT_TPIN).encode()
        self.mqtt_topic_out = str(self.wlan.get_hostname() + MQTT_TPOU).encode()
        try:
            self.mqtt = MQTTClient(mqtt_client_id, mqtt_broker, mqtt_port)
            self.mqtt.set_callback(self.mqtt_subscribe_callback)
            self.mqtt.connect(clean_session=False)
            print('[+] Sonoff.mqtt_start: Connected to ({0}'.format(str(mqtt_broker)))
        except KeyboardInterrupt:
            raise
        except Exception as e:
            eprint('[-] Sonoff.mqtt_setup: {0}'.format(e))
            eprint('    Failed to connect to MQTT, resetting..')
            self.reset()
        try:
            self.mqtt.subscribe(self.mqtt_topic_in)
            print('[+] Sonoff.mqtt_start: Subscribed to {0}'.format(self.mqtt_topic_in.decode('utf-8')))
        except KeyboardInterrupt:
            raise
        except Exception as e:
            eprint('[-] Sonoff.mqtt_setup: {0}'.format(e))
            eprint('    Failed to subscribe to {1}, resetting..'.format(self.mqtt_topic_in.decode('utf-8')))
            self.reset()
            self.led.blink(3)

    def mqtt_stop(self):
        self.mqtt.disconnect()

    def run(self):
        i = 0
        j = 0
        while True:
            i += 1
            try:
                self.mqtt.check_msg()
                self.relay.check()
                if i % 100 == 0:
                    print('[i] Sonoff.run: {0} - {1}'.format(self.mqtt_topic_out.decode('utf-8'), self.relay.state()))
                    self.mqtt_publish(self.relay.check())
                if i % 300 == 0:
                    if not self.wlan.isconnected():
                        self.wlan.connect(delay=WLAN_DLAY)
                        self.led.blink(3)
                    else:
                        self.led.blink(1, 300)
                if i % 36000 == 0:
                    gc.collect()
                utime.sleep_ms(100)

            except KeyboardInterrupt:
                raise

            except Exception as e:
                j += 1
                eprint('[-] Sonoff.run: {0}'.format(e))
                if j == 10:
                    eprint('[-] Resetting...')
                    self.reset()
                else:
                    eprint('[-] Running garbage collection...')
                    gc.collect()


s = Sonoff()
s.mqtt_start(MQTT_BRKR, s.wlan.get_hostname(), MQTT_PORT)
s.run()
