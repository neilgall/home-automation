# Home Automation Ansible setup

Prerequisites:

Each Raspberry Pi must have [ArchLinuxArm](https://archlinuxarm.org/platforms/armv6/raspberry-pi) installed.

WiFi must be configured and enabled:
* `wifi-menu`
* `systemctl enable wlan0-<ssid>`

Install Python and sudo
* `pacman-key --init`
* `pacman-key --populate`
* `pacman -Sy python3 sudo`

Add `alarm` user to sudoers
* `visudo`
* Remove comment at start of group `wheel` line

