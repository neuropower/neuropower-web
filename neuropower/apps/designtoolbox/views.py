from __future__ import unicode_literals
import sys
sys.path = sys.path[1:]
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.conf import settings
from scipy.stats import norm, t
import os
from utils import get_session_id
from forms import DesignMainForm,DesignConsForm
from models import DesignModel

## MAIN PAGE TEMPLATE PAGES

def FAQ(request):
    return render(request,"design/FAQ.html",{})

def tutorial(request):
    return render(request,"design/tutorial.html",{})

def methods(request):
    return render(request,"design/methods.html",{})

def start(request):
    return render(request,'design/start.html',{})

def maininput(request):
    sid = get_session_id(request)

    # Get the template/step status
    template = "design/input.html"
    context = {}

    inputform = DesignMainForm(request.POST or None)

    if not request.method=="POST" or not inputform.is_valid():
        context["inputform"] = inputform
        return render(request,template,context)
    else:
        form = inputform.save(commit=False)
        form.SID = sid
        form.save()
        return HttpResponseRedirect('../consinput/')

def consinput(request):
    sid = get_session_id(request)
    desdata = DesignModel.objects.filter(SID=sid)[::-1][0]
    n = desdata.S
    c = desdata.Clen

    # Get the template/step status
    template = "design/cons.html"
    context = {}

    consform = DesignConsForm(request.POST or None)

    if not request.method=="POST" or not consform.is_valid():
        context["consform"] = consform
        return render(request,template,context)
    else:
        form = consform.save(commit=False)
        form.SID = sid
        form.save()
        return render(request,'design/DGaPars.html',{})

### SESSION CONTROL

def end_session(request):
    '''ends a session so the user can start a new one.'''
    try:
        request.session.flush()
    except KeyError:
        pass
    return neuropowerinput(request,end_session=True)
