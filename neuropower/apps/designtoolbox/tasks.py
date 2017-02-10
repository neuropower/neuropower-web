from django.conf import settings
from .models import DesignModel
from neurodesign import geneticalgorithm, generate, msequence, report
from .forms import DesignRunForm
from celery import task, Celery
import os
import sys
from utils import probs_and_cons, push_to_s3
import numpy as np
from datetime import datetime
sys.path.append("/usr/local/miniconda/lib/python2.7/")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuropower.settings')
app = Celery('neuropower')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@app.task
def GeneticAlgorithm(sid,ignore_result=False):
    desdata = DesignModel.objects.get(SID=sid)

    subject = "NeuroDesign: optimisation process started"
    sender = "NeuroDesign"
    sendermail = "joke.durnez@gmail.com"
    message = "Your design optimisation has now started.  You can follow the progress here:"+" http://www.neuropowertools.org/design/runGA/?retrieve="+str(desdata.shareID)+". Thank you for using NeuroDesign."
    recipient = str(desdata.email)
    key = settings.MAILGUN_KEY

    command = "curl -s --user '" + key + "' https://api.mailgun.net/v3/neuropowertools.org/messages -F from='" + sender + \
        " <" + sendermail + ">' -F to=" + recipient + " -F subject="+subject+" -F text='" + message + "'"
    os.system(command)

    matrices = probs_and_cons(sid)

    if desdata.ITImodel == 1:
        model = "fixed"
        ITImean = desdata.ITIfixed
        ITImin = None
        ITImax = None
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

    EXP = geneticalgorithm.experiment(
        TR = desdata.TR,
        n_trials = desdata.L,
        P = matrices['P'],
        C = matrices['C'],
        duration = desdata.duration,
        n_stimuli = desdata.S,
        rho = desdata.rho,
        resolution = desdata.resolution,
        stim_duration = desdata.stim_duration,
        restnum = desdata.RestNum,
        restdur = desdata.RestDur,
        ITImodel = model,
        ITImin = ITImin,
        ITImean = ITImean,
        ITImax = ITImax,
        confoundorder = desdata.ConfoundOrder,
        maxrep = desdata.MaxRepeat,
        hardprob = desdata.HardProb,
        t_pre = desdata.t_prestim,
        t_post = desdata.t_poststim
    )

    seed = np.random.randint(10000)
    POP = geneticalgorithm.population(
        experiment = EXP,
        G = desdata.G,
        R = [0.4,0.4,0.2],
        q = desdata.q,
        weights = desdata.W,
        I = desdata.I,
        preruncycles = desdata.preruncycles,
        cycles = desdata.cycles,
        convergence=desdata.conv_crit,
        folder=desdata.onsets_folder,
        Aoptimality = True if desdata.Aoptimality == 1 else False,
        seed=seed
    )

    POP.print_cmd()
    desdata = DesignModel.objects.get(SID=sid)
    runform = DesignRunForm(None, instance=desdata)
    form = runform.save(commit=False)
    form.taskstatus = 2
    form.timestamp = str(datetime.now())
    form.timestart = str(datetime.now())
    form.running = 1
    form.seed = seed
    form.cmd = POP.cmd
    form.save()

    local_naturalselection(POP,sid)
    POP.download()
    desdata = DesignModel.objects.get(SID=sid)
    runform = DesignRunForm(None, instance=desdata)
    form = runform.save(commit=False)
    form.finished = True
    form.running = 0
    form.taskstatus = 3
    form.save()

    # list all files (with full path) for report
    infiles = [os.path.join(dp, f) for dp, dn, fn in os.walk(os.path.expanduser(desdata.onsets_folder)) for f in fn]
    # strip away /var/tmp --> design_suffix/xxx
    outfiles = [x[9:] for x in infiles]
    for file in range(len(infiles)):
        push_to_s3(infiles[file],"designs/"+outfiles[file])

    # Select optimal design
    desdata = DesignModel.objects.get(SID=sid)
    runform = DesignRunForm(None, instance=desdata)
    form = runform.save(commit=False)
    form.convergence = POP.finished
    form.files = outfiles
    form.save()

    subject = "NeuroDesign: optimisation process ended"
    sender = "NeuroDesign"
    sendermail = "joke.durnez@gmail.com"
    message = "Your design optimisation has now ended.  You can download the results here:"+" http://www.neuropowertools.org/design/runGA/?retrieve="+str(desdata.SID)+". Thank you for using NeuroDesign."
    recipient = str(desdata.email)
    key = settings.MAILGUN_KEY

    command = "curl -s --user '" + key + "' https://api.mailgun.net/v3/neuropowertools.org/messages -F from='" + sender + \
        " <" + sendermail + ">' -F to=" + recipient + " -F subject="+subject+" -F text='" + message + "'"
    os.system(command)

def local_naturalselection(POP,sid):
    '''
    Function to run natural selection for design optimization
    '''

    if (POP.exp.FcMax == 1 and POP.exp.FfMax==1):
        POP.max_eff()

    if POP.weights[0] > 0:
        desdata = DesignModel.objects.get(SID=sid)
        runform = DesignRunForm(None, instance=desdata)
        form = runform.save(commit=False)
        form.running = 2
        form.save()
        # add new designs
        POP.clear()
        POP.add_new_designs(weights=[1,0,0,0])
        # loop
        for generation in range(POP.preruncycles):
            POP.to_next_generation(seed=POP.seed,weights=[1,0,0,0])
            if generation % 10 == 10:
                print("optimisation for sid "+str(sid)+": generation "+str(generation))
                save_RDS(POP,sid,generation)
                desdata = DesignModel.objects.get(SID=sid)
                runform = DesignRunForm(None, instance=desdata)
                form = runform.save(commit=False)
                form.timestamp = str(datetime.now())
                form.generation = generation
                form.save()
            if POP.finished:
                continue
        POP.exp.FeMax = np.max(POP.bestdesign.F)

    if POP.weights[1] > 0:
        desdata = DesignModel.objects.get(SID=sid)
        runform = DesignRunForm(None, instance=desdata)
        form = runform.save(commit=False)
        form.running = 3
        form.metrics = ""
        form.bestdesign = ''
        form.save()
        POP.clear()
        POP.add_new_designs(weights=[0,1,0,0])
        # loop
        for generation in range(POP.preruncycles):
            POP.to_next_generation(seed=POP.seed,weights=[0,1,0,0])
            if generation % 10 == 0:
                print("optimisation for sid "+str(sid)+": generation "+str(generation))
                save_RDS(POP,sid,generation)
                desdata = DesignModel.objects.get(SID=sid)
                runform = DesignRunForm(None, instance=desdata)
                form = runform.save(commit=False)
                form.timestamp = str(datetime.now())
                form.generation = generation
                form.save()
            if POP.finished:
                continue
        POP.exp.FdMax = np.max(POP.bestdesign.F)

    # clear all attributes
    POP.clear()
    POP.add_new_designs()

    # loop
    desdata = DesignModel.objects.get(SID=sid)
    runform = DesignRunForm(None, instance=desdata)
    form = runform.save(commit=False)
    form.running = 4
    form.metrics = ""
    form.bestdesign = ''
    form.save()
    for generation in range(POP.cycles):
        POP.to_next_generation(seed=POP.seed)
        if generation % 10 == 0:
            print("optimisation for sid "+str(sid)+": generation "+str(generation))
            save_RDS(POP,sid,generation)
            desdata = DesignModel.objects.get(SID=sid)
            runform = DesignRunForm(None, instance=desdata)
            form = runform.save(commit=False)
            form.timestamp = str(datetime.now())
            form.generation = generation
            form.save()
        if POP.finished:
            continue

    return POP

def save_RDS(POP,sid,generation):
    try:
        desdata = DesignModel.objects.get(SID=sid)
    except OperationalError:
        return None

    # make metrics dictionary
    if not isinstance(desdata.metrics,dict):
        Out = {"FBest": [], 'FeBest': [], 'FfBest': [],'FcBest': [], 'FdBest': [], 'Gen': []}
    else:
        Out = desdata.metrics
    opt = [POP.bestdesign.F,POP.bestdesign.Fe,POP.bestdesign.Ff,POP.bestdesign.Fc,POP.bestdesign.Fd]
    k = 0
    for key in ['FBest','FeBest','FfBest','FcBest','FdBest']:
        Out[key].append(opt[k])
        k = k+1
    Out['Gen'].append(generation)

    # make bestdesign dictionary
    keys = ["Stimulus_"+str(i) for i in range(POP.exp.n_stimuli)]
    Seq = {}
    for s in keys:
        Seq.update({s:[]})
    for stim in range(POP.exp.n_stimuli):
        Seq["Stimulus_"+str(stim)]=POP.bestdesign.Xconv[:,stim].tolist()
    Seq.update({"tps":POP.bestdesign.experiment.r_tp.tolist()})
    runform = DesignRunForm(None, instance=desdata)
    form = runform.save(commit=False)
    form.metrics = Out
    form.bestdesign = Seq
    form.save()
