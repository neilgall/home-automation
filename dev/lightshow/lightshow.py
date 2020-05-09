#!/bin/env python3
from iot_core_client import IoTCoreClient
from controller import Lightshow, Event
from pushover import Pushover


if __name__ == "__main__":
  iot = IoTCoreClient(
    client_id = 'lightshow',
    host = 'aa40w08kkflrp-ats.iot.eu-west-1.amazonaws.com',
    port = 443,
    root_ca_path = './root-CA.crt'
  )

  pushover = Pushover(
    user_key = os.environ.get("PUSHOVER_USER_KEY"),
    api_token = os.environ.get("PUSHOVER_API_TOKEN")
  )

  controller = Lightshow(pushover)

  for zone in controller.zones():
    iot.register_on_off_thing(
      queue = controller.queue,
      thing_name = zone['name'],
      on_event = zone['on_event'],
      off_event = zone['off_event']
    )

  iot.register_poll_thing(controller.queue, (Event.POLL,))

  with controller:
    iot.start()
