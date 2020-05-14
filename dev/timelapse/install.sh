#!/bin/bash
DEST=../../roles/timelapse_store/files/scripts

cp -f *.py $DEST
cp -f timelapse_movie.sh $DEST
(cd ../.. && ansible-playbook -i hosts --extra-vars @secrets.yml timelapse.yml)
