import machine
import network
from utime import sleep_ms

router_connect = network.WLAN(network.STA_IF)
router_connect.active(True)
router_connect.config(dhcp_hostname='sonoffb_' + router_connect.config('mac')[-4:])
router_connect.connect('<my_ssid>', '<my_wifi_password>')

for t in range(5):
    print('checking connection to WiFi')
    sleep_ms(t * 20)
    if router_connect.isconnected():
        print('WiFi connected.')
        # GPIO13 = LED Pin
        p = machine.Pin(13, machine.Pin.OUT, value=1)
        # blink 3 times
        for i in range(6):
            p.value(not p.value())
            sleep_ms(500)
        break

