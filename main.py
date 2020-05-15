import machine
import utime
from wlan import WLAN, WLANException
from config import WLAN_SSID, WLAN_PASS, WLAN_HOST, WLAN_RTRY, WLAN_DLAY

# uncomment if not located in boot.py for webrepl access, the access needs to
# be set up previously
# import webrepl
# webrepl.start()

# store button state (0 = pressed, 1 = not pressed)
button_pressed = (machine.Pin(0, machine.Pin.IN).value() == 0)

# connect to wifi
wlan = WLAN(WLAN_SSID, WLAN_PASS)
wlan.set_hostname(WLAN_HOST)
i = 1
while i < WLAN_RTRY:
    i += 1
    try:
        if wlan.connect(delay=WLAN_DLAY):
            print('[+] WLAN connected to {0} as {1}.'.format(WLAN_SSID, wlan.ip()))
        # blink 3 times to indicate wifi connected
        for i in range(3 * 2 + 1):
            machine.Pin(13).value(i % 2)
            utime.sleep_ms(250)
        break
    except WLANException as e:
        print('[-] Main: {0}'.format(e))
        print('[-] WLAN connection {0} to {1} not successful..'.format(i, WLAN_SSID))
    except Exception as e:
        print('[-] Unhandled Exception occured:\n{0}\n[-] Resetting!'.format(e))
        machine.reset()

# check if button was pressed upon boot
if not button_pressed:
    print('[+] Starting Sonoff Switch program..')
    try:
        import sonoff
    except KeyboardInterrupt as e:
        print('[i] Code run interrupted.')
    except Exception as e:
        print('[-] Unhandled Exception occured:\n{0}\n[-] Resetting!'.format(e))
        machine.reset()
else:
    print('[i] Button pressed upon boot.')

print('[i] Entering REPL mode..')
