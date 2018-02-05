import requests
import os
import shutil
import json
import boto3
from django.conf import settings
import xml.etree.cElementTree
os.environ['http_proxy']=''
import urllib
from django.http import HttpResponseRedirect
import numpy as np
from ..models import DesignModel
from .utils import *
import encodings.idna

def create_neurodesign_string(sid):
    desdata = DesignModel.objects.filter(SID=sid).last()

    matrices = probs_and_cons(desdata.SID)

    if desdata.ITImodel == 1:
        model = "fixed"
        ITImean = desdata.ITIfixed
        ITImin = 'None'
        ITImax = 'None'
    elif desdata.ITImodel == 2:
        model = "exponential"
        ITImean = desdata.ITItruncmean
        ITImin = desdata.ITItruncmin
        ITImax = desdata.ITItruncmax
    elif desdata.ITImodel == 3:
        model = "uniform"
        ITImin = desdata.ITIunifmin
        ITImax = desdata.ITIunifmax
        ITImean = (desdata.ITIunifmin+desdata.ITIunifmax)/2.

    if (desdata.MaxRepeat<4 and desdata.S<5) or desdata.S==2:
        R = [0,1,0]
    else:
        R = [0.4,0.4,0.2]

    neurodesign_string = "import os \n" + \
    "if 'TASK_UID' in os.environ.keys(): \n" + \
    "    import sys \n" + \
    "    sys.path.append('/usr/local/bin/') \n" + \
    "    import geneticalgorithm \n" + \
    "else: \n" + \
    "    from neurodesign import geneticalgorithm, generate, msequence \n" + \
    "EXP = geneticalgorithm.experiment( \n" + \
    "    TR = %s, \n " %desdata.TR + \
    "    n_trials = %s, \n " %desdata.L + \
    "    P = %s, \n " %matrices['P'].tolist() + \
    "    C = %s, \n " %matrices['C'].tolist() + \
    "    duration = %s, \n " %desdata.duration + \
    "    n_stimuli = %s, \n " %desdata.S + \
    "    rho = %s, \n " %desdata.rho + \
    "    resolution = %s, \n " %desdata.resolution + \
    "    stim_duration = %s, \n " %desdata.stim_duration + \
    "    restnum = %s, \n " %desdata.RestNum + \
    "    restdur = %s, \n " %desdata.RestDur + \
    "    ITImodel = '%s', \n " %model + \
    "    ITImin = %s, \n " %ITImin + \
    "    ITImean = %s, \n " %ITImean + \
    "    ITImax = %s, \n " %ITImax + \
    "    confoundorder = %s, \n " %desdata.ConfoundOrder + \
    "    maxrep = %s, \n " %desdata.MaxRepeat + \
    "    hardprob = %s, \n " %desdata.HardProb + \
    "    t_pre = %s, \n " %desdata.t_prestim + \
    "    t_post = %s, \n" %desdata.t_poststim + \
    ") \n \n" + \
    "seed = %s \n" %np.random.randint(10000) + \
    "POP = geneticalgorithm.population( \n" + \
    "    experiment = EXP, \n " + \
    "    G = %s, \n " %desdata.G + \
    "    R = %s, \n " %R + \
    "    q = %s, \n " %desdata.q + \
    "    weights = %s, \n " %desdata.W.tolist() + \
    "    I = %s, \n " %desdata.I + \
    "    preruncycles = %s, \n " %desdata.preruncycles + \
    "    cycles = %s, \n " %desdata.cycles + \
    "    convergence = %s, \n " %desdata.conv_crit + \
    "    folder = '/tmp', \n " + \
    "    outdes = %s, \n " %desdata.outdes + \
    "    Aoptimality = %s, \n " %(True if desdata.Aoptimality == 1 else False) + \
    "    seed = seed \n " + \
    ") \n \n" + \
    "POP.naturalselection() \n" + \
    "POP.download()"

    return neurodesign_string

def write_neurodesign_script(sid):
    ndstr = create_neurodesign_string(sid)
    S3filename = "%s.py"%sid
    filename = "/tmp/%s.py"%sid
    f = open(filename,'w')
    f.write(ndstr)
    f.close()
    push_to_s3(filename,S3filename)

def push_to_s3(filename,key):
    client = boto3.client('s3')
    client.upload_file(filename,settings.AWS_STORAGE_BUCKET_NAME,key)
    response = client.put_object_acl(ACL='public-read', Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=key)
    os.remove(filename)

def submit_batch(sid):
    desdata = DesignModel.objects.filter(SID=sid).last()
    client = boto3.client('batch')
    filename = "%s.py"%sid
    response = client.submit_job(
        jobName = "neurodesign_%s"%sid,
        jobQueue = 'neuropower',
        jobDefinition = os.environ.get("AWS_BATCH_JOB_DEFINITION"),
        containerOverrides={
            'command':["%s.py"%sid],
            'environment':[
                {"name":"BATCH_FILE_S3_URL",
                 "value":os.path.join("s3://",settings.AWS_STORAGE_BUCKET_NAME,filename)
                 },
                {"name":"BATCH_FILE_TYPE",
                 "value":"script"},
                {"name":"TASK_UID",
                 "value":sid},
                {"name":"AWS_ACCESS_KEY_ID",
                 "value":os.environ.get('AWS_ACCESS_KEY_ID')},
                {"name":"AWS_SECRET_ACCESS_KEY",
                 "value":os.environ.get('AWS_SECRET_ACCESS_KEY')},
                {"name":"AWS_STORAGE_BUCKET_NAME",
                 "value":os.environ.get('AWS_STORAGE_BUCKET_NAME')},
                {"name":"RDS_DB_NAME",
                 "value":os.environ.get('RDS_DB_NAME')},
                {"name":"RDS_USERNAME",
                 "value":os.environ.get('RDS_USERNAME')},
                {"name":"RDS_PASSWORD",
                 "value":os.environ.get('RDS_PASSWORD')},
                {"name":"RDS_HOSTNAME",
                 "value":os.environ.get('RDS_HOSTNAME')},
                {"name":"RDS_PORT",
                 "value":os.environ.get('RDS_PORT')},
                {"name":"OPBEAT_ORG",
                 "value":os.environ.get('OPBEAT_ORG')},
                {"name":"OPBEAT_APP_ID",
                 "value":os.environ.get('OPBEAT_APP_ID')},
                {"name":"OPBEAT_TOKEN",
                 "value":os.environ.get('OPBEAT_TOKEN')},
                {"name":"MAILGUN_KEY",
                 "value":os.environ.get('MAILGUN_KEY')},
                {"name":"DJANGO_KEY",
                 "value":os.environ.get('DJANGO_KEY')}
                ]
        }
    )
    return response['jobId']

def get_job_status(sid):
    desdata = DesignModel.objects.filter(SID=sid).last()
    client = boto3.client('batch')
    jobid = desdata.jobid
    descr = client.describe_jobs(jobs=[jobid])['jobs'][0]
    return descr

def stop_job(sid):
    desdata = DesignModel.objects.filter(SID=sid).last()
    client = boto3.client('batch')
    jobid = desdata.jobid
    client.terminate_job(jobId=jobid,reason="User cancelled job.")

def get_s3_url(key):
    client = boto3.client('s3',region_name=os.environ.get("AWS_S3_REGION"))
    url = os.path.join(client.meta.endpoint_url,settings.AWS_STORAGE_BUCKET_NAME,key)
    return url
