#!/usr/bin/env python
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
from queue import Queue
from typing import Callable
import json
import logger
import time

logger.create("AWSIoTPythonSDK.core", logger.DEBUG)
_log = logger.create("iot_core_client", logger.INFO)

class IoTCoreClient:
    def __init__(self, client_id: str, root_ca_path: str, host: str, port: int=443):
        """
        Construct an IoT client

        client_id     -- an identifier for the client
        root_ca_path  -- path to the AWS root CA certificate
        host          -- endpoint host to connect to
        port          -- endpoint port to connect to
        """
        self._iot = AWSIoTMQTTShadowClient(client_id, useWebsocket=True)
        self._iot.configureEndpoint(host, port)
        self._iot.configureCredentials(root_ca_path)
        self._iot.configureAutoReconnectBackoffTime(1, 32, 20)
        self._iot.configureConnectDisconnectTimeout(10) 
        self._iot.configureMQTTOperationTimeout(5)
        self._iot.connect(keepAliveIntervalSecond=60)
        self._things = {}
        self._polls = []

    @logger.log_with(_log)
    def register_on_off_thing(self, thing_name: str, queue: Queue, on_event, off_event):
        """
        Register a Queue for a thing with on/off power state. Events will
        be posted to the queue to request changes in the device state.

        thing_name  -- name of thing in IoT core to monitor
        queue       -- a `Queue` to post events to
        on_event    -- event to post to turn on the device
        off_event   -- event to post to turn off the device
        """
        shadow = self._iot.createShadowHandlerWithName(thing_name, True)

        @logger.log_with(_log)
        def update_shadow(state):
            shadow.shadowUpdate(json.dumps({ "state": { "reported": { "state": state } } }), None, 5)

        @logger.log_with(_log)
        def on_delta(payload, response_status, token):
            state = json.loads(payload)["state"].get("state")
            if state is not None:
                update_shadow(state)
                queue.put(on_event if state == 'ON' else off_event)

        @logger.log_with(_log)
        def on_get(payload, response_status, token):
            state = json.loads(payload)['state']['desired']['state']
            if state in ['ON', 'OFF']:
                update_shadow(state)
                queue.put(on_event if state == 'ON' else off_event)

        shadow.shadowRegisterDeltaCallback(on_delta)
        shadow.shadowGet(on_get, 5)

        self._things[thing_name] = shadow
        

    @logger.log_with(_log)
    def register_poll_thing(self, queue: Queue, event):
        """
        Register a handler to be polled periodically.

        queue  -- a `Queue` to post events to
        event  -- the periodic event to be posted
        """
        @logger.log_with(_log)
        def on_poll():
            queue.put(event)

        self._polls.append(on_poll)


    @logger.log_with(_log)
    def start(self):
        """
        Enter the polling loop
        """
        try:
            while True:
                time.sleep(1)
                for p in self._polls:
                    p()

        except KeyboardInterrupt:
            pass
