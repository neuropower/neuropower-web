from __future__ import unicode_literals
from django.shortcuts import render
from django.core.files import File
from django.http import HttpResponse, HttpResponseRedirect
from .forms import ParameterForm, PeakTableForm, MixtureForm, PowerTableForm
from django.db import models
from django.conf import settings
from .models import PeakTableModel, ParameterModel, MixtureModel, PowerTableModel
from neuropower.utils import BUM, cluster, model, neuropowermodels,peakdistribution
from django.forms import model_to_dict
import nibabel as nib
import os
import numpy as np
from scipy.stats import norm, t
import pandas as pd
import tempfile, shutil, os,urllib
from .plots import plotPower


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
    if not ParameterModel.objects.filter(SID=sid):
        parsform = ParameterForm(request.POST or None,default="URL to nifti image")
        context = {"parsform": parsform}
        if not parsform.is_valid():
            return render(request,"neuropower.html",context)
        else:
            url = parsform.cleaned_data['url']
            location = create_temporary_copy(url,sid)
            saveparsform = parsform.save(commit=False)
            saveparsform.SID = sid
            saveparsform.location = location
            saveparsform.save()
            return HttpResponseRedirect('/neuropowerviewer/')
    else:
        parsform = ParameterForm(request.POST or None,default="URL to nifti image")
        context = {"parsform": parsform}
        return render(request,"neuropower.html",context)

def neuropowerviewer(request):
    sid = get_session_id(request)
    if not ParameterModel.objects.filter(SID=sid):
        context = {
            "text":"Please first fill out the input."
        }
        return render(request,"neuropowerviewer.html",context)
    else:
        sid = request.session.session_key
        parsdata = ParameterModel.objects.filter(SID=sid).reverse()[0]
        context = {
            "url":parsdata.url,
            "viewer":"<div class='papaya' data-params='params'></div>"
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
        if not PeakTableModel.objects.filter(SID=sid):
            parsdata = ParameterModel.objects.filter(SID=sid).reverse()[0]
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
        else:
            peakdata = PeakTableModel.objects.filter(SID=sid).reverse()[0]
            peaks = peakdata.data
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
        return render(request,"neuropowermodel.html",{})

def neuropowersamplesize(request):
    sid = get_session_id(request)
    if not ParameterModel.objects.filter(SID=sid):
        context = {"text":"Please first fill out the 'Data Location' and the 'Data Parameters' in the input."}
        return render(request,"neuropowersamplesize.html",context)
    if not MixtureModel.objects.filter(SID=sid):
        context = {"text":"Please first go to the 'Model Fit' page to initiate and inspect the fit of the mixture model to the distribution."}
        return render(request,"neuropowersamplesize.html",context)
    else:
        #if not PowerTableModel.objects.filter(SID=sid):
        parsdata = ParameterModel.objects.filter(SID=sid).reverse()[0]
        peakdata = PeakTableModel.objects.filter(SID=sid).reverse()[0]
        mixdata = MixtureModel.objects.filter(SID=sid).reverse()[0]
        peaks = peakdata.data
        # should be removed when mask is specified.#######
        SPM=nib.load(parsdata.location).get_data()
        mask = SPM!=0
        maskimg = nib.Nifti1Image(mask.astype(int),np.eye(4))
        ##################################################
        thresholds = neuropowermodels.threshold(peaks.peak,peaks.pval,FWHM=8,mask=maskimg,alpha=0.05,exc=float(parsdata.ExcZ))
        effect_cohen = float(mixdata.mu)/np.sqrt(float(parsdata.Subj))
        power_predicted = []
        newsubs = range(parsdata.Subj,71)
        for s in newsubs:
            projected_effect = float(effect_cohen)*np.sqrt(float(s))
            powerpred =  {k:1-neuropowermodels.altCDF(v,projected_effect,float(mixdata.sigma),exc=float(parsdata.ExcZ),method="RFT") for k,v in thresholds.items() if v!='nan'}
            power_predicted.append(powerpred)
        power_predicted_df = pd.DataFrame(power_predicted)
        power_predicted_df['newsamplesize']=newsubs
        powerform = PowerTableForm()
        savepowerform = powerform.save(commit=False)
        savepowerform.SID = sid
        savepowerform.data = power_predicted_df
        savepowerform.save()
        plothtml = plotPower(sid)
        return render(request,"neuropowersamplesize.html",{"plothtml":plothtml})
