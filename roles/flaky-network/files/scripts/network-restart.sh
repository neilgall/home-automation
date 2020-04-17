#!/bin/bash

ping -c2 192.168.0.1 > /dev/null
 
if [ $? != 0 ]; then
	echo "Restarting wlan0"
	nmcli device disconnect wlan0
	sleep 5
	nmcli device connect wlan0
fi
