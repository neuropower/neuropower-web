#!/bin/bash
source activate crnenv
pip install redis
celery worker -A celeryNP -Q default -n default@%h --maxtasksperchild=10
