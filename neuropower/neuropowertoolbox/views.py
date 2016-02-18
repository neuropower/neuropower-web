from __future__ import unicode_literals
from django.shortcuts import render
from django.core.files import File
from django.http import HttpResponse, HttpResponseRedirect
from .forms import ParameterForm, NiftiForm, PeakTableForm
from django.db import models
from django.conf import settings
from .models import NiftiModel, PeakTableModel, ParameterModel, MixtureModel
from neuropower.utils import BUM, cluster, model, neuropower,peakdistribution
from django.forms import model_to_dict
import nibabel as nib
import os
import numpy as np
from scipy.stats import norm, t

def home(request):
    return render(request,"home.html",{})

def neuropower(request):
    if not request.session.exists(request.session.session_key):
        request.session.create()
    sid = request.session.session_key
    if not NiftiModel.objects.filter(SID=sid):
        niftiform = NiftiForm(request.POST or None,default="URL to nifti image")
        parsform = ParameterForm(None)
        context = {"niftiform": niftiform,"parsform": parsform}
        if not niftiform.is_valid():
            return render(request,"neuropower.html",context)
            print("not valid")
        else:
            saveniftiform = niftiform.save(commit=False)
            saveniftiform.SID = sid
            saveniftiform.save()
            return HttpResponseRedirect('/neuropowerviewer/')
    if NiftiModel.objects.filter(SID=sid) and not ParameterModel.objects.filter(SID=sid):
        niftiform = NiftiForm(None,default="URL to nifti image")
        parsform = ParameterForm(request.POST or None)
        context = {"niftiform": niftiform,"parsform": parsform}
        if not parsform.is_valid():
            return render(request,"neuropower.html",context)
        else:
            saveparsform = parsform.save(commit=False)
            saveparsform.SID = sid
            saveparsform.save()
            return HttpResponseRedirect('/neuropowertable/')
    else:
        niftiform = NiftiForm(None,default="URL to nifti image")
        parsform = ParameterForm(None)
        context = {"niftiform": niftiform,"parsform": parsform}
        return render(request,"neuropower.html",context)

def neuropowerviewer(request):
    sid = request.session.session_key
    niftidata = NiftiModel.objects.filter(SID=sid).reverse()[0]
    parsform = ParameterForm(request.POST or None)
    context = {
        "url":niftidata.url,
    }
    if not parsform.is_valid():
        return render(request,"neuropowerviewer.html",context)
    else:
        return HttpResponseRedirect('/neuropowertable/')


def neuropowertable(request):
    sid = request.session.session_key
    if not PeakTableModel.objects.filter(SID=sid):
        niftidata = NiftiModel.objects.filter(SID=sid).reverse()[0]
        parsdata = ParameterModel.objects.filter(SID=sid).reverse()[0]
        dof = parsdata.Subj-1 if parsdata.Samples==1 else parsdata.Subj-2
        SPM=nib.load(niftidata.location).get_data()
        if parsdata.ZorT=='T':
            SPM = -norm.ppf(t.cdf(-SPM,df=float(dof)))
        ExcZ = float(parsdata.Exc) if parsdata.ExcUnits=='t' else -norm.ppf(float(parsdata.Exc))
        peaks = cluster.cluster(SPM,ExcZ)
        pvalues = np.exp(-ExcZ*(np.array(peaks.peak)-ExcZ))
        pvalues = [max(10**(-6),p) for p in pvalues]
        peaks['pval'] = pvalues
        peakform = PeakTableForm()
        savepeakform = peakform.save(commit=False)
        savepeakform.SID = sid
        savepeakform.data = peaks
        savepeakform.save()
    else:
        peakdata = PeakTableModel.objects.filter(SID=sid).reverse()[0]
        peaks = peakdata.data
    context = {
    "peaks":peaks.to_html(classes=["table table-striped"]),
    }
    return render(request,"neuropowertable.html",context)

def neuropowermodel(request):
    sid = request.session.session_key
    if not MixtureModel.objects.filter(SID=sid):
        peakdata = PeakTableModel.objects.filter(SID=sid).reverse()[0]
        peaks = peakdata.data
        bum = BUM.bumOptim(peaks['pval'].tolist(),starts=10)
        #modelfit = neuropower.modelfit(peaks.peak,bum['pi1'],exc=exc,starts=10,method="RFT")
    context = {
    "peaks":peaks.to_html(classes=["table table-striped"]),
    }
    return render(request,"neuropowermodel.html",context)

def plotpage(request):
    return render(request,"plotpage.html",{})
