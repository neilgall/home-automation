#!/usr/bin/env python3
import requests
import logger

_log = logger.create("pushover", level=logger.INFO)

class Pushover:
    """
    Very simple Pushover client
    """
    @logger.log_with(_log)
    def __init__(self, user_key: str, api_token: str):
        self._user_key = user_key
        self._api_token = api_token

    @logger.log_with(_log)
    def send(self, title: str="", message: str="", url: str=None):
        """
        Send a notification with 'title', 'message' and optional URL
        """
        if not (self._user_key and self._api_token):
            return        

        rsp = requests.post('https://api.pushover.net/1/messages.json', params={
            'token': self._api_token,
            'user':  self._user_key,
            'title': title,
            'message': message,
            'sound': 'none',
            'url': url 
        })

        return rsp.json() if rsp.status_code < 300 else rsp.status_code

if __name__ == "__main__":
    import sys
    p = Pushover(sys.argv[1], sys.argv[2])
    p.send(*sys.argv[3:])
