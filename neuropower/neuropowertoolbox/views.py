from __future__ import unicode_literals
from django.shortcuts import render
from django.core.files import File
from django.http import HttpResponse, HttpResponseRedirect
from .forms import ParameterForm, PeakTableForm, MixtureForm, PowerTableForm, PowerForm
from django.db import models
from django.conf import settings
from .models import PeakTableModel, ParameterModel, MixtureModel, PowerTableModel, PowerModel
from neuropower.utils import BUM, cluster, neuropowermodels,peakdistribution, utils
from django.forms import model_to_dict
import nibabel as nib
import os
import numpy as np
from scipy.stats import norm, t
import pandas as pd
import tempfile, shutil, os,urllib
from .plots import plotPower
from nilearn import masking
from django.conf import settings
import uuid

def home(request):
    return render(request,"home.html",{})

def get_session_id(request):
    if not request.session.exists(request.session.session_key):
        request.session.create()
    sid = request.session.session_key
    return(sid)

def neuropower(request):
    sid = get_session_id(request)
    parsform = ParameterForm(
        request.POST or None,
        request.FILES or None,
        default_url="URL to nifti image",
        dim_err=False
    )
    if not request.method=="POST" or not parsform.is_valid():
        context = {"parsform": parsform}
        return render(request,"neuropower.html",context)
    else: #request.method=="POST" AND form is valid
        mapID = str(sid)+"_"+str(uuid.uuid4())
        url = parsform.cleaned_data['url']
        location = utils.create_temporary_copy(url,mapID)
        saveparsform = parsform.save(commit=False)
        saveparsform.SID = sid
        saveparsform.location = location
        saveparsform.save()

        parsdata = ParameterModel.objects.filter(SID=sid)[::-1][0]
        SPM = nib.load(parsdata.location)
        saveparsform.DoF = parsdata.Subj-1 if parsdata.Samples==1 else parsdata.Subj-2
        if parsdata.ZorT=='T':
            SPM = -norm.ppf(t.cdf(-SPM.get_data(),df=float(parsdata.DoF)))
        saveparsform.ExcZ = float(parsdata.Exc) if float(parsdata.Exc)>1 else -norm.ppf(float(parsdata.Exc))
        parsdata.save()

        if parsdata.maskfile == "":
            mask = masking.compute_background_mask(SPM,border_size=2, opening=True)
            nvox = np.sum(mask.get_data())
            saveparsform.nvox = nvox
            saveparsform.save()
            return HttpResponseRedirect('/neuropowerviewer/')
        else:
            mask = os.path.join(settings.MEDIA_ROOT,str(parsdata.maskfile))
            newmask = os.path.join(settings.MEDIA_ROOT,"maps","mask_"+mapID+".nii")
            os.rename(mask,newmask)
            mask = nib.load(newmask)
            if SPM.get_data().shape != mask.get_data().shape:
                parsform = ParameterForm(
                    request.POST or None,
                    request.FILES or None,
                    default_url="URL to nifti image",
                    dim_err=True
                )
                context = {"parsform": parsform}
                return render(request,"neuropower.html",context)
            else:
                nvox = np.sum(mask.get_data())
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
        SPM = nib.load(parsdata.location).get_data()
        peaks = cluster.cluster(SPM,parsdata.ExcZ)
        pvalues = np.exp(-float(parsdata.ExcZ)*(np.array(peaks.peak)-float(parsdata.ExcZ)))
        pvalues = [max(10**(-6),p) for p in pvalues]
        peaks['pval'] = pvalues
        peakform = PeakTableForm()
        savepeakform = peakform.save(commit=False)
        savepeakform.SID = sid
        savepeakform.data = peaks
        savepeakform.save()
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
            powerpred =  {k:1-neuropowermodels.altCDF(v,projected_effect,float(mixdata.sigma),exc=float(parsdata.ExcZ),method="RFT") for k,v in thresholds.items()}
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
