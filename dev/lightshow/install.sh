#!/bin/bash
cp -f *.py ../../roles/lightshow/files/scripts
(cd ../.. && ansible-playbook -i hosts --extra-vars @secrets.yml lightshow.yml)
