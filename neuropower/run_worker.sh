#!/bin/bash
source activate crnenv
pip install redis
celery worker -A celeryNP -Q default -n default@%h --loglevel=info --maxtasksperchild=10
