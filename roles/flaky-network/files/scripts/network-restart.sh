#!/bin/bash

ping -c2 192.168.0.1 > /dev/null
 
if [ $? != 0 ]; then
	echo "Restarting wlan0"
	netctl restart wlan0-FortyEight
fi
