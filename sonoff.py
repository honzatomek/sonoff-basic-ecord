from machine import Pin, Timer, reset
from utime import sleep_ms
from uos import listdir
from umqtt.robust import MQTTClient

_PIN_LED = const(13)
_PIN_BTN = const(0)
_PIN_REL = const(12)

_LED_ON = const(0)
_BTN_ON = const(0)
_REL_ON = const(1)

class SonoffException(Exception):
  pass

class Sonoff:
  def __init__(self):
    self.__led = Pin(_PIN_LED, Pin.OUT, value=(1-_LED_ON))
    self.__button = Pin(_PIN_BTN, Pin.IN)
    self.__relay = Pin(_PIN_REL, Pin.OUT, value=self.load())

    self.__mqtt = None
    self.__mqtt_topic_in = None
    self.__mqtt_topic_out = None

  def load(self, save_file='relay.save'):
    try:
      if save_file in listdir('/'):
        with open(save_file, 'r', encoding='utf-8') as save:
          return int(save.readline())
      else:
        return Pin(_PIN_REL).value()
    except Exception as e:
      print('[-] Sonoff.load: Exception occured\n    {0}'.format(e))
      return (1 - _REL_ON)

  def save(self, save_file='relay.save', value=0):
    try:
      with open(save_file, 'w', encoding='utf-8') as save:
        save.write(str(value))
      return True
    except Exception as e:
      print('[-] Sonoff.save: Exception occured\n    {0}'.format(e))
      return False

  def reset(self, save_state=True):
    if save_state:
      self.save(value=self.__relay.value())
    reset()

  def blink(self, count=1, delay=250):
    for i in range(count * 2 + 1):
      self.__led.value(abs(_LED_ON - i % 2))
      sleep_ms(delay)

  def switch(self, value=2):
    if value in [0, '0']:       # off
      self.__relay.value(1 - _REL_ON)
    elif value in [1, '1']:     # on
      self.__relay.value(_REL_ON)
    elif value in [2, '2']:     # toggle
      self.__relay.value(not self.__relay.value())
    # any other case just returns state
    if self.__relay.value() == _REL_ON:
      return 1
    else:
      return 0

  def mqtt_subscribe_callback(self, topic, msg):
    topic = topic.decode('utf-8')
    msg = msg.decode('utf-8')
    if msg == 'reset':
      self.reset()
    else:
      self.publish(str(self.switch(msg)).encode())

  def mqtt_setup(self, mqtt_broker, mqtt_client_id, mqtt_port=1883, topic_in='in', topic_out='out'):
    self.__mqtt_topic_in   = topic_in.encode()
    self.__mqtt_topic_out = topic_out.encode()
    try:
      self.__mqtt = MQTTClient(mqtt_client_id, mqtt_broker, mqtt_port)
      self.__mqtt.set_callback(self.mqtt_subscribe_callback)
      self.__mqtt.connect()
    except KeyboardInterrupt:
      raise
    except Exception as e:
      print('[-] Sonoff.mqtt_setup: {0}\n    Failed to connect to MQTT, resetting..'.format(e))
      self.reset()
    try:
      self.__mqtt.subscribe(self.__mqtt_topic_in)
    except KeyboardInterrupt:
      raise
    except Exception as e:
      print('[-] Sonoff.mqtt_setup: {0}\n    Failed to subscribe to {1}, resetting..'.format(e, self.__mqtt_topic_in.decode('utf-8')))
      self.reset()

  def mqtt_publish(self, message):
    if not self.__mqtt is None:
      try:
        self.__mqtt.publish(self.__mqtt_topic_out, message.encode())
      except KeyboardInterrupt:
        raise
      except Exception as e:
        print('[-] Sonoff.mqtt_publish: {0}\n    Failed MQTT publish, resetting..'.format(e))
        self.reset()
