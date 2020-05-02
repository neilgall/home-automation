#!/bin/bash
# Partition the drive first
#  p1 = 100MB FAT boot
#  p2 = remainder of disk ext4

sudo mkfs.fat /dev/mmcblk0p1
sudo mkfs.ext4 /dev/mmcblk0p2

rm -rf root boot
mkdir -p root boot
sudo mount /dev/mmcblk0p1 boot
sudo mount /dev/mmcblk0p2 root

rm ArchLinuxARM-rpi-latest.tar.gz
wget http://os.archlinuxarm.org/os/ArchLinuxARM-rpi-latest.tar.gz
sudo bsdtar -xpf ArchLinuxARM-rpi-latest.tar.gz -C root
sudo mv root/boot/* boot
sync

sudo umount root boot

