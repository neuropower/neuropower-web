from __future__ import unicode_literals
from django.shortcuts import render
from django.core.files import File
from django.http import HttpResponse, HttpResponseRedirect
from .forms import ParameterForm, PeakTableForm, MixtureForm, PowerTableForm, PowerForm
from django.db import models
from django.conf import settings
from .models import PeakTableModel, ParameterModel, MixtureModel, PowerTableModel, PowerModel
from neuropower.utils import BUM, cluster, model, neuropowermodels,peakdistribution
from django.forms import model_to_dict
import nibabel as nib
import os
import numpy as np
from scipy.stats import norm, t
import pandas as pd
import tempfile, shutil, os,urllib
from .plots import plotPower
from nilearn import masking

def create_temporary_copy(path,sid):
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, 'nifti_down_"+sid+".nii.gz')
    urllib.urlretrieve(path, temp_path)
    return temp_path

def home(request):
    return render(request,"home.html",{})

def get_session_id(request):
    if not request.session.exists(request.session.session_key):
        request.session.create()
    sid = request.session.session_key
    return(sid)

def neuropower(request):
    sid = get_session_id(request)
    parsform = ParameterForm(request.POST or None,default="URL to nifti image")
    context = {"parsform": parsform}
    if not parsform.is_valid():
        return render(request,"neuropower.html",context)
    else:
        url = parsform.cleaned_data['url']
        location = create_temporary_copy(url,sid)
        SPM=nib.load(location)
        mask=masking.compute_background_mask(SPM,border_size=2, opening=True)
        nvox = np.sum(mask.get_data())
        saveparsform = parsform.save(commit=False)
        saveparsform.SID = sid
        saveparsform.location = location
        saveparsform.nvox = nvox
        saveparsform.save()
        return HttpResponseRedirect('/neuropowerviewer/')

def neuropowerviewer(request):
    sid = get_session_id(request)
    if not ParameterModel.objects.filter(SID=sid):
        context = {
            "text":"Please first fill out the input."
        }
        return render(request,"neuropowerviewer.html",context)
    else:
        sid = request.session.session_key
        parsdata = ParameterModel.objects.filter(SID=sid)[::-1][0]
        context = {
            "url":parsdata.url,
            "viewer":"<div class='papaya' data-params='params'></div>",
            "text":""
        }
        return render(request,"neuropowerviewer.html",context)

def neuropowertable(request):
    sid = get_session_id(request)
    if not ParameterModel.objects.filter(SID=sid):
        context = {
            "text":"Please first fill out the 'Data Location' and the 'Data Parameters' in the input."
        }
        return render(request,"neuropowerviewer.html",context)
    else:
        sid = request.session.session_key
        parsdata = ParameterModel.objects.filter(SID=sid)[::-1][0]
        parsdata.DoF = parsdata.Subj-1 if parsdata.Samples==1 else parsdata.Subj-2
        SPM=nib.load(parsdata.location).get_data()
        if parsdata.ZorT=='T':
            SPM = -norm.ppf(t.cdf(-SPM,df=float(parsdata.DoF)))
        parsdata.ExcZ = float(parsdata.Exc) if float(parsdata.Exc)>1 else -norm.ppf(float(parsdata.Exc))
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
        context = {
        "peaks":peaks.to_html(classes=["table table-striped"]),
        }
        return render(request,"neuropowertable.html",context)

def neuropowermodel(request):
    sid = get_session_id(request)
    if not ParameterModel.objects.filter(SID=sid):
        context = {"text":"Please first fill out the input."}
        return render(request,"neuropowerviewer.html",context)
    else:
        parsdata = ParameterModel.objects.filter(SID=sid)[::-1][0]
        peakdata = PeakTableModel.objects.filter(SID=sid)[::-1][0]
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
        return render(request,"neuropowermodel.html",{})

def neuropowersamplesize(request):

    sid = get_session_id(request)
    powerinputform = PowerForm(request.POST or None)

    if not ParameterModel.objects.filter(SID=sid):
        texttop = "Please first fill out the 'Data Location' and the 'Data Parameters' in the input."
        plothtml = ""
        textbottom = ""

    if not MixtureModel.objects.filter(SID=sid):
        texttop = "Please first go to the 'Model Fit' page to initiate and inspect the fit of the mixture model to the distribution."
        plothtml = ""
        textbottom = ""

    else:
        texttop = "Hover over the lines to see detailed power predictions"
        textbottom = ""
        parsdata = ParameterModel.objects.filter(SID=sid)[::-1][0]
        peakdata = PeakTableModel.objects.filter(SID=sid)[::-1][0]
        mixdata = MixtureModel.objects.filter(SID=sid)[::-1][0]
        peaks = peakdata.data
        thresholds = neuropowermodels.threshold(peaks.peak,peaks.pval,FWHM=8,nvox=float(parsdata.nvox),alpha=0.05,exc=float(parsdata.ExcZ))
        effect_cohen = float(mixdata.mu)/np.sqrt(float(parsdata.Subj))
        power_predicted = []
        newsubs = range(parsdata.Subj,71)
        for s in newsubs:
            projected_effect = float(effect_cohen)*np.sqrt(float(s))
            powerpred =  {k:1-neuropowermodels.altCDF(v,projected_effect,float(mixdata.sigma),exc=float(parsdata.ExcZ),method="RFT") for k,v in thresholds.items() if v!='nan'}
            power_predicted.append(powerpred)
        powertable = pd.DataFrame(power_predicted)
        powertable['newsamplesize']=newsubs
        powertableform = PowerTableForm()
        savepowertableform = powertableform.save(commit=False)
        savepowertableform.SID = sid
        savepowertableform.data = powertable
        savepowertableform.save()
        powerinputform = PowerForm(request.POST or None)
        plothtml = plotPower(sid)['code']
        if request.method == "POST":
            if powerinputform.is_valid():
                savepowerinputform = powerinputform.save(commit=False)
                savepowerinputform.SID = sid
                savepowerinputform.save()
                powerinputdata = PowerModel.objects.filter(SID=sid)[::-1][0]
                pow = powerinputdata.reqPow
                ss = powerinputdata.reqSS
                plotpower = plotPower(sid,powerinputdata.MCP,pow,ss)
                plothtml = plotpower['code']
                textbottom = plotpower['text']
        context = {
        "texttop":texttop,
        "textbottom":textbottom,
        "plothtml":plothtml,
        "powerinputform":powerinputform
        }
        return render(request,"neuropowersamplesize.html",context)
