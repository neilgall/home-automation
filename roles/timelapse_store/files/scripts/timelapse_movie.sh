#!/bin/bash
set -e

DIR=$1

if [ ! -d "${DIR}" ]; then
	echo "usage: $0 <directory>"
	exit 1
fi

cd ${DIR}
TODAY=`date +%m%d`
GLOB=img${TODAY}*.jpg
LIST=${TODAY}.txt

rm -f ${LIST}
for img in `ls ${GLOB}`; do
  echo "file '$img'" >>${LIST}
  echo "duration 0.25" >>${LIST}
done

/usr/bin/ffmpeg -f concat -i ${LIST} -c:v libx264 ${TODAY}.mp4
rm -f ${LIST} ${GLOB}
