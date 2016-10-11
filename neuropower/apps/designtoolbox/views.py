from __future__ import unicode_literals
import sys
sys.path = sys.path[1:]
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, render_to_response
from django.core.mail import send_mail
from django.conf import settings
from scipy.stats import norm, t
import os
from django.contrib.sessions.backends.db import SessionStore
from utils import get_session_id, probs_and_cons, get_design_steps, weights_html, combine_nested, prepare_download
from .forms import DesignMainForm, DesignConsForm, DesignReviewForm, DesignWeightsForm, DesignProbsForm, DesignOptionsForm, DesignRunForm, DesignDownloadForm, ContactForm, DesignNestedForm,DesignNestedConsForm, DesignSureForm, DesignMailForm
from .models import DesignModel
from .tasks import GeneticAlgorithm
from designcore import design
import numpy as np
import time
import json
import pandas as pd
import csv
import zipfile
import StringIO
import shutil
import urllib2
from celery import task
from celery.task.control import revoke, inspect
from celery.result import AsyncResult


def end_session(request):
    # Get the session ID and database entry

    sid = get_session_id(request)

    '''ends a session so the user can start a new one.'''
    try:
        desdata = DesignModel.objects.get(SID=sid)
        revoke(desdata.taskID,terminate=True,signal='KILL')
    except KeyError:
        pass
    try:
        request.session.flush()
    except KeyError:
        pass
    try:
        DesignModel.objects.filter(SID=sid).delete()
    except KeyError:
        pass
    return maininput(request, end_session=True)


def DFAQ(request):
    return render(request, "design/DFAQ.html", {})


def tutorial(request):
    return render(request, "design/tutorial.html", {})


def methods(request):
    return render(request, "design/methods.html", {})


def start(request):

    # Get the template/step status

    template = "design/start.html"
    context = {}

    # Get the session ID and database entry

    sid = get_session_id(request)
    context["steps"] = get_design_steps(template, sid)

    # initiate

    fbform = ContactForm(request.POST or None)
    context["form"] = fbform

    if request.method == "POST":
        if fbform.is_valid():
            subject = "feedback neurodesign"
            sender = fbform.cleaned_data['contact_name']
            sendermail = fbform.cleaned_data['contact_email']
            message = fbform.cleaned_data['content']
            recipient = ['joke.durnez@gmail.com']
            key = settings.MAILGUN_KEY

            command = "curl -s --user '" + key + "' https://api.mailgun.net/v3/neuropowertools.org/messages -F from='" + sender + \
                " <" + sendermail + ">' -F to='joke.durnez@gmail.com' -F subject='design toolbox feedback' -F text='" + message + "'"
            os.system(command)

            context['thanks'] = True

    return render(request, template, context)


def maininput(request, end_session=False):

    # Get the template/step status

    template = "design/input.html"
    context = {}

    # Get the session ID and database entry

    sid = get_session_id(request)
    context["steps"] = get_design_steps(template, sid)

    try:
        desdata = DesignModel.objects.get(SID=sid)
    except DesignModel.DoesNotExist:
        desdata = None

    # Define form

    inputform = DesignMainForm(request.POST or None, instance=desdata)

    if end_session == True:
        context["message"] = "Session has been successfully reset."

    # If page was not result of POST or not valid: show form with db entries
    # Else: go to next page

    if not request.method == "POST" or not inputform.is_valid():
        context["inputform"] = inputform
        return render(request, template, context)

    else:

        # initial save

        form = inputform.save(commit=False)
        form.shareID = sid
        form.SID = sid
        form.mainpars = True
        form.desfile = os.path.join(settings.MEDIA_ROOT, "designs",
                            "design_" + str(sid) + ".json")
        form.genfile = os.path.join(settings.MEDIA_ROOT, "designs",
                            "generation_" + str(sid) + ".json")
        form.onsetsfolder = os.path.join(settings.MEDIA_ROOT, "designonsets", str(sid))

        form.save()

        # get data and change parameters

        desdata = DesignModel.objects.get(SID=sid)
        weightsform = DesignWeightsForm(None, instance=desdata)
        weightsform = weightsform.save(commit=False)
        W = np.array([desdata.W1, desdata.W2, desdata.W3, desdata.W4])
        if np.sum(W) != 1:
            W = W / np.sum(W)
        weightsform.W = W

        if not desdata.TR%desdata.resolution == 0:
            resfact = np.ceil(desdata.TR/desdata.resolution)
            weightsform.resolution = desdata.TR/resfact

        # get ITI's streight
        if not (desdata.ITImin or desdata.ITImax):
            weightsform.ITImin = desdata.ITImean
            weightsform.ITImax = desdata.ITImean
        if not desdata.ITImean:
            weightsform.ITImean = (desdata.ITImin+desdata.ITImax)/2
        weightsform.save()

        if desdata.nested and desdata.nest_classes == None:
            context['message'] = "For a nested design, please specify the number of classes."
            context["inputform"] = inputform
            return render(request, "design/input.html", context)

        if desdata.nested:
            return HttpResponseRedirect('../nested/')
        else:
            return HttpResponseRedirect('../consinput/')


def nested(request):

    # Get the template/step status

    template = "design/nested.html"
    context = {}

    # Get the session ID and database entry

    sid = get_session_id(request)
    context["steps"] = get_design_steps(template, sid)

    try:
        desdata = DesignModel.objects.get(SID=sid)
    except DesignModel.DoesNotExist:
        return HttpResponseRedirect('../maininput/')

    # Define form

    nestedform = DesignNestedForm(
        request.POST or None, instance=desdata, stim=desdata.S)
    inputform = DesignMainForm(request.POST or None, instance=desdata)

    # If page was result of POST or not valid: show form with db entries
    # Else: go to next page

    if not request.method == "POST" or not nestedform.is_valid():
        context["nestedform"] = nestedform
        return render(request, template, context)
    else:
        form = nestedform.save(commit=False)
        form.SID = sid
        form.nestpars = True
        form.save()

        # get data and change parameters

        matrices = combine_nested(sid)
        if matrices['empty'] == True:
            context['message'] = "Please fill out all stimuli"
            context["nestedform"] = DesignNestedForm(
                request.POST or None, instance=desdata, stim=desdata.S)
            return render(request, "design/nested.html", context)
        if np.max(matrices['G']) > desdata.nest_classes:
            context['message'] = "There are more classes than was specified in the previous screen."
            context["nestedform"] = DesignNestedForm(
                request.POST or None, instance=desdata, stim=desdata.S)
            return render(request, "design/nested.html", context)


        form.nest_structure = matrices['G']
        form.save()

        return HttpResponseRedirect('../consinput/')



def consinput(request):

    # Get the template/step status

    template = "design/cons.html"
    context = {}

    # Get the session ID and database entry

    sid = get_session_id(request)
    context["steps"] = get_design_steps(template, sid)

    try:
        desdata = DesignModel.objects.get(SID=sid)
    except DesignModel.DoesNotExist:
        return HttpResponseRedirect('../maininput/')

    # Define form

    # If page was result of POST or not valid: show form with db entries
    # Else: go to next page

    if desdata.nested == True:
        a = np.array(['P0','P1','P2','P3','P4','P5','P6','P7','P8','P9'])
        b = np.array(desdata.nest_structure)
        Pmat = [a[b==(i+1)].tolist() for i in xrange(desdata.nest_classes)]
        consform = DesignNestedConsForm(
            request.POST or None, instance=desdata, stim=desdata.S, cons=desdata.Clen, structure=Pmat, classes=desdata.nest_structure)
    else:
        consform = DesignConsForm(
            request.POST or None, instance=desdata, stim=desdata.S, cons=desdata.Clen)

    if not request.method == "POST":
        context["consform"] = consform
        return render(request, template, context)
    else:
        form = consform.save(commit=False)
        form.SID = sid
        form.conpars = True
        form.save()

        # get data and change parameters

        consform = DesignProbsForm(None, instance=desdata)
        consform = consform.save(commit=False)
        matrices = probs_and_cons(sid)
        if matrices['empty'] == True:
            context['message'] = "Please fill out all probabilities and contrasts"
            context["consform"] = DesignConsForm(
                request.POST or None, instance=desdata, stim=desdata.S, cons=desdata.Clen)
            return render(request, "design/cons.html", context)
        consform.P = matrices['P']
        consform.C = matrices['C']
        if desdata.HardProb == True:
            consform.G = 200
            consform.I = 100
        consform.save()

        return HttpResponseRedirect('../review/')


def review(request):

    # Get the template/step status

    template = "design/review.html"
    context = {}

    # Get the session ID and database entry

    sid = get_session_id(request)
    context["steps"] = get_design_steps(template, sid)

    try:
        desdata = DesignModel.objects.get(SID=sid)
    except DesignModel.DoesNotExist:
        return HttpResponseRedirect('../maininput/')

    # Define form

    revform = DesignReviewForm(request.POST or None, instance=desdata)
    context["revform"] = revform

    # Set summary variables in context

    matrices = probs_and_cons(sid)
    context['ITImin'] = desdata.ITImin
    context['ITImean'] = desdata.ITImean
    context['ITImax'] = desdata.ITImax
    context['TR'] = desdata.TR
    context['S'] = desdata.S
    context['L'] = desdata.L
    context["Phtml"] = matrices["Phtml"]
    context["Chtml"] = matrices["Chtml"]
    context["Whtml"] = weights_html(desdata.W)
    context["order"] = desdata.ConfoundOrder
    context["repeat"] = desdata.MaxRepeat

    context["message"] = ""
    if desdata.HardProb == True:
        context["message"] = context["message"] + \
            "<br><p><b>Warning:</b> Because of the hard limit on the frequencies, we increased the size of the generation and the number of random designs per generation.  This might slow down the optimisation.  </p>"
    if desdata.MaxRepeat < 10 and desdata.S == 2:
        context["message"] = context["message"] + "<br><p><b>Warning:</b> With only 2 stimuli, many random designs have repetitions larger dan " + \
            str(desdata.MaxRepeat) + \
            ".  We increased the number of random designs per generation, but this might slow down the optimisation.  </p>"
    if desdata.S>5 and desdata.L>200 and desdata.ITImax>3 and (desdata.Restnum<30 and desdata.Resdur>30) and desdata.C.shape[0]>5:
        context['message'] = context['message']+"<br><p><b>Warning:</b>This is a long and complex design.  Be aware that the optimisation will take a <b>long</b> time.</p>"

    # Duration
    dur = desdata.ITImean*desdata.L+desdata.RestNum*desdata.RestDur
    if dur > 1800:
        context['message'] = context['message'] + "<p><b>Warning:</b> The run you request is longer dan 30 minutes.  This optimisation will take <b>a long</b> time.  You could set the resolution lower, or split the experiment in multiple shorter runs.  Or you could grab a coffee and wait a few hours for the optimisation to complete.</p>"
    # If page was result of POST: show summary
    # Else: go to next page

    if not request.method == "POST":
        return render(request, template, context)
    else:
        form = revform.save(commit=False)
        form.SID = sid
        form.save()

        return HttpResponseRedirect('../runGA/')


def options(request):

    # Get the template/step status

    template = "design/options.html"
    context = {}

    # Get the session ID and database entry

    sid = get_session_id(request)
    context["steps"] = get_design_steps(template, sid)

    try:
        desdata = DesignModel.objects.get(SID=sid)
    except DesignModel.DoesNotExist:
        return HttpResponseRedirect('../maininput/')

    # Define form

    opsform = DesignOptionsForm(request.POST or None, instance=desdata)
    context["opsform"] = opsform

    # If page was result of POST: show summary
    # Else: go to next page

    if not request.method == "POST":
        return render(request, template, context)
    else:
        form = opsform.save(commit=False)
        form.SID = sid
        form.save()
        return HttpResponseRedirect('../review/')


def runGA(request):


    # Get the template/step status

    template = "design/runGA.html"
    context = {}
    context['tasks_queued'] = len(list(inspect().reserved().values())[0])
    context['tasks_running'] = float(len(list(inspect().active().values())[0]))/settings.CELERYD_CONCURRENCY


    # Get the session ID

    sid = get_session_id(request)
    context["steps"] = get_design_steps(template, sid)

    # retrieve session information

    retrieve_id = request.GET.get('retrieve','')
    if retrieve_id:
        desdata = DesignModel.objects.get(shareID=retrieve_id)
        desdata.SID=sid
        desdata.save()
        context["steps"] = get_design_steps(template, sid)

    try:
        desdata = DesignModel.objects.get(SID=sid)
        context['no_data'] = False
    except DesignModel.DoesNotExist:
        context['no_data']=True

        return render(request, template, context)

    # Do we know email?
    mailform = DesignMailForm(request.POST or None, instance=desdata)
    runform = DesignRunForm(request.POST, instance=desdata)

    if not desdata.email:
        context["mailform"] = mailform
    else:
        context['runform'] = runform

    # check status of job

    form = runform.save(commit=False)
    if desdata.taskID:
        task = AsyncResult(desdata.taskID)
        if task.status == "PENDING":
            form.taskstatus = 1
            form.running = 0
        elif task.status == "STARTED":
            form.taskstatus = 2
        elif ((task.status == "RETRY"
            or  task.status == "FAILURE"
            or task.status == "SUCCESS")
            and desdata.optimalorder):
            form.taskstatus = 3
            form.running = 0
        else:
            form.taskstatus = 0
            form.running = 0
    else:
        form.taskstatus = 0
        form.running = 0
    form.save()

    # pass results for visualisation

    if os.path.isfile(desdata.genfile):
        jsonfile = open(desdata.genfile).read()
        try:
            data = json.loads(jsonfile)
            data = json.dumps(data)
            context['optim'] = data
        except ValueError:
            pass

    if os.path.isfile(desdata.desfile):
        jsonfile = open(desdata.desfile).read()
        try:
            data = json.loads(jsonfile)
            data = json.dumps(data)
            context['design'] = data
            context['stim'] = desdata.S
        except ValueError:
            pass

    # show downloadform if results are available

    desdata = DesignModel.objects.get(SID=sid)
    if desdata.taskstatus == 3:
        downform = DesignDownloadForm(
            request.POST or None, instance=desdata)
        context["downform"] = downform

    # Responsive loop

    if request.method == "POST":
        someonesure = False

        # if mail is given
        if request.POST.get("Mail") == "Submit":

            if mailform.is_valid():

                email=mailform.cleaned_data['email']
                name=mailform.cleaned_data['name']

                desdata = DesignModel.objects.get(SID=sid)
                runform = DesignRunForm(None, instance=desdata)
                form = runform.save(commit=False)
                form.email = email
                form.name = name
                form.taskID = ""
                form.save()

                desdata = DesignModel.objects.get(SID=sid)

                context['mailform'] = None
                context['runform'] = runform

                return render(request, template, context)

        # If stop is requested
        if request.POST.get("GA") == "Stop":

            if not (desdata.taskstatus == 2 or desdata.taskstatus == 1):
                context['message'] = "You want to stop the optimisation, but nothing is running."
            else:
                revoke(desdata.taskID,terminate=True,signal='KILL')
                desdata = DesignModel.objects.get(SID=sid)
                runform = DesignRunForm(None, instance=desdata)
                form = runform.save(commit=False)
                form.taskstatus = 0
                form.taskID = ""
                form.save()
                context["message"] = "The optimisation has been terminated."

            return render(request, template, context)

        if request.POST.get("Sure") == "I'm sure about this":
            someonesure = True
            desdata = DesignModel.objects.get(SID=sid)
            runform = DesignRunForm(None, instance=desdata)
            form = runform.save(commit=False)
            form.taskstatus = 0
            form.taskID = ""
            form.convergence = False
            form.save()

        # If run is requested
        if request.POST.get("GA") == "Run" or someonesure:

            desdata = DesignModel.objects.get(SID=sid)
            if desdata.taskstatus > 0:
                if desdata.taskstatus == 1:
                    context['message'] = "There is already an optimisation process queued.  You can only queue or run one design optimisation at a time."
                elif desdata.taskstatus == 2:
                    context['message'] = "There is already an optimisation process running.  You can only queue or run one design optimisation at a time."
                elif desdata.taskstatus == 3:
                    context['sure'] = True
                    sureform = DesignSureForm(
                        request.POST or None, instance=desdata)
                    context['sureform'] = sureform
                return render(request, template, context)
            else:
                desdata = DesignModel.objects.get(SID=sid)
                runform = DesignRunForm(None, instance=desdata)
                res = GeneticAlgorithm.delay(sid)
                form = runform.save(commit=False)
                form.taskID = res.task_id
                form.save()
                desdata = DesignModel.objects.get(SID=sid)
                context['refresh'] = True
                context['status'] = "PENDING"
                context['message'] = "Job succesfully submitted."
                return render(request, template, context)


        # If request = download
        if request.POST.get("Download") == "Download optimal sequence":

            download = prepare_download(sid)

            resp = HttpResponse(
                download['file'].getvalue(),
                content_type="application/x-zip-compressed"
                )
            resp['Content-Disposition'] = 'attachment; filename=%s' % download['zipfile']

            return resp

    else:
        desdata = DesignModel.objects.get(SID=sid)
        context["preruns"] = desdata.preruncycles
        context["runs"] = desdata.cycles
        context["refrun"] = desdata.running
        context['status'] = "NOT RUNNING"

        if desdata.taskstatus==1:
            context['status'] = "PENDING"
        if desdata.taskstatus==2:
            context['status'] = "RUNNING"
            if desdata.preruncycles<1000 or desdata.cycles<1000 or desdata.resolution>0.2:
                context['alert'] = "Please be aware that the number of iterations for the optimisation is low.  These values are perfect for trying out the application but the results will be sub-optimal.  For a good optimisation, go to options on the review page and change the number of runs and preruns and the resolution.  Some reasonable values are: 10,000 preruns, 10,000 runs and a resolution of 0.1s."
        if desdata.taskstatus==3:
            context['refrun'] = 5
            context['status'] = "STOPPED"


        context["message"] = ""
        if desdata.running == 1:
            context["message"] = "Design optimisation initiated."
        elif desdata.running == 2:
            context["message"] = "Running first pre-run to find maximum efficiency."
        elif desdata.running == 3:
            context["message"] = "Running second pre-run to find maximum power."
        elif desdata.running == 4:
            context["message"] = "Running design optimisation."
        elif desdata.taskstatus == 3 and desdata.convergence:
            context['message'] = 'Design optimisation finished after convergence.'
        elif desdata.taskstatus == 3:
            context['message'] = 'Design optimisation finished, convergence not reached.  Consider increasing the number of generations.'


    return render(request, template, context)

def updatepage(request):
    return render(request, "design/updatepage.html", {})
