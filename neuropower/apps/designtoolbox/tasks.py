from django.conf import settings
from .models import DesignModel
from neurodesign import geneticalgorithm, generate, msequence, report
from .forms import DesignRunForm
from celery import task, Celery
import os
from utils import probs_and_cons
import numpy as np

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuropower.settings')
app = Celery('neuropower')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task
def GeneticAlgorithm(sid,ignore_result=False):
    desdata = DesignModel.objects.get(SID=sid)

    subject = "NeuroDesign: optimisation process started"
    sender = "NeuroDesign"
    sendermail = "joke.durnez@gmail.com"
    message = "Your design optimisation has now started.  You can follow the progress here:"+" http://development.neuropowertools.org/design/runGA/?retrieve="+str(desdata.shareID)+". Thank you for using NeuroDesign."
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
        folder=desdata.onsetsfolder,
        Aoptimality = True if desdata.Aoptimality == 1 else False,
        seed=seed
    )

    POP.print_cmd()
    desdata = DesignModel.objects.get(SID=sid)
    runform = DesignRunForm(None, instance=desdata)
    form = runform.save(commit=False)
    form.running = 1
    form.seed = seed
    form.cmd = POP.cmd
    form.save()

    POP.naturalselection()
    POP.download()

    # Select optimal design
    desdata = DesignModel.objects.get(SID=sid)
    runform = DesignRunForm(None, instance=desdata)
    form = runform.save(commit=False)
    form.convergence = POP.finished
    form.zip_filename = POP.zip_filename
    form.zipfile = POP.file
    print("popfile: "+POP.file)
    form.save()

    subject = "NeuroDesign: optimisation process ended"
    sender = "NeuroDesign"
    sendermail = "joke.durnez@gmail.com"
    message = "Your design optimisation has now ended.  You can download the results here:"+" http://development.neuropowertools.org/design/runGA/?retrieve="+str(desdata.SID)+". Thank you for using NeuroDesign."
    recipient = str(desdata.email)
    key = settings.MAILGUN_KEY

    command = "curl -s --user '" + key + "' https://api.mailgun.net/v3/neuropowertools.org/messages -F from='" + sender + \
        " <" + sendermail + ">' -F to=" + recipient + " -F subject="+subject+" -F text='" + message + "'"
    os.system(command)
