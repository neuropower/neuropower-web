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
from utils import get_session_id, probs_and_cons, get_design_steps, weights_html, combine_nested,textify_code
from .forms import DesignMainForm, DesignConsForm, DesignReviewForm, DesignWeightsForm, DesignProbsForm, DesignOptionsForm, DesignRunForm, DesignDownloadForm, ContactForm, DesignNestedForm,DesignNestedConsForm, DesignSureForm, DesignMailForm, DesignCodeForm
from .models import DesignModel
from .tasks import GeneticAlgorithm
import numpy as np
import time
import json
import pandas as pd
import csv
import zipfile
import StringIO
import shutil
import urllib2
from datetime import datetime
from celery import task
from celery.task.control import revoke, inspect
from celery.result import AsyncResult
import requests


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
        form.local_folder = "/var/tmp/"
        form.design_suffix = "design_"+str(sid)
        form.onsets_folder = form.local_folder + form.design_suffix
        form.codefilename = "GeneticAlgorithm_"+str(sid)+".py"
        form.codefile = os.path.join(form.onsets_folder, form.codefilename)
        form.save()

        if os.path.exists(form.onsets_folder):
            files = os.listdir(form.onsets_folder)
            for f in files:
                if os.path.isdir(os.path.join(form.onsets_folder,f)):
                    shutil.rmtree(os.path.join(form.onsets_folder,f))
                else:
                    os.remove(os.path.join(form.onsets_folder,f))
        else:
            os.mkdir(form.onsets_folder)
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

        # get duration in seconds
        if desdata.duration_unitfree:
            if desdata.duration_unit == 2:
                weightsform.duration = desdata.duration_unitfree*60
            elif desdata.duration_unit == 1:
                weightsform.duration = desdata.duration_unitfree
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
    if desdata.S>5 and desdata.L>200 and desdata.ITImax>3 and (desdata.Restnum<30 and desdata.Resdur>30) and desdata.C.shape[0]>5:
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
        pass

    # Define form
    if "desdata" in locals():
        opsform = DesignOptionsForm(request.POST or None, instance=desdata)
    else:
        opsform = DesignOptionsForm(request.POST or None)

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
    if not inspect().reserved() == None:
        context['tasks_queued'] = len(list(inspect().reserved().values())[0])
        context['tasks_running'] = float(len(list(inspect().active().values())[0]))/settings.CELERYD_CONCURRENCY
    else:
        context['tasks_queued'] = 0
        context['tasks_running'] = 0


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
    if desdata.taskstatus == 0:
        form.running = 0
    elif desdata.taskstatus == 1 or desdata.taskstatus == 2:
        if not desdata.timestamp == "":
            last = datetime.strptime(desdata.timestamp,'%Y-%m-%d %H:%M:%S.%f')
            now = datetime.now()
            delta = now-last
            deltamin = delta.days*24*60.+delta.seconds/60.
            if deltamin > 10:
                form.taskstatus = 4
                form.running = 0
        else:
            form.taskstatus = 4
            form.running = 0
    elif desdata.taskstatus > 2:
        form.running = 0
    form.save()

    # This approach needs access to the workers which is not guaranteed with EB
    # if desdata.taskID:
    #     task = AsyncResult(desdata.taskID)
    #     if task.status == "PENDING":
    #         form.taskstatus = 1
    #         form.running = 0
    #         if desdata.finished == True:
    #             form.taskstatus = 3
    #             form.running = 0
    #     elif task.status == "STARTED":
    #         form.taskstatus = 2
    #     elif ((task.status == "RETRY"
    #         or  task.status == "FAILURE"
    #         or task.status == "SUCCESS")):
    #         form.taskstatus = 3
    #         form.running = 0
    #     else:
    #         form.taskstatus = 0
    #         form.running = 0
    # else:
    #     form.taskstatus = 0
    #     form.running = 0
    # form.save()

    # pass results for visualisation

    if isinstance(desdata.metrics,dict):
        optim = json.dumps(desdata.metrics)
        context['optim'] = optim

    if isinstance(desdata.bestdesign,dict):
        data = json.dumps(desdata.bestdesign)
        context['design'] = data
        context['stim'] = desdata.S

    # show downloadform if results are available
    desdata = DesignModel.objects.get(SID=sid)
    if desdata.taskstatus == 3:
        downform = DesignDownloadForm(
            request.POST or None, instance=desdata)
        context["downform"] = downform

    if desdata.taskstatus>1:
        codeform = DesignCodeForm(
            request.POST or None, instance=desdata)
        context['codeform'] = codeform

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
            form.finished = False
            form.convergence = False
            form.save()

        # If run is requested
        if request.POST.get("GA") == "Run" or someonesure:

            desdata = DesignModel.objects.get(SID=sid)
            if desdata.taskstatus > 0 and not desdata.taskstatus == 4:
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
                form.taskstatus = 2
                form.taskstatus = 1
                form.save()
                desdata = DesignModel.objects.get(SID=sid)
                context['refresh'] = True
                context['status'] = "PENDING"
                context['message'] = "Job succesfully submitted."
                return render(request, template, context)


        # If request = download
        if request.POST.get("Code") == "Download script":
            cmd = textify_code(sid)
            desdata = DesignModel.objects.get(SID=sid)

            resp = HttpResponse(
                cmd
                )
            resp['Content-Disposition'] = 'attachment; filename=%s' % desdata.codefilename

            return resp

        # If request = download
        if request.POST.get("Download") == "Download optimal sequence":
            desdata = DesignModel.objects.get(SID=sid)

            if os.path.exists(form.onsets_folder):
                files = os.listdir(form.onsets_folder)
                for f in files:
                    if os.path.isdir(os.path.join(form.onsets_folder,f)):
                        shutil.rmtree(os.path.join(form.onsets_folder,f))
                    else:
                        os.remove(os.path.join(form.onsets_folder,f))
            else:
                os.mkdir(form.onsets_folder)

            localfiles = []
            for fl in desdata.files:
                # check if part right after "design_sid" is a folder, if yes: make folder
                stripped = fl.split("/")[1]
                if len(stripped.split("."))==1:
                    # means it's a folder under onsetsfolder
                    folder = desdata.onsets_folder+"/"+stripped
                    if not os.path.exists(folder):
                        os.mkdir(folder)
                aws_url = "https://"+settings.AWS_S3_CUSTOM_DOMAIN+"/designs/"+fl
                local = desdata.local_folder+fl

                response = requests.get(aws_url)
                if response.status_code == 200:
                    with open(local,"wb") as f:
                        f.write(response.content)

                localfiles.append(local)

            # zip up
            zip_subdir = "OptimalDesign"
            zip_filename = "%s.zip" % zip_subdir
            popfile = StringIO.StringIO()
            zf = zipfile.ZipFile(popfile,"w")

            for fpath in localfiles:
                zf.write(os.path.join(desdata.design_suffix,fpath),os.path.join(zip_subdir,fpath))
            zf.close()

            resp = HttpResponse(
                popfile.getvalue(),
                content_type="application/x-zip-compressed"
                )
            resp['Content-Disposition'] = 'attachment; filename=%s' % zip_filename

            return resp

    else:
        desdata = DesignModel.objects.get(SID=sid)
        context["preruns"] = desdata.preruncycles
        context["runs"] = desdata.cycles
        context["refrun"] = desdata.running
        context['status'] = "NOT RUNNING"

        if desdata.taskstatus==0:
            context['status'] = "PENDING"
        if desdata.taskstatus==1 or desdata.taskstatus==2:
            context['status'] = "RUNNING"
            if desdata.preruncycles<1000 or desdata.cycles<1000 or desdata.resolution>0.2:
                context['alert'] = "Please be aware that the number of iterations for the optimisation is low.  These values are perfect for trying out the application but the results will be sub-optimal.  For a good optimisation, go to the settings and change the number of runs and preruns and the resolution.  Some reasonable values are: 10,000 preruns, 10,000 runs and a resolution of 0.1s."
        if desdata.taskstatus==3:
            context['refrun'] = 5
            context['status'] = "FINISHED"
        if desdata.taskstatus == 4:
            context['refrun'] = 5
            context['status'] = "FAILED"
            context['alert'] = "Something went wrong and we don't know what.  Your optimisation has stopped.  You can see the optimisation below, but you can't download the results. Please contact us if the problem reoccurs."


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
