#!/bin/bash

ping -c2 {{router_ip}} > /dev/null
 
if [ $? != 0 ]; then
	echo "Restarting wlan0"
	netctl restart wlan0-Forty-Eight
fi
