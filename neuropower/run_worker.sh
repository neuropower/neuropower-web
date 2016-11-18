#!/bin/bash
pip install redis
celery worker -A celeryNP -Q default -n default@%h --loglevel=info --maxtasksperchild=10
