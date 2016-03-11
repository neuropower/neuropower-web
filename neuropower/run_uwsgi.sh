#!/bin/bash
python manage.py makemigrations
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py celeryd -l info
uwsgi uwsgi.ini
