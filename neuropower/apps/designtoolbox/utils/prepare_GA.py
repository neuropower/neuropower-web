import requests
import os
import shutil
import json
from django.conf import settings
import encodings.idna

import boto3
import boto
os.environ['http_proxy']=''
import urllib
from django.conf import settings
from django.http import HttpResponseRedirect
import numpy as np
from ..models import DesignModel
from .utils import *

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
    "    import geneticalgorithm \n" + \
    "else: \n" + \
    "    from neurodesign import geneticalgorithm, generate, msequence \n" + \
    "from neurodesign import geneticalgorithm \n" + \
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
    # http://www.laurentluce.com/posts/upload-and-download-files-tofrom-amazon-s3-using-pythondjango/
    import boto
    from boto.s3.key import Key
    # set boto lib debug to critical
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    # connect to the bucket
    conn = boto.connect_s3(settings.AWS_ACCESS_KEY_ID,
                    settings.AWS_SECRET_ACCESS_KEY)
    bucket = conn.get_bucket(bucket_name)
    # go through each version of the file
    # create a key to keep track of our file in the storage
    k = Key(bucket)
    k.key = key
    k.set_contents_from_filename(filename)
    # we need to make it public so it can be accessed publicly
    # using a URL like http://s3.amazonaws.com/bucket_name/key
    k.make_public()
    # remove the file from the web server
    os.remove(filename)

def submit_batch(sid):
    client = boto3.client('batch')
    filename = "%s.py"%sid
    response = client.submit_job(
        jobName = "neurodesign_%s"%sid,
        jobQueue = 'neurodesign',
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
                 "value":settings.AWS_ACCESS_KEY_ID},
                {"name":"AWS_SECRET_ACCESS_KEY",
                 "value":settings.AWS_SECRET_ACCESS_KEY}
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
    client.terminate_job(jobId=jobid)

def get_s3_url(filename):
    conn = boto.connect_s3()
    bucket = conn.get_bucket(settings.AWS_STORAGE_BUCKET_NAME)
    s3_file_path = bucket.get_key(filename)
    url = s3_file_path.generate_url(expires_in=600)
    return url
