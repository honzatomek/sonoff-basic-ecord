import network
from utime import sleep_ms
from ubinascii import hexlify

TIMEOUT_MS = 3000
class WiFi:
    def __init__(self, ssid, password):
        self.__ssid = ssid
        self.__password = password
        self.__ap_if = network.WLAN(network.AP_IF)
        self.__sta_if = network.WLAN(network.STA_IF)
        self.__ap_if.active(False)
        self.__sta_if.active(True)
        self.__hostname = 'snf'

    def set_hostname(self, hostname, append_mac_len=4):
        if append_mac_len > 0:
            self.__hostname = hostname + self.mac().replace(':', '')[0:append_mac_len]
        elif append_mac_len < 0:
            self.__hostname = hostname + self.mac().replace(':', '')[append_mac_len:]
        else:
            self.__hostname = hostname
        self.__sta_if.config(dhcp_hostname=self.__hostname)

    def hostname(self):
        return self.__hostname

    def connect(self, timeout_ms=TIMEOUT_MS):
        self.__ap_if.active(False)
        self.__sta_if.active(True)
        print('[+] Connecting to network "{0}'.format(self.__ssid))
        self.__sta_if.connect(self.__ssid, self.__password)
        delay = 500
        for i in range(int(timeout_ms / delay)):
            sleep_ms(delay)
            if self.__sta_if.isconnected():
                print('[i] WiFi "{0}" connected. IP: {1}'.format(self.__ssid, self.ifconfig()[0]))
                return True
        raise Exception('[-] Problem connecting to {0}.'.format(self.__ssid))

    def disconnect(self):
        self.__sta_if.disconnect()

    def isconnected(self):
        return self.__sta_if.isconnected()

    def ifconfig(self):
        return self.__sta_if.ifconfig()

    def mac(self):
        return hexlify(network.WLAN().config('mac'), ':').decode()
