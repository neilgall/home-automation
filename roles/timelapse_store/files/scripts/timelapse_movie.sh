#!/bin/bash
set -e

DIR=$1

if [ ! -d "${DIR}" ]; then
	echo "usage: $0 <directory>"
	exit 1
fi

cd ${DIR}

# runs after midnight so pick image files from day before
TODAY=`date --date yesterday +%m%d`
TODAY_LONG=`date --date yesterday "+%B %d"`

GLOB=img*.jpg
LIST=${TODAY}.txt

rm -f ${LIST}
for img in `ls ${GLOB}`; do
  echo "file '$img'" >>${LIST}
  echo "duration 0.25" >>${LIST}
done

/usr/bin/ffmpeg -f concat -i ${LIST} -c:v libx264 -pix_fmt yuv420p ${TODAY}.mp4
rm -f ${LIST} ${GLOB}

cp ${TODAY}.mp4 /var/www/media

/usr/local/bin/pushover.py \
	"Greenhouse" \
	"Greenhouse timelapse for ${TODAY_LOMG}" \
	https://neilgall.uk:41423/media/${TODAY}.mp4
