#!/bin/bash
python manage.py makemigrations --noinput
python manage.py migrate --noinput
python manage.py collectstatic --noinput
uwsgi uwsgi.ini
