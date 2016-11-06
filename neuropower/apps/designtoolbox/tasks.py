from django.conf import settings
from .models import DesignModel
from designcore import design
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
    elif desdata.ITImodel == 2:
        model = "truncated exponential"
    elif desdata.ITImodel == 3:
        model = "uniform"

    des = design.GeneticAlgorithm(
        # design specific
        ITImodel = model,
        ITIfixed = desdata.ITIfixed,
        ITIunifmin = desdata.ITIunifmin,
        ITIunifmax = desdata.ITIunifmax,
        ITItruncmin = desdata.ITItruncmin,
        ITItruncmax = desdata.ITItruncmax,
        ITItruncmean = desdata.ITItruncmean,
        TR=desdata.TR,
        n_trials=desdata.L,
        duration=desdata.duration,
        P=matrices["P"],
        C=matrices["C"],
        stim_duration=desdata.stim_duration,
        weights=desdata.W,
        ConfoundOrder=desdata.ConfoundOrder,
        MaxRepeat=desdata.MaxRepeat,
        restnum=desdata.RestNum,
        restlength=desdata.RestDur,
        # general/defaulted
        rho=desdata.rho,
        Aoptimality=True if desdata.Aoptimality == 1 else False,
        saturation=True if desdata.Saturation == 1 else False,
        resolution=desdata.resolution,
        G=desdata.G,
        q=desdata.q,
        I=desdata.I,
        cycles=desdata.cycles,
        preruncycles=desdata.preruncycles,
        HardProb=desdata.HardProb,
        tapsfile="/code/taps.p",
        write_score=desdata.genfile,
        write_design=desdata.desfile,
        convergence=desdata.conv_crit,
        folder=desdata.onsetsfolder
    )
    des.counter = 0

    desdata = DesignModel.objects.get(SID=sid)
    runform = DesignRunForm(None, instance=desdata)
    form = runform.save(commit=False)
    form.running = 1
    form.cmd = des.cmd
    form.save()

    # Create first generation
    des.GeneticAlgorithmInitiate()

    # Maximise Fe
    if des.weights[0] > 0 and des.preruncycles > 0:
        desdata = DesignModel.objects.get(SID=sid)
        runform = DesignRunForm(None, instance=desdata)
        form = runform.save(commit=False)
        form.running = 2
        form.save()
        des.prerun = 'Fe'
        des.GeneticAlgorithmNaturalSelection()
        des.FeMax = np.max(NatSel['Best'])

    # Maximise Fd
    if des.weights[1] > 0 and des.preruncycles > 0:
        desdata = DesignModel.objects.get(SID=sid)
        runform = DesignRunForm(None, instance=desdata)
        form = runform.save(commit=False)
        form.running = 3
        form.save()
        des.prerun = 'Fd'
        des.GeneticAlgorithmNaturalSelection()
        des.FdMax = np.max(NatSel['Best'])

    # Natural selection
    desdata = DesignModel.objects.get(SID=sid)
    runform = DesignRunForm(None, instance=desdata)
    form = runform.save(commit=False)
    form.running = 4
    form.save()
    des.prerun = None
    des.GeneticAlgorithmNaturalSelection()
    des.prepare_download()

    # Select optimal design
    OptInd = np.min(np.arange(len(Generation['F']))[
                    Generation['F'] == np.max(Generation['F'])])

    desdata = DesignModel.objects.get(SID=sid)
    runform = DesignRunForm(None, instance=desdata)
    form = runform.save(commit=False)
    form.convergence = des.conv
    form.zip_filename = des.zip_filename
    form.file = des.file
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
