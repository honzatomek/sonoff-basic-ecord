from machine import Pin, reset
from time import sleep_ms

SAVE_FILE = 'relay.save'
TIMEOUT_MS = 3000

class Sonoff:
    def __init__(self, led=13, btn=0, rly=12, l_on=0, b_press=0, r_on=1):
        self.__led_on = l_on
        self.led = Pin(led, Pin.OUT, value=(1-l_on))
        self.__btn_press = b_press
        self.btn = Pin(btn, Pin.IN)
        self.__rly_on = r_on
        self.rly = Pin(rly, Pin.OUT, value=Pin(rly).value())
        self.r_val = self.rly.value()
        self.btn.irq(trigger=Pin.IRQ_FALLING, handler=self.button_press)
        self.topic = ''
        self.mqtt_publish = None

    def blink(self, count=1, blink_ms=250):
        self.led.value(1 - self.__led_on)
        for i in range(2 * count - 1):
            self.led.value(not self.led.value())
            sleep_ms(blink_ms)
        self.led.value(1 - self.__led_on)

    def reset(self):
        self.save()
        self.blink(1, 1500)
        reset()

    def button_press(self, pin=None):
        i = 0
        while self.btn.value() == self.__btn_press:
            sleep_ms(100)
            i += 1
        if i < int(TIMEOUT_MS / 100):
            print('[+] button short press, switching.')
            self.switch()
        else:
            print('[-] button long press, resetting..')
            self.reset()

    def check_relay(self, tim=None):
        if self.rly.value() != self.r_val:
            self.switch(int(self.r_val == self.__rly_on))

    def state(self):
        return int(self.rly.value() == self.__rly_on)

    def switch(self, value=None):
        if value == 0:
            self.rly.value(1 - self.__rly_on)
        elif value == 1:
            self.rly.value(self.__rly_on)
        else:
            self.rly.value(not self.rly.value())
        self.r_val = self.rly.value()
        if self.mqtt_publish is not None:
            self.mqtt_publish(self.topic, str(self.state()).encode())

    def save(self, value=None):
        if value is None:
            value = int(self.rly.value() == self.__rly_on)
        with open(SAVE_FILE, 'w') as sf:
            sf.write(str(value))

    def load(self):
        try:
            with open(SAVE_FILE, 'r') as sf:
                value = int(sf.readline().strip('\n'))
        except Exception as e:
            print(e)
            value = 1
        self.switch(value)

    def set_mqtt(self, topic, mqtt_publish=None):
        if mqtt_publish is not None:
            self.topic = topic
            self.mqtt_publish = mqtt_publish
