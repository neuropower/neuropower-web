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
import tempfile

temp_dir = tempfile.gettempdir()

def home(request):
    return render(request,"home.html",{})

def get_session_id(request):
    if not request.session.exists(request.session.session_key):
        request.session.create()
    sid = request.session.session_key
    return(sid)

def neuropowerstart(request):
    return render(request,"neuropowerstart.html",{})

def FAQ(request):
    return render(request,"FAQ.html",{})

def tutorial(request):
    return render(request,"tutorial.html",{})

def methods(request):
    return render(request,"methods.html",{})

def neuropowerinput(request):
    sid = get_session_id(request)
    parsform = ParameterForm(
        request.POST or None,
        request.FILES or None,
        default_url="URL to nifti image",
        err=""
    )

    if not request.method=="POST" or not parsform.is_valid():
        context = {"parsform": parsform}
        return render(request,"neuropowerinput.html",context)

    else:
        saveparsform = parsform.save(commit=False)
        saveparsform.SID = sid
        saveparsform.save()

        # handle data: copy to temporary location
        parsdata = ParameterModel.objects.filter(SID=sid)[::-1][0]
        mapID = str(sid)+"_"+str(uuid.uuid4())
        if not parsdata.url == "":
            url = parsform.cleaned_data['url']
            location = utils.create_temporary_copy(url,mapID,mask=False,url=True)
        elif not parsdata.spmfile == "":
            spmfile = os.path.join(settings.MEDIA_ROOT,str(parsdata.spmfile))
            location = utils.create_temporary_copy(spmfile,mapID,mask=False, url=False)
        saveparsform.location = location
        saveparsform.save()
        parsdata = ParameterModel.objects.filter(SID=sid)[::-1][0]
        SPM = nib.load(parsdata.location)

        # check if the IQR is realistic (= check whether these are Z- or T-values)
        IQR = np.subtract(*np.percentile(SPM.get_data(),[75,25]))
        if IQR > 20:
            parsform = ParameterForm(
                request.POST or None,
                request.FILES or None,
                default_url="URL to nifti image",
                err="median",
                )
            context = {"parsform": parsform}
            return render(request,"neuropowerinput.html",context)

        # save other parameters
        saveparsform.DoF = parsdata.Subj-1 if parsdata.Samples==1 else parsdata.Subj-2
        saveparsform.ExcZ = float(parsdata.Exc) if float(parsdata.Exc)>1 else -norm.ppf(float(parsdata.Exc))

        # handle mask
        if parsdata.maskfile == "":
            mask = masking.compute_background_mask(SPM,border_size=2, opening=True)
            nvox = np.sum(mask.get_data())
            saveparsform.nvox = nvox
        else:
            maskfile = os.path.join(settings.MEDIA_ROOT,str(parsdata.maskfile))
            masklocation = utils.create_temporary_copy(maskfile,mapID,mask=True,url=False)
            mask = nib.load(masklocation).get_data()

            # return error when dimensions are different
            if SPM.get_data().shape != mask.shape:
                parsform = ParameterForm(
                    request.POST or None,
                    request.FILES or None,
                    default_url="URL to nifti image",
                    err="dim",
                )
                context = {"parsform": parsform}
                return render(request,"neuropowerinput.html",context)
            else:
                SPM_masked = np.multiply(SPM.get_data(),mask)
                SPM_nib = nib.Nifti1Image(SPM_masked,np.eye(4))
                nib.save(SPM_nib,parsdata.location)
                saveparsform.nvox = np.sum(mask)
        saveparsform.save()
        return HttpResponseRedirect('/neuropowerviewer/') if parsdata.spmfile == "" else HttpResponseRedirect('/neuropowertable/')


def neuropowerviewer(request):
    sid = get_session_id(request)
    viewer = ""
    url = ""
    text = ""
    if not ParameterModel.objects.filter(SID=sid):
        text = "Please first fill out the input."
    else:
        parsdata = ParameterModel.objects.filter(SID=sid)[::-1][0]
        if parsdata.url == "":
            text = "The viewer is only available for publicly available data (specify a url in the input)."
        else:
            url = parsdata.url
            viewer = "<div class='papaya' data-params='params'></div>"

    context = {
        "url":url,
        "viewer":viewer,
        "text":text
    }

    return render(request,"neuropowerviewer.html",context)

def neuropowertable(request):
    sid = get_session_id(request)
    if not ParameterModel.objects.filter(SID=sid):
        context = {"text":"No data found. Go to 'Input' and fill out the form."}
        return render(request,"neuropowertable.html",context)
    else:
        sid = request.session.session_key
        parsdata = ParameterModel.objects.filter(SID=sid)[::-1][0]
        SPM = nib.load(parsdata.location).get_data()
        if parsdata.ZorT=='T':
            SPM = -norm.ppf(t.cdf(-SPM,df=float(parsdata.DoF)))
        print("noproblem?")
        peaks = cluster.cluster(SPM,parsdata.ExcZ)
        print("problem?")
        pvalues = np.exp(-float(parsdata.ExcZ)*(np.array(peaks.peak)-float(parsdata.ExcZ)))
        pvalues = [max(10**(-6),p) for p in pvalues]
        peaks['pval'] = pvalues
        peakform = PeakTableForm()
        savepeakform = peakform.save(commit=False)
        savepeakform.SID = sid
        savepeakform.data = peaks
        savepeakform.save()
        context = {"peaks":peaks.to_html(classes=["table table-striped"])}
    return render(request,"neuropowertable.html",context)

def neuropowermodel(request):
    sid = get_session_id(request)
    if not ParameterModel.objects.filter(SID=sid):
        context = {"text":"No data found. Go to 'Input' and fill out the form."}
        return render(request,"neuropowermodel.html",context)
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

    if not MixtureModel.objects.filter(SID=sid):
        texttop = "Before doing any power calculations, the distribution of effects has to be estimated.  Please go to 'Model Fit'to initiate and inspect the fit of the mixture model to the distribution."
        plothtml = ""
        textbottom = ""

    if not ParameterModel.objects.filter(SID=sid):
        texttop = "No data found. Go to 'Input' and fill out the form."
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

def neuropowercrosstab(request):

    sid = get_session_id(request)
    powerinputform = PowerForm(request.POST or None)

    if not MixtureModel.objects.filter(SID=sid):
        text = "Before doing any power calculations, the distribution of effects has to be estimated.  Please go to 'Model Fit'to initiate and inspect the fit of the mixture model to the distribution."
        context = {"text":text}

    if not ParameterModel.objects.filter(SID=sid):
        text = "No data found. Go to 'Input' and fill out the form."
        context = {"text":text}

    else:
        powerdata = PowerTableModel.objects.filter(SID=sid)[::-1][0]
        powertable = powerdata.data[['newsamplesize','RFT','BF','BH','UN']].round(decimals=2)
        powertable.columns=['Sample Size','Random Field Theory','Bonferroni','Benjamini-Hochberg','Uncorrected']
        context = {"power":powertable.to_html(index=False,col_space='120px',classes=["table table-striped"])}

    return render(request,"neuropowercrosstab.html",context)
