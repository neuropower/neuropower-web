from __future__ import unicode_literals
from django.shortcuts import render
from django.core.files import File
from django.http import HttpResponse, HttpResponseRedirect
from .forms import ParameterForm, NiftiForm, PeakTableForm, MixtureForm
from django.db import models
from django.conf import settings
from .models import NiftiModel, PeakTableModel, ParameterModel, MixtureModel
from neuropower.utils import BUM, cluster, model, neuropowermodels,peakdistribution
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
        niftidata = NiftiModel.objects.filter(SID=sid).reverse()[0]
        niftiform = NiftiForm(None,default=niftidata.url)
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
    if not request.session.exists(request.session.session_key):
        request.session.create()
    sid = request.session.session_key
    if not NiftiModel.objects.filter(SID=sid):
        context = {
            "text":"Please first fill out the 'Data Location' form in the input."
        }
        return render(request,"neuropowerviewer.html",context)
    else:
        sid = request.session.session_key
        niftidata = NiftiModel.objects.filter(SID=sid).reverse()[0]
        parsform = ParameterForm(request.POST or None)
        context = {
            "url":niftidata.url,
            "viewer":"<div class='papaya' data-params='params'></div>"
        }
        if not parsform.is_valid():
            return render(request,"neuropowerviewer.html",context)
        else:
            return HttpResponseRedirect('/neuropowertable/')

def neuropowertable(request):
    if not request.session.exists(request.session.session_key):
        request.session.create()
    sid = request.session.session_key
    if not ParameterModel.objects.filter(SID=sid):
        context = {
            "text":"Please first fill out the 'Data Location' and the 'Data Parameters' in the input."
        }
        return render(request,"neuropowerviewer.html",context)
    else:
        sid = request.session.session_key
        if not PeakTableModel.objects.filter(SID=sid):
            niftidata = NiftiModel.objects.filter(SID=sid).reverse()[0]
            parsdata = ParameterModel.objects.filter(SID=sid).reverse()[0]
            parsdata.DoF = parsdata.Subj-1 if parsdata.Samples==1 else parsdata.Subj-2
            SPM=nib.load(niftidata.location).get_data()
            if parsdata.ZorT=='T':
                SPM = -norm.ppf(t.cdf(-SPM,df=float(parsdata.DoF)))
            parsdata.ExcZ = float(parsdata.Exc) if parsdata.ExcUnits=='t' else -norm.ppf(float(parsdata.Exc))
            peaks = cluster.cluster(SPM,parsdata.ExcZ)
            pvalues = np.exp(-parsdata.ExcZ*(np.array(peaks.peak)-parsdata.ExcZ))
            pvalues = [max(10**(-6),p) for p in pvalues]
            peaks['pval'] = pvalues
            peakform = PeakTableForm()
            savepeakform = peakform.save(commit=False)
            savepeakform.SID = sid
            savepeakform.data = peaks
            savepeakform.save()
            parsdata.save()
        else:
            peakdata = PeakTableModel.objects.filter(SID=sid).reverse()[0]
            peaks = peakdata.data
        context = {
        "peaks":peaks.to_html(classes=["table table-striped"]),
        }
        return render(request,"neuropowertable.html",context)

def neuropowermodel(request):
    if not request.session.exists(request.session.session_key):
        request.session.create()
    sid = request.session.session_key
    if not ParameterModel.objects.filter(SID=sid) or not NiftiModel.objects.filter(SID=sid):
        context = {
            "text":"Please first fill out the 'Data Location' and the 'Data Parameters' in the input."
        }
        return render(request,"neuropowerviewer.html",context)
    else:
        if not MixtureModel.objects.filter(SID=sid):
            parsdata = ParameterModel.objects.filter(SID=sid).reverse()[0]
            peakdata = PeakTableModel.objects.filter(SID=sid).reverse()[0]
            peaks = peakdata.data
            bum = BUM.bumOptim(peaks.pval.tolist(),starts=10)
            modelfit = neuropowermodels.modelfit(peaks.peak.tolist(),bum['pi1'],exc=float(parsdata.ExcZ),starts=10,method="RFT")
            mixtureform = MixtureForm()
            savemixtureform = mixtureform.save(commit=False)
            savemixtureform.SID = sid
            savemixtureform.pi1 = bum['pi1']
            savemixtureform.a = bum['a']
            savemixtureform.mu = modelfit['mu']
            savemixtureform.sigma = modelfit['sigma']
            savemixtureform.save()
        context = {
        #"peaks":peaks.to_html(classes=["table table-striped"]),
        }
        return render(request,"neuropowermodel.html",context)

def neuropowersamplesize(request):
    if not request.session.exists(request.session.session_key):
        request.session.create()
    sid = request.session.session_key
    if not ParameterModel.objects.filter(SID=sid) or not NiftiModel.objects.filter(SID=sid):
        context = {
            "text":"Please first fill out the 'Data Location' and the 'Data Parameters' in the input."
        }
    if not MixtureModel.objects.filter(SID=sid):
        context = {
            "text":"Please first go to the 'Model Fit' page to initiate and inspect the fit of the mixture model to the distribution."
        }
    else:
        mixdata = PeakTableModel.objects.filter(SID=sid).reverse()[0]
    return render(request,"neuropowersamplesize.html",{})
