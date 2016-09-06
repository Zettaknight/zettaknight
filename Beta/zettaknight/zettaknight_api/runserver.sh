#!/bin/bash

date_time=$(date)

echo -e  "\nZettaknight API server started at ${date_time}!\n"
python /home/rgoodbe/mysite/manage.py runserver 0.0.0.0:8000
