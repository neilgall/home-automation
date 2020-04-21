#!/bin/bash

MOUNT=$1
if [ ! -d "${MOUNT}" ]; then
	echo "usage: $0 <mount-point>"
	exit 1
fi

tmp=/var/lib/timelapse
mkdir -p ${tmp}
cd ${tmp}

/opt/vc/bin/raspistill \
	--output img%010d.jpg \
	--datetime \
	--width 1920 \
	--height 1080 \
	--exposure auto

mount ${MOUNT}
test -d ${MOUNT}/images || exit 1

/bin/mv img*.jpg ${MOUNT}/images
