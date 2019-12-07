#!/bin/sh

export OMP_NUM_THREADS=20
export OMP_WAIT_POLICY=PASSIVE

uwsgi --master --single-interpreter --enable-threads --processes 4 --threads 2 --http :5000 --chdir src --module app:app --logto log/app.log
