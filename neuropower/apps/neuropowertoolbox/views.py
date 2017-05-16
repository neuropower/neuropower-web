from __future__ import unicode_literals
import sys
sys.path = sys.path[1:]
from .forms import ParameterForm, PeakTableForm, MixtureForm, PowerTableForm, PowerForm
from .models import NeuropowerModel
from .utils import get_url, get_neuropower_steps, get_db_entries, get_session_id, create_local_copy, get_neurovault_form
from neuropowercore import cluster, BUM, neuropowermodels
from django.http import HttpResponseRedirect
from plots import plotPower, plotModel
from django.shortcuts import render
from django.conf import settings
from scipy.stats import norm, t
from nilearn import masking
import nibabel as nib
import pandas as pd
import numpy as np
import tempfile
import uuid
import os

temp_dir = tempfile.gettempdir()

## MAIN PAGE TEMPLATE PAGES

def npFAQ(request):
    return render(request,"neuropower/neuropowerFAQ.html",{})

def tutorial(request):
    return render(request,"neuropower/tutorial.html",{})

def methods(request):
    return render(request,"neuropower/methods.html",{})

### SESSION CONTROL

def end_session(request):
    '''ends a session so the user can start a new one.'''
    try:
        request.session.flush()
    except KeyError:
        pass
    return neuropowerstart(request)

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

    # get DB entry for sid
    try:
        neuropowerdata = NeuropowerModel.objects.get(SID=sid)
    except NeuropowerModel.DoesNotExist:
        neuropowerdata = None

    # Get the template/step status
    template = "neuropower/neuropowerinput.html"
    context = {}
    steps = get_neuropower_steps(template,sid)
    context["steps"] = steps

    # Initiate parameter form
    parsform = ParameterForm(request.POST or None,
                             request.FILES or None,
                             instance=neuropowerdata,
                             default_url="URL to nifti image",
                             err="")

    # Check if a message is passed
    message = request.GET.get('message','')
    context['message'] = message

    # Check if redirect from neurovault
    neurovault_id = request.GET.get('neurovault','')

    if neurovault_id:
        neurovault_data = get_neurovault_form(request,neurovault_id)

        context['parsform'] = neurovault_data["parsform"]
        if not neurovault_data["message"] == None:
            context['message'] = neurovault_data["message"]

        return render(request,template,context)

    # Check if new user or if parameterform is invalid
    if not request.method=="POST" or not parsform.is_valid():
        context["parsform"] = parsform

        return render(request,template,context)

    else:
        form = parsform.save(commit = False)
        form.SID = sid
        form.save()

        # handle data: copy to local drive

        neuropowerdata = NeuropowerModel.objects.get(SID=sid)

        # create folder to save map local

        if not os.path.exists("/var/maps/"):
            os.mkdir("/var/maps/")

        # make local copies of map and mask

        map_local = "/var/maps/"+sid+"_map"
        mask_local = "/var/maps/"+sid+"_mask"

        if not neuropowerdata.map_url == "":
            map_url = neuropowerdata.map_url
        else:
            map_url = "https://"+settings.AWS_S3_CUSTOM_DOMAIN+str(neuropowerdata.spmfile.name)

        map_local = create_local_copy(map_url,map_local)

        if not neuropowerdata.maskfile == "":
            mask_url = "https://"+settings.AWS_S3_CUSTOM_DOMAIN+str(neuropowerdata.maskfile.name)
            mask_local = create_local_copy(mask_url,mask_local)

        # save map locations to database

        form = parsform.save(commit = False)
        form.map_url = map_url
        form.map_local = map_local
        if not neuropowerdata.maskfile == "":
            form.mask_url = mask_url
            form.mask_local = mask_local
        else:
            form.mask_local = mask_local
        form.save()

        # perform some higher level cleaning

        error = None

        neuropowerdata = NeuropowerModel.objects.get(SID=sid)
        SPM = nib.load(neuropowerdata.map_local)
        if len(SPM.shape)>3:
            if not SPM.shape[3]==1 or len(SPM.shape)>4:
                error = "shape"

        # check if the IQR is realistic (= check whether these are Z- or T-values)
        IQR = np.subtract(*np.percentile(SPM.get_data(),[75,25]))
        if IQR > 20:
            error = "median"

        # save other parameters

        form.DoF = neuropowerdata.Subj-1 if neuropowerdata.Samples==1 else neuropowerdata.Subj-2
        form.ExcZ = float(neuropowerdata.Exc) if float(neuropowerdata.Exc)>1 else -norm.ppf(float(neuropowerdata.Exc))

        # if mask does not exist: create
        if neuropowerdata.maskfile == "":
            mask = masking.compute_background_mask(SPM,border_size=2, opening=True)
            nvox = np.sum(mask.get_data())
            form.mask_local = neuropowerdata.mask_local+".nii.gz"
            nib.save(mask,form.mask_local)
            form.nvox = nvox
        # if mask is given: check dimensions
        else:
            mask = nib.load(neuropowerdata.mask_local).get_data()
            if SPM.get_data().shape != mask.shape:
                error = "dim"
            else:
                form.nvox = np.sum(mask)

        # throw error if detected
        if error:
            parsform = ParameterForm(request.POST or None,
                                     request.FILES or None,
                                     default_url="URL to nifti image",
                                     err=error)
            context["parsform"] = parsform
            return render(request,template,context)
        else:
            form.step = 1
            form.save()

        return HttpResponseRedirect('../neuropowertable/')

def neuropowerviewer(request):

    # Create the session id for the user
    sid = get_session_id(request)

    # get DB entry for sid
    try:
        neuropowerdata = NeuropowerModel.objects.get(SID=sid)
    except NeuropowerModel.DoesNotExist:
        neuropowerdata = None

    # Get the template/step status
    template = "neuropower/neuropowerviewer.html"
    context = {}
    steps = get_neuropower_steps(template,sid)
    context["steps"] = steps

    # check for unauthorised page visit
    link = get_db_entries(template,sid)
    if not link == "":
        return HttpResponseRedirect(link)

    context["url"] = neuropowerdata.map_url
    context["thr"] = neuropowerdata.Exc
    context["viewer"] = "<div class='papaya' data-params='params'></div>"

    return render(request,template,context)

def neuropowertable(request):

    # Create the session id for the user
    sid = get_session_id(request)

    # get DB entry for sid
    try:
        neuropowerdata = NeuropowerModel.objects.get(SID=sid)
    except NeuropowerModel.DoesNotExist:
        neuropowerdata = None

    # Get the template/step status
    template = "neuropower/neuropowertable.html"
    context = {}
    steps = get_neuropower_steps(template,sid)
    context["steps"] = steps

    link = get_db_entries(template,sid)
    if not link == "":
        return HttpResponseRedirect(link)

    # Check if a message is passed
    message = request.GET.get('message','')
    context['message'] = message

    # Initiate peak table
    peakform = PeakTableForm(instance = neuropowerdata)
    form = peakform.save(commit=False)
    form.SID = sid

    # Compute peaks
    SPM = nib.load(neuropowerdata.map_local).get_data()
    MASK = nib.load(neuropowerdata.mask_local).get_data()
    if neuropowerdata.ZorT == 'T':
        SPM = -norm.ppf(t.cdf(-SPM,df=float(neuropowerdata.DoF)))
    peaks = cluster.PeakTable(SPM,float(neuropowerdata.ExcZ),MASK)

    if len(peaks) < 30:
        context["text"] = "There are too few peaks for a good estimation.  Either the ROI is too small or the screening threshold is too high."
        form.err = context["text"]
    else:
        pvalues = np.exp(-float(neuropowerdata.ExcZ)*(np.array(peaks.peak)-float(neuropowerdata.ExcZ)))
        pvalues = [max(10**(-6),p) for p in pvalues]
        peaks['pval'] = pvalues
        form.peaktable = peaks
        context["peaks"] = peaks.to_html(classes=["table table-striped"])
        form.step = 2
    form.save()

    return render(request,template,context)

def neuropowermodel(request):

    # Create the session id for the user
    sid = get_session_id(request)

    # get DB entry for sid
    try:
        neuropowerdata = NeuropowerModel.objects.get(SID=sid)
    except NeuropowerModel.DoesNotExist:
        neuropowerdata = None

    # Get the template/step status
    template = "neuropower/neuropowermodel.html"
    context = {}
    steps = get_neuropower_steps(template,sid)
    context["steps"] = steps

    link = get_db_entries(template,sid)
    if not link == "":
        return HttpResponseRedirect(link)

    peaks = neuropowerdata.peaktable

    # Check if a message is passed
    message = request.GET.get('message','')
    context['message'] = message

    # Estimate pi1
    bum = BUM.EstimatePi1(peaks.pval.tolist(),starts=20) # :)
    if bum['pi1']<0.1:
        context['message']=message+"\nWARNING: The estimates prevalence of activation is very low.  The estimation procedure gets rather unstable in this case. Proceed with caution."
    if bum['pi1']==0:
        context['message']=message+"\n The estimated prevalence of activation is zero, which means our model can't find evidence that there is non-null activation in this contrast.  As such, a power analysis will not be possible..."

    # Estimate mixture model
    modelfit = neuropowermodels.modelfit(peaks.peak.tolist(),
                                         bum['pi1'],
                                         exc = float(neuropowerdata.ExcZ),
                                         starts=20,
                                         method="RFT")

    # Save estimates to form
    mixtureform = MixtureForm(instance = neuropowerdata)
    form = mixtureform.save(commit=False)
    form.SID = sid
    form.pi1 = bum['pi1']
    form.a = bum['a']
    if bum['pi1']>0:
        form.mu = modelfit['mu']
        form.sigma = modelfit['sigma']
        form.step = 3
    else:
        form.mu = 0
        form.sigma = 0
    form.save()

    # context["link"] = plotModel(sid)

    return render(request,template,context)

def neuropowersamplesize(request):

    # Create the session id for the user
    sid = get_session_id(request)

    # get DB entry for sid
    try:
        neuropowerdata = NeuropowerModel.objects.get(SID=sid)
    except NeuropowerModel.DoesNotExist:
        neuropowerdata = None

    # Get the template/step status
    template = "neuropower/neuropowersamplesize.html"
    context = {}
    steps = get_neuropower_steps(template,sid)
    context["steps"] = steps

    link = get_db_entries(template,sid)
    if not link == "":
        return HttpResponseRedirect(link)

    # Check if a message is passed
    message = request.GET.get('message','')
    context['message'] = message


    # Load model data
    context['texttop'] = "Hover over the lines to see detailed power predictions"
    if not neuropowerdata.err == "":
        context["text"] = neuropowerdata.err
        return render(request,template,context)
    peaks = neuropowerdata.peaktable

    powerinputform = PowerForm(request.POST or None,instance=neuropowerdata)

    if neuropowerdata.mu==0:
        context['message']=message+"\n Our model can't find evidence that there is non-null activation in this contrast.  As such, a power analysis will not be possible..."
    else:
        context["plot"] = True
        if neuropowerdata.pi1<0.1:
            context['message']=message+"\nWARNING: The estimates prevalence of activation is very low.  The estimation procedure gets rather unstable in this case. Proceed with caution."
        # Estimate smoothness
        if neuropowerdata.SmoothEst==1:
            #Manual
            FWHM = np.array([float(neuropowerdata.Smoothx),float(neuropowerdata.Smoothy),float(neuropowerdata.Smoothz)])
            voxsize = np.array([float(neuropowerdata.Voxx),float(neuropowerdata.Voxy),float(neuropowerdata.Voxz)])
        elif neuropowerdata.SmoothEst==2:
            # Estimate from data
            cmd_smooth = "smoothest -V -z "+neuropowerdata.map_local+" -m "+neuropowerdata.mask_local
            tmp = os.popen(cmd_smooth).read()
            FWHM = np.array([float(x[8:15]) for x in tmp.split("\n")[16].split(",")])
            voxsize=np.array([1,1,1])

        # Compute thresholds and standardised effect size
        thresholds = neuropowermodels.threshold(peaks.peak,peaks.pval,FWHM=FWHM,voxsize=voxsize,nvox=float(neuropowerdata.nvox),alpha=float(neuropowerdata.alpha),exc=float(neuropowerdata.ExcZ))
        effect_cohen = float(neuropowerdata.mu)/np.sqrt(float(neuropowerdata.Subj))

        # Compute predicted power
        power_predicted = []
        newsubs = range(neuropowerdata.Subj,neuropowerdata.Subj+600)
        for s in newsubs:
            projected_effect = float(effect_cohen)*np.sqrt(float(s))
            powerpred =  {k:1-neuropowermodels.altCDF([v],projected_effect,float(neuropowerdata.sigma),exc=float(neuropowerdata.ExcZ),method="RFT")[0] for k,v in thresholds.items() if not v == 'nan'}
            power_predicted.append(powerpred)

        # Check if there are thresholds (mainly BH) missing
        missing = [k for k,v in thresholds.items() if v == 'nan']
        if len(missing) > 0:
            context['MCPwarning']="There is not enough power to estimate a threshold for "+" and ".join(missing)+"."

        # Save power calculation to table and model
        powertable = pd.DataFrame(power_predicted)
        powertable['newsamplesize']=newsubs
        powertableform = PowerTableForm(instance=neuropowerdata)

        savepowertableform = powertableform.save(commit=False)
        savepowertableform.SID = sid
        savepowertableform.data = powertable
        savepowertableform.step = 4
        savepowertableform.save()

        context['plothtml'] = plotPower(sid)['code']

        # Adjust plot with specific power or sample size question
        if request.method == "POST":
            if powerinputform.is_valid():
                savepowerinputform = powerinputform.save(commit=False)
                savepowerinputform.SID = sid
                savepowerinputform.save()
                neuropowerdata = NeuropowerModel.objects.get(SID=sid)
                pow = float(neuropowerdata.reqPow)
                ss = neuropowerdata.reqSS
                plotpower = plotPower(sid,neuropowerdata.MCP,pow,ss)
                context['plothtml'] = plotpower['code']
                context["textbottom"] = plotpower['text']

    context["powerinputform"] = powerinputform

    return render(request,template,context)

def neuropowercrosstab(request):

    # Create the session id for the user
    sid = get_session_id(request)

    # get DB entry for sid
    try:
        neuropowerdata = NeuropowerModel.objects.get(SID=sid)
    except NeuropowerModel.DoesNotExist:
        neuropowerdata = None

    # Get the template/step status
    template = "neuropower/neuropowercrosstab.html"
    context = {}
    steps = get_neuropower_steps(template,sid)
    context["steps"] = steps

    link = get_db_entries(template,sid)
    if not link == "":
        return HttpResponseRedirect(link)

    # Check if a message is passed
    message = request.GET.get('message','')
    context['message'] = message

    if neuropowerdata.mu==0:
        context['message']="\n Our model can't find evidence that there is non-null activation.  As such, a power analysis will not be possible..."
    else:
        if neuropowerdata.pi1<0.1:
            context['message']="\nWARNING: The estimates prevalence of activation is very low.  The estimation procedure gets rather unstable in this case. Proceed with caution."

        # Load model data
        if not neuropowerdata.err == "":
            context["text"] = peakdata.err
            return render(request,template,context)

        # Restyle power table for export
        names = neuropowerdata.data.columns.tolist()[:-1]
        names.insert(0,'newsamplesize')
        powertable = neuropowerdata.data[names].round(decimals=2)
        repldict = {'BF':'Bonferroni','BH':'Benjamini-Hochberg','UN':'Uncorrected','RFT':'Random Field Theory','newsamplesize':'Samplesize'}
        for word, initial in repldict.items():
            names=[i.replace(word,initial) for i in names]
        powertable.columns=names
        context["power"] = powertable.to_html(index=False,col_space='120px',classes=["table table-striped"])

    return render(request,template,context)
