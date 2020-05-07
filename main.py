from machine import Pin, Timer
from machine import reset as __reset
import network
from umqtt.simple import MQTTClient
from utime import sleep_ms
from ubinascii import hexlify
from uos import listdir

HOST = 'snf'

SSID = 'honza+eliska'
PASS = 'nwuwoceww'

MQTT = '192.168.1.4'
PORT = 1883
TOPI = '/in'
TOPO = '/out'

LED = {'pin': 13, 'on': 0, 'off': 1}
BTN = {'pin': 0, 'on': 0, 'off': 1}
REL = {'pin': 12, 'on': 1, 'off': 0, 'state': None}

C = {} # controls

SAVE = 'relay.save'

def load():
    if SAVE in listdir():
        with open(SAVE, 'r') as sfile:
            return int(sfile.readline())
    else:
        return Pin(REL['pin']).value()

def save():
    with open(SAVE, 'w') as sfile:
        sfile.write(Pin(REL['pin']).value())

def blink(count=1, delay=250):
    if 'LED' in C.keys():
        led = C['LED']
    else:
        led = Pin(LED['pin'], value=Pin(LED['pin']).value())
    led.value(LED['off'])
    for i in range(count * 2 - 1):
        led.value(not led.value())
        sleep_ms(delay)
    led.value(LED['off'])

def switch(value=2):
    if 'REL' in C.keys():
        C['REL'] = C['REL']
    else:
        C['REL'] = Pin(REL['pin'], value=Pin(REL['pin']).value())
    if value == 0:
        C['REL'].value(REL['off'])
    elif value == 1:
        C['REL'].value(REL['on'])
    elif value == 2:
        C['REL'].value(not C['REL'].value())
    else:
        C['REL'].value(REL['off'])
    REL['state'] = C['REL'].value()

def reset():
    blink(1, 1500)
    save()
    __reset()

def button_press(pin=None):
    i = 0
    while C['BTN'].value() == BTN['on']:
        sleep_ms(100)
        i += 1
    if i < int(30):
        print('[+] button short press, switching.')
        switch()
    else:
        print('[-] button long press, resetting..')
        reset()

def check(t=None):
    if C['REL'].value() != REL['state']
        switch()

def connect(sta_if):
    if not sta_if.isconnected():
        try:
            sta_if.connect(SSID, PASS)
            for i in range(10):
                sleep_ms(500)
                if sta_if.isconnected():
                    print('[+] WiFi connected to {0}. IP = {1}'.format(SSID, sta_if.ifconfig()[0]))
                    return True
        except:
            pass
    print('[-] WiFi not connected to {0}. Retrying in 30 seconds.'.format(SSID))
    return False

def sonoff():
    # assign controls
    C.setdefault('REL', Pin(REL['pin'], value=load()))
    C.setdefault('LED', Pin(LED['pin'], value=LED['off']))
    C.setdefault('BTN', Pin(BTN['pin'], value=BTN['off']))
    REL['state'] = C[REL].value())
    blink(count=1, delay=100)
    print('[+] Controls assigned.')

    # set control callbacks
    C['BTN'].irq(trigger=Pin.IRQ_FALLING, handler=button_press)
    t_check = Timer(0)
    t_check.init(period=250, mode=Timer.PERIODIC, callback=check)
    print('[+] Control callbacks set.')

    # connect to WiFi
    network.WLAN(network.AP_IF).active(False)
    sta = network.WLAN(network.STA_IF).active(True)
    mac = hexlify(network.WLAN().config('mac'), ':').decode().replace(':', '')
    HOST += mac[4:]
    sta.config(dhcp_hostname=HOST)
    connect(sta)
    t_wifi = Timer(1)
    t_wifi.init(period=30000, mode=Timer.PERIODIC, callback=connect)


if __name__ == '__main__':
    sonoff()
