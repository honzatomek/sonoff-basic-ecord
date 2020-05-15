import network
import utime
from ubinascii import hexlify


class WLANException(Exception):
    pass


class WLAN:
    def __init__(self, ssid, password):
        self.__ssid = ssid
        self.__pass = password
        self.__access_point = network.WLAN(network.AP_IF)
        self.__station = network.WLAN(network.STA_IF)
        self.__station.active(True)
        self.__hostname = self.__station.config('dhcp_hostname')

    @staticmethod
    def mac_address():
        return hexlify(network.WLAN().config('mac'), ':').decode('utf-8')

    def set_hostname(self, prefix, mac_length=-4):
        mac_address = WLAN.mac_address().replace(':', '')
        if abs(mac_length) > len(mac_address):
            print('[-] WLAN.set_hostname: mac_length({0}) is longer '
                  'than mac_address({2}), using full lenght'.format(mac_length, mac_address))
            mac_length = len(mac_address)

        if mac_length < 0:
            hostname = prefix + mac_address[mac_length:]
        else:
            hostname = prefix + mac_address[:mac_length]
        self.__station.config(dhcp_hostname=hostname)
        self.__hostname = hostname
        return hostname

    def get_hostname(self):
        return self.__hostname

    def connect(self, delay=10000):
        self.__access_point.active(False)
        self.__station.active(True)
        cstart_ms = utime.ticks_ms()
        if not self.__station.isconnected():
            self.__station.connect(self.__ssid, self.__pass)
            while not self.__station.isconnected():
                if utime.ticks_diff(cstart_ms, utime.ticks_ms()) > delay:
                    raise WLANException('[-] WLAN.connect() timed out!')
                utime.sleep_ms(100)
        return True

    def isconnected(self):
        return self.__station.isconnected()

    def ip(self):
        return self.__station.ifconfig()[0]
