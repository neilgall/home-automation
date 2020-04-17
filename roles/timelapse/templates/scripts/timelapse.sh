#!/bin/bash

test -d {{nfs_mount_local}}/images || exit 1

cd /tmp
/opt/vc/bin/raspistill -o img%010d.jpg -w 640 -h 480 -dt
/bin/mv img*.jpg {{nfs_mount_local}}/images

