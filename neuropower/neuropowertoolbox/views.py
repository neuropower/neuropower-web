from __future__ import unicode_literals
from neuropowertoolbox.forms import ParameterForm, PeakTableForm, MixtureForm, PowerTableForm, PowerForm
from neuropowertoolbox.models import PeakTableModel, ParameterModel, MixtureModel, PowerTableModel, PowerModel
from neuropower.utils import BUM, cluster, neuropowermodels,peakdistribution, utils
from neuropowertoolbox.utils import get_url, get_neuropower_steps, get_session_id
from django.http import HttpResponse, HttpResponseRedirect
import matplotlib
from neuropowertoolbox.plots import plotPower
from django.forms import model_to_dict
from django.shortcuts import render
from django.core.files import File
from django.conf import settings
from scipy.stats import norm, t
from django.db import models
from nilearn import masking
import nibabel as nib
import pandas as pd
import numpy as np
import tempfile
import requests
import shutil
import json
import uuid
import os


temp_dir = tempfile.gettempdir()

### MAIN TEMPLATE PAGES ################################################

def home(request):
    return render(request,"main/home.html",{})

def FAQ(request):
    return render(request,"main/FAQ.html",{})

def tutorial(request):
    return render(request,"main/tutorial.html",{})

def methods(request):
    return render(request,"main/methods.html",{})

### SESSION CONTROL

def end_session(request):
    '''ends a session so the user can start a new one.'''
    try:
        sid = request.session.session_key
        del request.session[sid]
    except KeyError:
        pass
    return neuropowerinput(request,end_session=True)

### NEUROPOWER TEMPLATE PAGES

def neuropowerstart(request):
    '''step 1: start'''


    # Get the template/step status
    sid = get_session_id(request)
    template = "neuropower/neuropowerstart.html"
    steps = get_neuropower_steps(template,sid)

    context = {"steps":steps}

    return render(request,template,context)


def neuropowerinput(request,neurovault_id=None,end_session=False):
    '''step 2: input'''

    # Create the session id for the user
    sid = get_session_id(request)

    # Get the template/step status
    template = "neuropower/neuropowerinput.html"
    steps = get_neuropower_steps(template,sid)

    parsform = ParameterForm(request.POST or None,
                             request.FILES or None,
                             default_url="URL to nifti image",
                             err="")

    neurovault_id = request.GET.get('neurovault','')
    context = {"steps":steps}

    # If the user has ended their session, give message
    if end_session == True:
        context["message"] = "Session has been successfully reset."

    if neurovault_id:
        neurovault_image = get_url("http://neurovault.org/api/images/%s/?format=json" %(neurovault_id))
        collection_id = str(neurovault_image['collection_id'])
        neurovault_collection = get_url("http://neurovault.org/api/collections/%s/?format=json" %(collection_id))

        parsform = ParameterForm(request.POST or None,
                                 request.FILES or None,
                                 default_url = "",
                                 err = "",
                                 initial = {"url":neurovault_image["file"],
                                            "ZorT":"T" if neurovault_image["map_type"] =="T map" else "Z",
                                            "Subj":neurovault_image["number_of_subjects"]})
        context["parsform"] = parsform
        return render(request,template,context)

    if not request.method=="POST" or not parsform.is_valid():
        context["parsform"] = parsform
        return render(request,template,context)

    else:
        form = parsform.save(commit=False)
        form.SID = sid
        mapID = "%s_%s" %(str(sid),str(uuid.uuid4()))
        form.mapID = mapID
        peaktable = os.path.join(settings.MEDIA_ROOT,"peaktables","peaks_%s.csv" %(mapID))
        form.peaktable = peaktable
        form.save()

        # handle data: copy to temporary location
        parsdata = ParameterModel.objects.filter(SID=sid)[::-1][0]
        mapID = "%s_%s" %(str(sid),str(uuid.uuid4()))
        form.mapID = mapID
        if not parsdata.url == "":
            url = parsform.cleaned_data['url']
            location = utils.create_temporary_copy(url,mapID,mask=False,url=True)
        elif not parsdata.spmfile == "":
            spmfile = os.path.join(settings.MEDIA_ROOT,str(parsdata.spmfile))
            location = utils.create_temporary_copy(spmfile,mapID,mask=False, url=False)
        form.location = location
        form.save()
        parsdata = ParameterModel.objects.filter(SID=sid)[::-1][0]
        SPM = nib.load(parsdata.location)

        # check if the IQR is realistic (= check whether these are Z- or T-values)
        IQR = np.subtract(*np.percentile(SPM.get_data(),[75,25]))
        if IQR > 20:
            parsform = ParameterForm(request.POST or None,
                                     request.FILES or None,
                                     default_url = "URL to nifti image",
                                     err = "median")
            context["parsform"] = parsform
            return render(request,template,context)

        # save other parameters
        form.DoF = parsdata.Subj-1 if parsdata.Samples==1 else parsdata.Subj-2
        form.ExcZ = float(parsdata.Exc) if float(parsdata.Exc)>1 else -norm.ppf(float(parsdata.Exc))

        # handle mask
        if parsdata.maskfile == "":
            mask = masking.compute_background_mask(SPM,border_size=2, opening=True)
            nvox = np.sum(mask.get_data())
            masklocation = os.path.join(settings.MEDIA_ROOT,"maps/mask_"+mapID+".nii.gz")
            nib.save(mask,masklocation)
            form.nvox = nvox
        else:
            maskfile = os.path.join(settings.MEDIA_ROOT,str(parsdata.maskfile))
            masklocation = utils.create_temporary_copy(maskfile,mapID,mask=True,url=False)
            mask = nib.load(masklocation).get_data()

            # return error when dimensions are different
            if SPM.get_data().shape != mask.shape:
                parsform = ParameterForm(request.POST or None,
                                         request.FILES or None,
                                         default_url="URL to nifti image",
                                         err="dim")
                context["parsform"] = parsform
                return render(request,template,context)
            else:
                SPM_masked = np.multiply(SPM.get_data(),mask)
                SPM_nib = nib.Nifti1Image(SPM_masked,np.eye(4))
                nib.save(SPM_nib,parsdata.location)
                form.nvox = np.sum(mask)
        form.masklocation = masklocation
        form.save()

        if parsdata.spmfile == "":
            return HttpResponseRedirect('/neuropowerviewer/')
        else:
            return HttpResponseRedirect('/neuropowertable/')


def neuropowerviewer(request):

    # Get the template/step status
    sid = get_session_id(request)
    template = "neuropower/neuropowerviewer.html"
    steps = get_neuropower_steps(template,sid)

    viewer = ""
    url = ""
    text = ""
    thr = ""
    if not ParameterModel.objects.filter(SID=sid):
        text = "Please first fill out the input."
    else:
        parsdata = ParameterModel.objects.filter(SID=sid)[::-1][0]
        if parsdata.url == "":
            text = "The viewer is only available for publicly available data (specify a url in the input)."
        else:
            url = parsdata.url
            thr = parsdata.Exc
            viewer = "<div class='papaya' data-params='params'></div>"

    context = {"url":url,
               "viewer":viewer,
               "text":text,
               "thr":thr,
               "steps":steps}

    return render(request,template,context)

def neuropowertable(request):

    # Get the template/step status
    sid = get_session_id(request)
    template = "neuropower/neuropowertable.html"
    steps = get_neuropower_steps(template,sid)
    context = {"steps":steps}

    if not ParameterModel.objects.filter(SID=sid):
        # Should not be able to reach this condition
        context["text"] = "No data found. Go to 'Input' and fill out the form."
        return render(request,template,context)

    else:
        sid = request.session.session_key #why are we getting session id again?
        parsdata = ParameterModel.objects.filter(SID=sid)[::-1][0]
        SPM = nib.load(parsdata.location).get_data()
        if parsdata.ZorT == 'T':
            SPM = -norm.ppf(t.cdf(-SPM,df=float(parsdata.DoF)))
        cluster.cluster(SPM,parsdata.ExcZ,parsdata.peaktable)
        peaks = pd.read_csv(parsdata.peaktable,sep="\t")
        if len(peaks) < 30:
            context["text"] = "There are too few peaks for a good estimation.  Either the ROI is too small or the screening threshold is too high."
        else:
            pvalues = np.exp(-float(parsdata.ExcZ)*(np.array(peaks.peak)-float(parsdata.ExcZ)))
            pvalues = [max(10**(-6),p) for p in pvalues]
            peaks['pval'] = pvalues
            peakform = PeakTableForm()
            form = peakform.save(commit=False)
            form.SID = sid
            form.data = peaks
            form.save()
            context["peaks"] = peaks.to_html(classes=["table table-striped"])

    return render(request,template,context)

def neuropowermodel(request):

    # Get the template/step status
    sid = get_session_id(request)
    template = "neuropower/neuropowermodel.html"
    steps = get_neuropower_steps(template,sid)
    context = {"steps":steps}

    if not ParameterModel.objects.filter(SID=sid):
        # We should not be able to get to this step
        context["text"] = "No data found. Go to 'Input' and fill out the form."
        return render(request,template,context)
    else:
        parsdata = ParameterModel.objects.filter(SID=sid)[::-1][0]
        peakdata = PeakTableModel.objects.filter(SID=sid)[::-1][0]
        peaks = peakdata.data
        bum = BUM.bumOptim(peaks.pval.tolist(),starts=10) # :)

        modelfit = neuropowermodels.modelfit(peaks.peak.tolist(),
                                             bum['pi1'],
                                             exc = float(parsdata.ExcZ),
                                             starts=10,
                                             method="RFT")

        mixtureform = MixtureForm()
        form = mixtureform.save(commit=False)
        form.SID = sid
        form.pi1 = bum['pi1']
        form.a = bum['a']
        form.mu = modelfit['mu']
        form.sigma = modelfit['sigma']
        form.save()
        return render(request,template,context)

def neuropowersamplesize(request):

    # Get the template/step status
    sid = get_session_id(request)
    template = "neuropower/neuropowersamplesize.html"
    steps = get_neuropower_steps(template,sid)
    context = {"steps":steps}

    powerinputform = PowerForm(request.POST or None)

    if not ParameterModel.objects.filter(SID=sid):
        texttop = "No data found. Go to 'Input' and fill out the form."

    elif not MixtureModel.objects.filter(SID=sid):
        texttop = "Before doing any power calculations, the distribution of effects has to be estimated.  Please go to 'Model Fit'to initiate and inspect the fit of the mixture model to the distribution."

    else:
        texttop = "Hover over the lines to see detailed power predictions"
        parsdata = ParameterModel.objects.filter(SID=sid)[::-1][0]
        peakdata = PeakTableModel.objects.filter(SID=sid)[::-1][0]
        mixdata = MixtureModel.objects.filter(SID=sid)[::-1][0]
        peaks = peakdata.data

        # smoothness
        if parsdata.SmoothEst==1:
            #Manual
            FWHM = np.array([parsdata.Smoothx,parsdata.Smoothy,parsdata.Smoothz])
            voxsize = np.array([parsdata.Voxx,parsdata.Voxy,parsdata.Voxz])
        elif parsdata.SmoothEst==2:
            # Estimate from data
            cmd_smooth = "smoothest -V -z "+parsdata.location+" -m "+parsdata.masklocation
            tmp = os.popen(cmd_smooth).read()
            FWHM = np.array([float(x[8:15]) for x in tmp.split("\n")[16].split(",")])
            voxsize=np.array([1,1,1])
        thresholds = neuropowermodels.threshold(peaks.peak,peaks.pval,FWHM=FWHM,voxsize=voxsize,nvox=float(parsdata.nvox),alpha=0.05,exc=float(parsdata.ExcZ))
        print(thresholds)
        effect_cohen = float(mixdata.mu)/np.sqrt(float(parsdata.Subj))
        power_predicted = []
        newsubs = range(parsdata.Subj,301)
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
                pow = float(powerinputdata.reqPow)
                ss = powerinputdata.reqSS
                plotpower = plotPower(sid,powerinputdata.MCP,pow,ss)
                plothtml = plotpower['code']
                context["textbottom"] = plotpower['text']

    context["texttop"] = texttop
    context["plothtml"] = plothtml
    context["powerinputform"] = powerinputform

    return render(request,template,context)

def neuropowercrosstab(request):

    # Get the template/step status
    sid = get_session_id(request)
    template = "neuropower/neuropowercrosstab.html"
    steps = get_neuropower_steps(template,sid)
    context = {"steps":steps}

    powerinputform = PowerForm(request.POST or None)

    if not MixtureModel.objects.filter(SID=sid):
        context["text"] = "Before doing any power calculations, the distribution of effects has to be estimated.  Please go to 'Model Fit'to initiate and inspect the fit of the mixture model to the distribution."


    if not ParameterModel.objects.filter(SID=sid):
        context["text"] = "No data found. Go to 'Input' and fill out the form."

    else:
        powerdata = PowerTableModel.objects.filter(SID=sid)[::-1][0]
        powertable = powerdata.data[['newsamplesize','RFT','BF','BH','UN']].round(decimals=2)
        powertable.columns=['Sample Size','Random Field Theory','Bonferroni','Benjamini-Hochberg','Uncorrected']
        context["power"] = powertable.to_html(index=False,col_space='120px',classes=["table table-striped"])

    return render(request,template,context)
