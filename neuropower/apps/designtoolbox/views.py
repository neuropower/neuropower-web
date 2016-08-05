from __future__ import unicode_literals
import sys
sys.path = sys.path[1:]
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.conf import settings
from scipy.stats import norm, t
import os
from utils import get_session_id, probs_and_cons, get_design_steps
from forms import DesignMainForm,DesignConsForm,DesignReviewForm,DesignWeightsForm, DesignProbsForm, DesignOptionsForm
from models import DesignModel
import numpy as np

## MAIN PAGE TEMPLATE PAGES

def FAQ(request):
    return render(request,"design/FAQ.html",{})

def tutorial(request):
    return render(request,"design/tutorial.html",{})

def methods(request):
    return render(request,"design/methods.html",{})

def start(request):

    # Get the template/step status

    template = "design/start.html"
    context = {}

    # Get the session ID and database entry

    sid = get_session_id(request)
    context["steps"] = get_design_steps(template,sid)

    return render(request,template,context)

def maininput(request):

    # Get the template/step status

    template = "design/input.html"
    context = {}

    # Get the session ID and database entry

    sid = get_session_id(request)
    context["steps"] = get_design_steps(template,sid)

    try:
        desdata = DesignModel.objects.get(SID=sid)
    except DesignModel.DoesNotExist:
        desdata = None

    # Define form

    inputform = DesignMainForm(request.POST or None,instance=desdata)

    # If page was result of POST or not valid: show form with db entries
    # Else: go to next page

    if not request.method=="POST" or not inputform.is_valid():
        context["inputform"] = inputform
        return render(request,template,context)
    else:

        # initial save

        form = inputform.save(commit=False)
        form.SID = sid
        form.save()

        # get data and change parameters

        desdata = DesignModel.objects.get(SID=sid)
        weightsform = DesignWeightsForm(None, instance=desdata)
        weightsform = weightsform.save(commit=False)
        W = np.array([desdata.W1,desdata.W2,desdata.W3,desdata.W4])
        if np.sum(W)>1:
            W = W/np.sum(W)
        weightsform.W = W
        weightsform.save()

        return HttpResponseRedirect('../consinput/')

def consinput(request):

    # Get the template/step status

    template = "design/cons.html"
    context = {}

    # Get the session ID and database entry

    sid = get_session_id(request)
    context["steps"] = get_design_steps(template,sid)

    try:
        desdata = DesignModel.objects.get(SID=sid)
    except DesignModel.DoesNotExist:
        desdata = None
        inputform = DesignMainForm(request.POST or None, instance=desdata)
        template = 'design/input.html'
        message = "Before you can fill out the contrasts and trial probabilities, you'll first need to fill out this form with basic information about your design."
        context = {
            "inputform": inputform,
            "message": message,
            "steps":get_design_steps(template,sid)
        }
        return render(request,template,context)

    # Define form

    consform = DesignConsForm(request.POST or None,instance=desdata,stim=desdata.S,cons=desdata.Clen)

    # If page was result of POST or not valid: show form with db entries
    # Else: go to next page

    if not request.method=="POST" or not consform.is_valid():
        context["consform"] = consform
        return render(request,template,context)
    else:
        form = consform.save(commit=False)
        form.SID = sid
        form.save()

        # get data and change parameters

        consform = DesignProbsForm(None, instance=desdata)
        consform = consform.save(commit=False)
        matrices = probs_and_cons(sid)
        consform.P = matrices['P']
        consform.C = matrices['C']
        consform.save()

        return HttpResponseRedirect('../review/')

def review(request):

    # Get the template/step status

    template = "design/review.html"
    context = {}

    # Get the session ID and database entry

    sid = get_session_id(request)
    context["steps"] = get_design_steps(template,sid)

    try:
        desdata = DesignModel.objects.get(SID=sid)
    except DesignModel.DoesNotExist:
        desdata = None
        inputform = DesignMainForm(request.POST or None, instance=desdata)
        template = 'design/input.html'
        message = "Before you can review your settings, you'll first need to fill out this form with basic information about your design."
        context = {
            "inputform": inputform,
            "message": message,
            "steps":get_design_steps(template,sid)
        }
        return render(request,template,context)

    # Define form

    revform = DesignReviewForm(request.POST or None,instance=desdata)
    context["revform"] = revform

    # Set summary variables in context

    matrices = probs_and_cons(sid)
    context['ITI']=desdata.ITI
    context['TR']=desdata.TR
    context['S']=desdata.S
    context['L']=desdata.L
    context["P"] = matrices["P"]

    # If page was result of POST: show summary
    # Else: go to next page

    if not request.method=="POST":
        return render(request,template,context)
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
    context["steps"] = get_design_steps(template,sid)

    try:
        desdata = DesignModel.objects.get(SID=sid)
    except DesignModel.DoesNotExist:
        desdata = None
        inputform = DesignMainForm(request.POST or None, instance=desdata)
        template = 'design/input.html'
        message = "Before you can change the internal settings, you'll first need to fill out this form with basic information about your design."
        context = {
            "inputform": inputform,
            "message": message,
            "steps":get_design_steps(template,sid)
        }
        return render(request,template,context)

    # Define form

    opsform = DesignOptionsForm(request.POST or None,instance=desdata)
    context["opsform"] = opsform

    # If page was result of POST: show summary
    # Else: go to next page

    if not request.method=="POST":
        return render(request,template,context)
    else:
        form = opsform.save(commit=False)
        form.SID = sid
        form.save()
        return HttpResponseRedirect('../runGA/')

def runGA(request):
    sid = get_session_id(request)
    context["steps"] = get_design_steps(template,sid)

    desdata = DesignModel.objects.filter(SID=sid)[::-1][0]

    # Get the template/step status
    template = "design/RunGA.html"
    context = {}

    return render(request,template,context)

### SESSION CONTROL

def end_session(request):
    '''ends a session so the user can start a new one.'''
    try:
        request.session.flush()
    except KeyError:
        pass
    return neuropowerinput(request,end_session=True)
