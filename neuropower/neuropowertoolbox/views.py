from __future__ import unicode_literals
from django.shortcuts import render
from django.core.files import File
from django.http import HttpResponse, HttpResponseRedirect
from .forms import ParameterForm, NiftiForm, PeakTableForm
from django.db import models
from django.conf import settings
from .models import NiftiModel, PeakTableModel, ParameterModel
from neuropower.utils import BUM, cluster, model, neuropower,peakdistribution
from django.forms import model_to_dict
import nibabel as nib
import os
import numpy as np
from scipy.stats import norm

def home(request):
    return render(request,"home.html",{})

def neuropower(request):
    sid = request.session.session_key
    niftiform = NiftiForm(request.POST or None,default="URL to nifti image")
    parsform = ParameterForm(request.POST or None)
    context = {
        "niftiform": niftiform,
        "parsform": parsform
    }
    if not niftiform.is_valid():
        return render(request,"neuropower.html",context)
    else:
        saveniftiform = niftiform.save(commit=False)
        saveniftiform.SID = sid
        saveniftiform.save()
        return HttpResponseRedirect('/neuropowerviewer/')

def neuropowerviewer(request):
    sid = request.session.session_key
    niftidata = NiftiModel.objects.filter(SID=sid).reverse()[0]
    niftiform = NiftiForm(None,default=niftidata.url)
    parsform = ParameterForm(request.POST or None)
    context = {
        "niftiform": niftiform,
        "parsform": parsform,
        "url":niftidata.url,
    }
    if not parsform.is_valid():
        return render(request,"neuropowerviewer.html",context)
    else:
        saveparsform = parsform.save(commit=False)
        saveparsform.SID = sid
        saveparsform.save()
        return HttpResponseRedirect('/neuropowertable/')


def neuropowertable(request):
    sid = request.session.session_key
    niftidata = NiftiModel.objects.filter(SID=sid).reverse()[0]
    parsdata = ParameterModel.objects.filter(SID=sid).reverse()[0]
    niftiform = NiftiForm(None,default=niftidata.url)
    parsform = ParameterForm(None)
    if not PeakTableModel.objects.filter(SID=sid):
        dof = [parsdata.Subj-1 if parsdata.Samples==1 else parsdata.Subj-2]
        SPM=nib.load(niftidata.location).get_data()
        if parsdata.ZorT=='T':
            SPM = -norm.ppf(t.cdf(-SPM,df=float(dof)))
        excZ = [float(parsdata.Exc) if parsdata.ExcUnits=='Z' else -norm.ppf(float(parsdata.Exc))]
        peaks = cluster.cluster(SPM,excZ[0])
        peakform = PeakTableForm()
        savepeakform = peakform.save(commit=False)
        savepeakform.SID = sid
        savepeakform.data = peaks
        savepeakform.save()
    else:
        peakdata = PeakTableModel.objects.filter(SID=sid).reverse()[0]
        peaks = peakdata.data
    context = {
    "url":niftidata.url,
    "niftiform": niftiform,
    "parsform": parsform,
    "peaks":peaks.to_html(classes=["table table-striped"]),
    }
    return render(request,"neuropowertable.html",context)

def neuropowermodelplot(request):
    sid = request.session.session_key
    peakdata = PeakTableModel.objects.filter(SID=sid).reverse()[0]
    peaks = peakdata.data
    context = {
    "peaks":peaks.to_html(classes=["table table-striped"]),
    }
    return render(request,"neuropowermodelplot.html",context)

def plotpage(request):
    return render(request,"plotpage.html",{})
