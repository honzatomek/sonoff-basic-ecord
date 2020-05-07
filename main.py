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

C = {}       # controls
STA = None   # Network Station
MC = None    # MQTT Client
DELAY = 200  # main loop delay [ms]

SAVE = 'relay.save'

def load():
    global SAVE
    global REL
    try:
        with open(SAVE, 'r') as sfile:
            return int(sfile.read())
    except Exception as e:
        print(e)
        return Pin(REL['pin']).value()

def save():
    global SAVE
    global REL
    with open(SAVE, 'w') as sfile:
        sfile.write(Pin(REL['pin']).value())

def blink(count=1, delay=250):
    global C
    global LED
    C['LED'].value(LED['off'])
    for i in range(count * 2 - 1):
        C['LED'].value(not C['LED'].value())
        sleep_ms(delay)
    C['LED'].value(LED['off'])

def switch(value=2):
    global C
    global REL
    if value == 0:
        C['REL'].value(REL['off'])
    elif value == 1:
        C['REL'].value(REL['on'])
    elif value == 2:
        C['REL'].value(not C['REL'].value())
    else:
        C['REL'].value(REL['off'])
    REL['state'] = C['REL'].value()

def state():
    global C
    global REL
    return int(C['REL'].value() == REL['on'])

def reset():
    blink(1, 1500)
    save()
    __reset()

def button_press(pin=None):
    global C
    global BTN
    i = 0
    while C['BTN'].value() == BTN['on']:
        sleep_ms(100)
        i += 1
    if i < int(30):
        print('[+] button short press, switching.')
        switch(2)
    else:
        print('[-] button long press, resetting..')
        reset()

def check(t=None):
    global C
    global REL
    if C['REL'].value() != REL['state']:
        switch(2)

def connect(t=None):
    global STA
    if STA.isconnected():
        blink()
        return True
    try:
        STA.connect(SSID, PASS)
        for i in range(10):
            sleep_ms(500)
            if STA.isconnected():
                print('[+] WiFi connected to {0}. IP = {1}'.format(SSID, STA.ifconfig()[0]))
                blink(2, 200)
                mconnect()
                return True
    except Exception as e:
        print(e)
        print('[-] WiFi not connected to {0}. Retrying in 30 seconds.'.format(SSID))
        blink(2, 500)
        return False

def mconnect(do_blink=True):
    global MC
    global TOPI
    try:
        MC.connect()
        MC.subscribe(TOPI.encode())
        print('[+] Connected to MQTT Broker {0}, subscribed to topic {1}.'.format(MQTT, TOPI))
        if do_blink:
            blink(3, 200)
        return True
    except Exception as e:
        print(e)
        print('[-] Connection to MQTT Broker failed.')
        if do_blink:
            blink(3, 500)
        return False

def mqtt_callback(topic, msg):
    global MC
    global TOPO
    topic = topic.decode()
    msg = msg.decode()
    if msg == '0':
        switch(0)
    elif msg == '1':
        switch(1)
    elif msg == '2':
        switch(2)
    elif msg == 'blink':
        blink()
    elif msg == 'reset':
        reset()
    elif msg == 'state':
        pass
    else:
        return
    MC.publish(TOPO.encode(), str(state()).encode())


# assign controls
C.setdefault('REL', Pin(REL['pin'], Pin.OUT, value=load()))
C.setdefault('LED', Pin(LED['pin'], Pin.OUT, value=LED['off']))
C.setdefault('BTN', Pin(BTN['pin'], Pin.IN, value=BTN['off']))
REL['state'] = C['REL'].value()
blink(count=1, delay=100)
print('[+] Controls assigned.')

# set control callbacks
C['BTN'].irq(trigger=Pin.IRQ_FALLING, handler=button_press)
# t_check = Timer(0)
# t_check.init(period=500, mode=Timer.PERIODIC, callback=check)
print('[+] Control callbacks set.')

# connect to WiFi
network.WLAN(network.AP_IF).active(False)
STA = network.WLAN(network.STA_IF)
STA.active(True)
mac = hexlify(network.WLAN().config('mac'), ':').decode().replace(':', '')
HOST += mac[-4:]
STA.config(dhcp_hostname=HOST)
connect()
t_wifi = Timer(1)
t_wifi.init(period=5000, mode=Timer.PERIODIC, callback=connect)

# set up MQTT Client
MC = MQTTClient(HOST, MQTT, PORT)
TOPI = HOST + TOPI
TOPO = HOST + TOPO
MC.set_callback(mqtt_callback)
mconnect()

# main loop
for i in range(int(1000/DELAY) * 60 * 60 * 2):  # last only 2 hours, then reset
    try:
        sleep_ms(DELAY)
        check()
        if i % int(5000/DELAY) == 0:  # each 5 seconds
            MC.publish(TOPO.encode(), str(state()).encode())
        MC.check_msg()
    except Exception as e:
        print(e)
        connect()
        mconnect()

# reset when main loop ends
reset()
