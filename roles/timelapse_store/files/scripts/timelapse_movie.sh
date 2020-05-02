#!/bin/bash
set -e

DIR=$1
WWW=/var/www/media
PYTHON=/usr/bin/python3

if [ ! -d "${DIR}" ]; then
	echo "usage: $0 <directory>"
	exit 1
fi

# runs after midnight so pick image files from day before
TODAY=`date --date yesterday +%m%d`
TODAY_LONG=`date --date yesterday "+%B %d"`

GLOB=${DIR}/img*.jpg
LIST=/tmp/${TODAY}.txt

${PYTHON} overlay_pirrigator_data.py \
	--pirrigator http://pirrigator:5000/api \
	--index ${LIST} \
	${GLOB}

/usr/bin/ffmpeg \
	-f concat \
	-safe 0 \
	-i ${LIST} \
	-c:v libx264 \
	-pix_fmt yuv420p \
	-movflags faststart \
	${WWW}/${TODAY}.mp4

rm -f ${LIST} ${GLOB} *.png

cat <<EOF >${WWW}/${TODAY}.html
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <link href="timelapse.css" rel="stylesheet" type="text/css" media="all">
    <style>
body { 
  margin: 0;
}

video {
    width: 100%;
    height: auto;
    max-width: 100%;
    max-height: 100%;
    box-sizing: border-box;
}

.video-container {
    position: absolute;
    top: 0;
    left: 0;
    bottom: 0;
    right: 0;
    z-index:999;
}
    </style>
  </head>
  <body>
    <div class="video-container">
      <video src="${TODAY}.mp4" controls>
        Your browser does not support HTML5 video
      </video>"
    </div>
  </body>
</html>
EOF

${PYTHON} pushover.py \
	"Greenhouse" \
	"Greenhouse timelapse for ${TODAY_LONG}" \
	https://neilgall.uk:41423/media/${TODAY}.html
