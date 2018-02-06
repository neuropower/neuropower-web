import django
import sys
import os
sys.path.append('/tmp/neuropower-web/neuropower')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.settings'
django.setup()

from neurodesign import geneticalgorithm, generate, msequence, report
from sqlalchemy.exc import OperationalError, DatabaseError
from django.core.exceptions import ObjectDoesNotExist
from apps.designtoolbox.forms import DesignRunForm
from apps.designtoolbox.models import DesignModel
from django.conf import settings
from celery import task, Celery
from datetime import datetime
import numpy as np

class design(geneticalgorithm.design):
    def no_func():
        return 0

class experiment(geneticalgorithm.experiment):
    def no_func():
        return 0

class population(geneticalgorithm.population):
    def naturalselection(POP):
        sid = os.environ['TASK_UID']
        desdata = DesignModel.objects.filter(SID=sid).first()
        runform = DesignRunForm(None, instance=desdata)
        # send email
        subject = "NeuroDesign: optimisation process started"
        sender = "NeuroDesign"
        sendermail = "joke.durnez@gmail.com"
        message = "Your design optimisation has now started.  You can follow the progress here:"+" http://www.neuropowertools.org/design/runGA/?retrieve="+str(desdata.shareID)+". Thank you for using NeuroDesign."
        recipient = str(desdata.email)
        key = settings.MAILGUN_KEY
        command = "curl -s --user '" + key + "' https://api.mailgun.net/v3/neuropowertools.org/messages -F from='" + sender + \
            " <" + sendermail + ">' -F to=" + recipient + " -F subject="+subject+" -F text='" + message + "'"
        os.system(command)

        sid = os.environ.get('TASK_UID')
        '''
        Function to run natural selection for design optimization
        '''

        if (POP.exp.FcMax == 1 and POP.exp.FfMax==1):
            POP.max_eff()

        if POP.weights[0] > 0:
            desdata = DesignModel.objects.filter(SID=sid).first()
            runform = DesignRunForm(None, instance=desdata)
            form = runform.save(commit=False)
            form.running = 2
            form.save()
            # add new designs
            POP.clear()
            POP.add_new_designs(weights=[1,0,0,0])
            # loop
            for generation in range(POP.preruncycles):
                print("prerun1 for sid "+str(sid)+": generation "+str(generation))
                POP.to_next_generation(seed=POP.seed,weights=[1,0,0,0])
                if generation % 10 == 10:
                    save_RDS(POP,sid,generation)
                    desdata = DesignModel.objects.filter(SID=sid).first()
                    runform = DesignRunForm(None, instance=desdata)
                    form = runform.save(commit=False)
                    form.timestamp = str(datetime.now())
                    form.generation = generation
                    form.save()
                if POP.finished:
                    continue
            POP.exp.FeMax = np.max(POP.bestdesign.F)

        if POP.weights[1] > 0:
            desdata = DesignModel.objects.filter(SID=sid).first()
            runform = DesignRunForm(None, instance=desdata)
            form = runform.save(commit=False)
            form.running = 3
            form.metrics = ""
            form.bestdesign = ''
            form.save()
            POP.clear()
            print("adding new designs...")
            POP.add_new_designs(weights=[0,1,0,0])
            # loop
            for generation in range(POP.preruncycles):
                print("prerun2 for sid "+str(sid)+": generation "+str(generation))
                POP.to_next_generation(seed=POP.seed,weights=[0,1,0,0])
                if generation % 10 == 0:
                    save_RDS(POP,sid,generation)
                    desdata = DesignModel.objects.filter(SID=sid).first()
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
        desdata = DesignModel.objects.filter(SID=sid).first()
        runform = DesignRunForm(None, instance=desdata)
        form = runform.save(commit=False)
        form.running = 4
        form.metrics = ""
        form.bestdesign = ''
        form.save()
        for generation in range(POP.cycles):
            POP.to_next_generation(seed=POP.seed)
            print("optimisation for sid "+str(sid)+": generation "+str(generation))
            if generation % 10 == 0:
                save_RDS(POP,sid,generation)
                desdata = DesignModel.objects.filter(SID=sid).first()
                runform = DesignRunForm(None, instance=desdata)
                form = runform.save(commit=False)
                form.timestamp = str(datetime.now())
                form.generation = generation
                form.save()
            if POP.finished:
                continue

        return POP

def save_RDS(POP,sid,generation):
    desdata = None
    tries = 0
    while desdata == None or tries < 5:
        tries += 1
        try:
            desdata = DesignModel.objects.filter(SID=sid).first()
        except OperationalError or ObjectDoesNotExist or DatabaseError:
            return None

    # make metrics dictionary
    if not desdata == None:
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
