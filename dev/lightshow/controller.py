
import logger
import threading
import time
from enum import Enum
from queue import Queue, Empty

try:
    import RPi.GPIO as gpio
    _using_fake_rpi = False

except ModuleNotFoundError:
    import fake_rpi, sys
    sys.modules['RPi'] = fake_rpi.RPi
    sys.modules['RPi.GPIO'] = fake_rpi.RPi.GPIO
    fake_rpi.toggle_print(True)
    _using_fake_rpi = True
    import RPi.GPIO as gpio


_log = logger.create("controller", logger.INFO)

_ZONES = {
    'garden-lights': {
        'friendly_name': 'Garden Fairy Lights',
        'description': 'Lights all around the garden',
        'control-pins': [14, 15, 25]
    },
    'summerhouse-lights': {
        'friendly_name': 'Summerhouse Lights',
        'description': 'Internal lights in the summerhouse',
        'control-pins': [24]    
    }
}

READY_PIN = 23
SWITCH_PIN = 17
ON_DELAY = 1.0

class Event(Enum):
    ON = "on"
    OFF = "off"
    POLL = "poll"
    EXIT = "exit"


class Lightshow(threading.Thread):
    def __init__(self, pushover):
        threading.Thread.__init__(self)

        self._pushover = pushover
        self.queue = Queue()

    def zones(self):
        return [{
            'name': zone,
            'on_event': (Event.ON, zone),
            'off_event': (Event.OFF, zone)
        } for zone in _ZONES]

    @logger.log_with(_log)
    def __enter__(self, *args):
        gpio.setwarnings(False)
        gpio.setmode(gpio.BCM)
        gpio.setup(READY_PIN, gpio.OUT)
        gpio.setup(SWITCH_PIN, gpio.IN, pull_up_down=gpio.PUD_UP)
        gpio.output(READY_PIN, gpio.HIGH)

        for zone in _ZONES.values():
            for pin in zone['control-pins']:
                gpio.setup(pin, gpio.OUT)
                gpio.output(pin, gpio.LOW)

        self.start()

    @logger.log_with(_log)
    def __exit__(self, *args):
        self.queue.put((Event.EXIT,))
        self.join()

        gpio.output(READY_PIN, gpio.LOW)
        for zone in _ZONES.values():
          for pin in zone['control-pins']:
            gpio.output(pin, gpio.LOW)
        gpio.cleanup()

    def run(self):
        _log.debug("Starting control thread")
        self._pushover.send(title='Lightshow', message='Controller started')

        self._switch_state = self._read_switch()
        self._lights_state = { zone: False for zone in _ZONES }

        while True:
            try:
                event, *args = self.queue.get(block=True)
                # _log.debug(f"handling event {event} {args}")

                if event == Event.EXIT:
                    break

                elif event == Event.ON:
                    self._lights_on(args[0])

                elif event == Event.OFF:
                    self._lights_off(args[0])

                elif event == Event.POLL:
                    switch = self._read_switch()
                    if switch != self._switch_state:
                      self._switch_state = switch
                      for zone in _ZONES:
                          self._toggle_lights(zone)

                else:
                    _log.error(f"unknown event {event}")

            except Exception as e:
                _log.error(f"unable to process event {event}: {e}")

    @logger.log_with(_log)
    def _lights_on(self, zone):
        if self._lights_state[zone]:
            return
        self._lights_state[zone] = True
        for pin in _ZONES[zone]['control-pins']:
            _log.debug(f"pin {pin} on")
            gpio.output(pin, gpio.HIGH)
            time.sleep(ON_DELAY)
        self._send_pushover(zone, True)

    @logger.log_with(_log)
    def _lights_off(self, zone):
        if not self._lights_state[zone]:
            return
        self._lights_state[zone] = False
        for pin in _ZONES[zone]['control-pins']:
            _log.debug(f"pin {pin} off")
            gpio.output(pin, gpio.LOW)
        self._send_pushover(zone, False)

    @logger.log_with(_log)
    def _toggle_lights(self, zone):
        if self._lights_state[zone]:
            self._lights_off(zone)
        else:
            self._lights_on(zone)

    @logger.log_with(_log)
    def _send_pushover(self, zone, state):
        self._pushover.send(
            title=_ZONES[zone]['friendly_name'],
            message=f'Lights {"on" if state else "off"}!'
        )

    # @logger.log_with(_log)
    def _read_switch(self):
        return not _using_fake_rpi and gpio.input(SWITCH_PIN) != 0
