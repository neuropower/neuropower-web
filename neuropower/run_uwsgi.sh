#!/bin/bash
source activate crnenv
source /usr/share/fsl/5.0/etc/fslconf/fsl.sh
python manage.py makemigrations --merge --noinput
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py celeryd -l info
uwsgi uwsgi.ini
