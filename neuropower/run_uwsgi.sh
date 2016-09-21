#!/bin/bash
source activate crnenv
source /usr/share/fsl/5.0/etc/fslconf/fsl.sh
PATH=$PATH:/usr/lib/python2.7
export PATH
python manage.py makemigrations --merge --noinput
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py celeryd -l info
uwsgi uwsgi.ini
