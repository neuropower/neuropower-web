from __future__ import unicode_literals
import sys
sys.path = sys.path[1:]

from django.contrib.sessions.backends.db import SessionStore
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, render_to_response
from django.core.mail import send_mail
from django.conf import settings
from scipy.stats import norm, t
from utils.prepare_GA import *
from django.db.models import Q
from datetime import datetime
from utils.utils import *
from copy import deepcopy
from .models import *
import datetime as dt
from .forms import *
import pandas as pd
import numpy as np
import StringIO
import requests
import zipfile
import urllib2
import shutil
import time
import json
import csv
import os


def end_session(request):
    # Get the session ID and database entry

    sid = get_session_id(request)

    '''ends a session so the user can start a new one.'''
    try:
        request.session.flush()
    except KeyError:
        pass
    return start(request)

def DFAQ(request):
    return render(request, "design/DFAQ.html", {})

def tutorial(request):
    return render(request, "design/tutorial.html", {})

def methods(request):
    return render(request, "design/methods.html", {})

def package(request):
    return render(request, "design/pythonpackage.html", {})

def start(request, end_session=False):

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


def maininput(request):

    # Get the template/step status

    template = "design/input.html"
    context = {}

    # Get the session ID and database entry

    sid = get_session_id(request)
    context["steps"] = get_design_steps(template, sid)

    desdata = DesignModel.objects.filter(SID=sid).last()
    if desdata == None:
        desdata = DesignModel.create(sid)

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
        desdata.SID = sid
        desdata.step = 1

        # get data and change parameters
        W = np.array([desdata.W1, desdata.W2, desdata.W3, desdata.W4])
        if np.sum(W) != 1:
            W = W / np.sum(W)
        desdata.W = W

        # get duration in seconds
        if desdata.duration_unitfree:
            if desdata.duration_unit == 2:
                desdata.duration = desdata.duration_unitfree*60
            elif desdata.duration_unit == 1:
                desdata.duration = desdata.duration_unitfree
        desdata.save()

        return HttpResponseRedirect('../consinput/')

def consinput(request):

    # Get the template/step status

    template = "design/cons.html"
    context = {}

    # Get the session ID and database entry

    sid = get_session_id(request)
    context["steps"] = get_design_steps(template, sid)

    desdata = DesignModel.objects.filter(SID=sid).last()
    if desdata == None:
        return HttpResponseRedirect('../maininput/')

    consform = DesignConsForm(
        request.POST or None, instance=desdata, stim=desdata.S, cons=desdata.Clen)

    if not request.method == "POST":

        context["consform"] = consform
        return render(request, template, context)

    else:

        form = consform.save(commit=False)
        form.set=2
        form.SID = sid
        form.save()

        # get data and change parameters

        matrices = probs_and_cons(desdata.SID)
        print(desdata.SID)

        if matrices['empty'] == True:
            context['message'] = "Please fill out all probabilities and contrasts"
            context["consform"] = DesignConsForm(
                request.POST or None, instance=desdata, stim=desdata.S, cons=desdata.Clen)
            return render(request, "design/cons.html", context)

        desdata.P = matrices['P']
        desdata.C = matrices['C']
        if desdata.HardProb == True:
            desdata.G = 200
            desdata.I = 100
        desdata.save()

        return HttpResponseRedirect('../review/')


def review(request):

    # Get the template/step status

    template = "design/review.html"
    context = {}

    # Get the session ID and database entry

    sid = get_session_id(request)
    context["steps"] = get_design_steps(template, sid)

    desdata = DesignModel.objects.filter(SID=sid).last()
    if desdata == None:
        return HttpResponseRedirect('../maininput/')

    # Define form

    revform = DesignReviewForm(request.POST or None, instance=desdata)
    context["revform"] = revform

    # Set summary variables in context

    matrices = probs_and_cons(sid)
    context["Phtml"] = matrices["Phtml"]
    context["Chtml"] = matrices["Chtml"]
    context["Whtml"] = weights_html(desdata.W)
    context['desdata'] = desdata

    context["message"] = ""
    if desdata.HardProb == True:
        context["message"] = context["message"] + \
            "<br><p><b>Warning:</b> Because of the hard limit on the frequencies, we increased the size of the generation and the number of random designs per generation.  This might slow down the optimisation.  </p>"
    if desdata.MaxRepeat < 10 and desdata.S == 2:
        context["message"] = context["message"] + "<br><p><b>Warning:</b> With only 2 stimuli, many random designs have repetitions larger than " + \
            str(desdata.MaxRepeat) + \
            ".  We increased the number of random designs per generation, but this might slow down the optimisation.  </p>"
    if desdata.S>5 and desdata.L>200 and (desdata.ITIunifmax>3 or desdata.ITItruncmax>3) and (desdata.Restnum<30 and desdata.Resdur>30) and desdata.C.shape[0]>5:
        context['message'] = context['message']+"<br><p><b>Warning:</b>This is a long and complex design.  Be aware that the optimisation will take a <b>long</b> time.</p>"

    # Duration
    if desdata.ITImodel == 1:
        context['ITImodel'] = "fixed"
        mean = desdata.ITIfixed
        context['ITI'] = "The ITI's are equal to "+str(mean)+" seconds."
    elif desdata.ITImodel == 2:
        context['ITImodel'] = 'truncated exponential'
        mean = desdata.ITItruncmean
        context['ITI'] = "The ITI's are between "+str(desdata.ITItruncmin)+" and "+str(desdata.ITItruncmax)+" seconds and on average "+str(mean)+" seconds."
    elif desdata.ITImodel == 3:
        context['ITImodel'] = 'uniform'
        mean = (desdata.ITIunifmin+desdata.ITIunifmax)/2.
        context['ITI'] = "The ITI's are between "+str(desdata.ITIunifmin)+" and "+str(desdata.ITIunifmax)+" seconds and on average "+str(mean)+" seconds."

    if desdata.L:
        if desdata.RestNum>0:
            dur = mean*desdata.L+desdata.RestNum*desdata.RestDur
        else:
            dur = mean*desdata.L
    elif desdata.duration:
        dur = desdata.duration
    else:
        dur == 0
    if dur > 1800:
        context['message'] = context['message'] + "<p><b>Warning:</b> The run you request is longer dan 30 minutes.  This optimisation will take <b>a long</b> time.  You could set the resolution lower, or split the experiment in multiple shorter runs.  Or you could grab a coffee and wait a few hours for the optimisation to complete.</p>"
    # If page was result of POST: show summary
    # Else: go to next page

    if not request.method == "POST":
        return render(request, template, context)
    else:
        desdata.SID = sid
        desdata.save()

        return HttpResponseRedirect('../runGA/')


def options(request):

    # Get the template/step status

    template = "design/options.html"
    context = {}

    # Get the session ID and database entry

    sid = get_session_id(request)
    context["steps"] = get_design_steps(template, sid)

    desdata = DesignModel.objects.filter(SID=sid).last()
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

    # Get the session ID

    sid = get_session_id(request)
    context["steps"] = get_design_steps(template, sid)

    # retrieve DB entry (eiter retrieve or session)

    retrieve_id = request.GET.get('retrieve','')
    if retrieve_id:
        desdata = DesignModel.objects.filter(shareID=retrieve_id).first()
        desdata.SID = sid
        desdata.save()
        context["steps"] = get_design_steps(template, sid)
    else:
        desdata = DesignModel.objects.filter(SID=sid).last()
        if not desdata == None:
            context['no_data'] = False
        else:
            context['no_data']=True
            return render(request, template, context)

    # Do we know email?

    mailform = DesignMailForm(request.POST or None)
    runform = DesignRunForm(request.POST, instance = desdata)

    if not desdata.email:
        context["mailform"] = mailform
    else:
        context['runform'] = runform

    # is there a process started? If yes, what's the status?

    status = None
    if not desdata.jobid == "":
        status = get_job_status(sid)['status']

    # pass results for visualisation

    if isinstance(desdata.metrics,dict):
        optim = json.dumps(desdata.metrics)
        context['optim'] = optim

    if isinstance(desdata.bestdesign,dict):
        data = json.dumps(desdata.bestdesign)
        context['design'] = data
        context['stim'] = desdata.S

    # show downloadform if results are available
    desdata = DesignModel.objects.filter(SID=sid).last()
    if status == 'SUCCEEDED':
        downform = DesignDownloadForm(
            request.POST or None, instance=desdata)
        context["downform"] = downform

    # show downloadform for py-file if submitted
    if status:
        codeform = DesignCodeForm(
            request.POST or None, instance=desdata)
        context['codeform'] = codeform
        context['status'] = status

    # Responsive loop

    if request.method == "POST":

        # if mail is given
        if request.POST.get("Mail") == "Submit":

            if mailform.is_valid():

                email=mailform.cleaned_data['email']
                name=mailform.cleaned_data['name']

                desdata = DesignModel.objects.filter(SID=sid).last()
                runform = DesignRunForm(None, instance=desdata)
                form = runform.save(commit=False)
                form.email = email
                form.name = name
                form.taskID = ""
                form.save()

                desdata = DesignModel.objects.filter(SID=sid).last()

                context['mailform'] = None
                context['runform'] = runform

                return render(request, template, context)

        # If stop is requested
        if request.POST.get("GA") == "Stop":

            if not status or status == 'SUCCEEDED' or status == 'FAILED':
                context['message'] = "You want to stop the optimisation, but nothing is running."
            else:
                stop_job(sid)
                context['message'] = "Your optimisation is halted."
                context['status'] = 'FAILED'
            return render(request, template, context)


        # If run is requested
        if request.POST.get("GA") == "Run":

            desdata = DesignModel.objects.filter(SID=sid).last()
            if status and not ( status == 'SUCCEEDED' or status == 'FAILED' ):
                context['message'] = "There is already an optimisation process running.  You can only queue or run one design optimisation at a time."
            else:
                # start process
                write_neurodesign_script(sid)
                jobid = submit_batch(sid)
                form = runform.save(commit=False)
                form.jobid = jobid
                form.metrics = ""
                form.shareID = sid
                form.bestdesign = ""
                form.running = 0
                form.save()
                desdata = DesignModel.objects.filter(SID=sid).last()
                context['refresh'] = True
                context['message'] = "Job succesfully submitted."
                context['status'] = 'SUBMITTED'
                return render(request, template, context)


        if request.POST.get("Code") == "Download script":
            desdata = DesignModel.objects.filter(SID=sid).last()
            url = get_s3_url("%s.py"%desdata.shareID)
            return HttpResponseRedirect(url)

        # If request = download
        if request.POST.get("Download") == "Download optimal sequence":
            desdata = DesignModel.objects.filter(SID=sid).last()
            url = get_s3_url("%s.tar.gz"%desdata.shareID)
            return HttpResponseRedirect(url)

    else:
        desdata = DesignModel.objects.filter(SID=sid).last()
        context["preruns"] = desdata.preruncycles
        context["runs"] = desdata.cycles
        context["refrun"] = desdata.running

        if desdata.preruncycles<1000 or desdata.cycles<1000 or desdata.resolution>0.2:
            context['alert'] = "Please be aware that the number of iterations for the optimisation is low.  These values are perfect for trying out the application but the results will be sub-optimal.  For a good optimisation, go to the settings and change the number of runs and preruns and the resolution.  Some reasonable values are: 10,000 preruns, 10,000 runs and a resolution of 0.1s."
        if status == 'FAILED':
            context['alert'] = "Something went wrong and we don't know what.  Your optimisation has stopped.  You can see the optimisation below, but you can't download the results. Please contact us if the problem reoccurs."

    if status == 'RUNNING':
        if desdata.running == 2:
            context['message'] = 'Running first pre-run to find maximum efficiency.'
        elif desdata.running == 3:
            context["message"] = "Running second pre-run to find maximum power."
        elif desdata.running == 4:
            context['message'] = 'Design optimisation running.'
        if desdata.running in [2,3,4]:
            context['refrun'] = desdata.running
    if status == 'SUCCEEDED':
        context['refrun'] = desdata.running
        context['message'] = 'Design optimisation finished.'

    return render(request, template, context)
