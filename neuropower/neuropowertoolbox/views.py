from __future__ import unicode_literals
import sys
sys.path = sys.path[1:]
from neuropowertoolbox.forms import ParameterForm, PeakTableForm, MixtureForm, PowerTableForm, PowerForm
from neuropowertoolbox.models import PeakTableModel, ParameterModel, MixtureModel, PowerTableModel, PowerModel
from neuropowertoolbox.utils import get_url, get_neuropower_steps, get_db_entries, get_session_id, create_temporary_copy
from neuropower import cluster, BUM, neuropowermodels
from django.http import HttpResponseRedirect
from neuropowertoolbox.plots import plotPower
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
        request.session.flush()
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
    context = {}
    steps = get_neuropower_steps(template,sid)

    parsform = ParameterForm(request.POST or None,
                             request.FILES or None,
                             default_url="URL to nifti image",
                             err="")

    neurovault_id = request.GET.get('neurovault','')
    context["steps"] = steps
    message = request.GET.get('message','')
    context['message'] = message

    # If the user has ended their session, give message
    if end_session == True:
        context["message"] = "Session has been successfully reset."

    if neurovault_id:
        neurovault_image = get_url("http://neurovault.org/api/images/%s/?format=json" %(neurovault_id))
        collection_id = str(neurovault_image['collection_id'])

        if not (neurovault_image['map_type'] == 'Z map' or neurovault_image['map_type'] == 'T map' or neurovault_image['analysis_level']==None):
            context["message"] = "Power analyses can only be performed on Z or T maps."
        if not (neurovault_image['analysis_level'] == 'group' or neurovault_image['analysis_level']==None):
            context["message"] = "Power analyses can only be performed on group statistical maps."

        parsform = ParameterForm(request.POST or None,
                                 request.FILES or None,
                                 default_url = "",
                                 err = '',
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
        form.save()

        # handle data: copy to temporary location
        parsdata = ParameterModel.objects.filter(SID=sid)[::-1][0]
        mapID = "%s_%s" %(str(sid),str(uuid.uuid4()))
        form.mapID = mapID
        if not parsdata.url == "":
            url = parsform.cleaned_data['url']
            location = create_temporary_copy(url,mapID,mask=False,url=True)
        elif not parsdata.spmfile == "":
            spmfile = os.path.join(settings.MEDIA_ROOT,str(parsdata.spmfile))
            location = create_temporary_copy(spmfile,mapID,mask=False, url=False)
        form.location = location
        form.save()
        parsdata = ParameterModel.objects.filter(SID=sid)[::-1][0]
        SPM = nib.load(parsdata.location)
        if len(SPM.shape)>3:
            if not SPM.shape[4]==1 or len(SPM.shape)>4:
                parsform = ParameterForm(request.POST or None,
                                         request.FILES or None,
                                         default_url = "URL to nifti image",
                                         err = "shape")
                context["parsform"] = parsform
                return render(request,template,context)


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
            masklocation = create_temporary_copy(maskfile,mapID,mask=True,url=False)
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
                form.nvox = np.sum(mask)
        form.masklocation = masklocation
        form.save()

        if parsdata.spmfile == "":
            return HttpResponseRedirect('/neuropowerviewer/')
        else:
            return HttpResponseRedirect('/neuropowertable/')


def neuropowerviewer(request):
    # Get the template
    sid = get_session_id(request)
    template = "neuropower/neuropowerviewer.html"
    context = {}

    link = get_db_entries(template,sid)
    if not link == "":
        return HttpResponseRedirect(link)

    parsdata = ParameterModel.objects.filter(SID=sid)[::-1][0]
    if parsdata.url == "":
        context["text"] = "The viewer is only available for publicly available data (specify a url in the input)."
    else:
        context["url"] = parsdata.url
        context["thr"] = parsdata.Exc
        context["viewer"] = "<div class='papaya' data-params='params'></div>"

    context["steps"] = get_neuropower_steps(template,sid)

    return render(request,template,context)

def neuropowertable(request):

    # Get the template/step status
    sid = get_session_id(request)
    template = "neuropower/neuropowertable.html"
    context = {}

    message = request.GET.get('message','')
    context['message'] = message

    link = get_db_entries(template,sid)
    if not link == "":
        return HttpResponseRedirect(link)

    # Initiate peak table
    peakform = PeakTableForm()
    form = peakform.save(commit=False)
    form.SID = sid

    # Load model data
    parsdata = ParameterModel.objects.filter(SID=sid)[::-1][0]

    # Compute peaks
    SPM = nib.load(parsdata.location).get_data()
    MASK = nib.load(parsdata.masklocation).get_data()
    if parsdata.ZorT == 'T':
        SPM = -norm.ppf(t.cdf(-SPM,df=float(parsdata.DoF)))
    peaks = cluster.cluster(SPM,float(parsdata.ExcZ),MASK)

    if len(peaks) < 30:
        context["text"] = "There are too few peaks for a good estimation.  Either the ROI is too small or the screening threshold is too high."
        form.err = context["text"]
    else:
        pvalues = np.exp(-float(parsdata.ExcZ)*(np.array(peaks.peak)-float(parsdata.ExcZ)))
        pvalues = [max(10**(-6),p) for p in pvalues]
        peaks['pval'] = pvalues
        form.data = peaks
        context["peaks"] = peaks.to_html(classes=["table table-striped"])
    form.save()

    # Get step status
    context["steps"] = get_neuropower_steps(template,sid)

    return render(request,template,context)

def neuropowermodel(request):

    # Get the template
    sid = get_session_id(request)
    template = "neuropower/neuropowermodel.html"
    context = {}

    message = request.GET.get('message','')
    context['message'] = message

    link = get_db_entries(template,sid)
    if not link == "":
        return HttpResponseRedirect(link)

    # Load model data
    parsdata = ParameterModel.objects.filter(SID=sid)[::-1][0]
    peakdata = PeakTableModel.objects.filter(SID=sid)[::-1][0]
    if not peakdata.err == "":
        context["text"] = peakdata.err
        return render(request,template,context)
    peaks = peakdata.data

    # Estimate pi1
    bum = BUM.bumOptim(peaks.pval.tolist(),starts=20) # :)
    if bum['pi1']<0.1:
        context['message']=message+"\nWARNING: The estimates prevalence of activation is very low.  The estimation procedure gets rather unstable in this case. Proceed with caution."
    if bum['pi1']==0:
        context['message']=message+"\n The estimated prevalence of activation is zero, which means our model can't find evidence that there is non-null activation in this contrast.  As such, a power analysis will not be possible..."

    # Estimate mixture model
    modelfit = neuropowermodels.modelfit(peaks.peak.tolist(),
                                         bum['pi1'],
                                         exc = float(parsdata.ExcZ),
                                         starts=20,
                                         method="RFT")

    # Save estimates to form
    mixtureform = MixtureForm()
    form = mixtureform.save(commit=False)
    form.SID = sid
    form.pi1 = bum['pi1']
    form.a = bum['a']
    if bum['pi1']>0:
        form.mu = modelfit['mu']
        form.sigma = modelfit['sigma']
    else:
        form.mu = 0
        form.sigma = 0
    form.save()

    # Get step status
    context["steps"] = get_neuropower_steps(template,sid,bum['pi1'])

    return render(request,template,context)

def neuropowersamplesize(request):

    # Get the template/step status
    sid = get_session_id(request)
    template = "neuropower/neuropowersamplesize.html"
    context = {}

    message = request.GET.get('message','')
    context['message'] = message

    link = get_db_entries(template,sid)
    if not link == "":
        return HttpResponseRedirect(link)

    # Load model data
    context['texttop'] = "Hover over the lines to see detailed power predictions"
    parsdata = ParameterModel.objects.filter(SID=sid)[::-1][0]
    peakdata = PeakTableModel.objects.filter(SID=sid)[::-1][0]
    if not peakdata.err == "":
        context["text"] = peakdata.err
        return render(request,template,context)
    mixdata = MixtureModel.objects.filter(SID=sid)[::-1][0]
    peaks = peakdata.data

    powerinputform = PowerForm(request.POST or None)

    if mixdata.mu==0:
        context['message']=message+"\n Our model can't find evidence that there is non-null activation in this contrast.  As such, a power analysis will not be possible..."
    else:
        context["plot"] = True
        if mixdata.pi1<0.1:
            context['message']=message+"\nWARNING: The estimates prevalence of activation is very low.  The estimation procedure gets rather unstable in this case. Proceed with caution."
        # Estimate smoothness
        if parsdata.SmoothEst==1:
            #Manual
            FWHM = np.array([float(parsdata.Smoothx),float(parsdata.Smoothy),float(parsdata.Smoothz)])
            voxsize = np.array([float(parsdata.Voxx),float(parsdata.Voxy),float(parsdata.Voxz)])
        elif parsdata.SmoothEst==2:
            # Estimate from data
            cmd_smooth = "smoothest -V -z "+parsdata.location+" -m "+parsdata.masklocation
            tmp = os.popen(cmd_smooth).read()
            FWHM = np.array([float(x[8:15]) for x in tmp.split("\n")[16].split(",")])
            voxsize=np.array([1,1,1])

        # Compute thresholds and standardised effect size
        thresholds = neuropowermodels.threshold(peaks.peak,peaks.pval,FWHM=FWHM,voxsize=voxsize,nvox=float(parsdata.nvox),alpha=float(parsdata.alpha),exc=float(parsdata.ExcZ))
        effect_cohen = float(mixdata.mu)/np.sqrt(float(parsdata.Subj))

        # Compute predicted power
        power_predicted = []
        newsubs = range(parsdata.Subj,parsdata.Subj+600)
        for s in newsubs:
            projected_effect = float(effect_cohen)*np.sqrt(float(s))
            powerpred =  {k:1-neuropowermodels.altCDF([v],projected_effect,float(mixdata.sigma),exc=float(parsdata.ExcZ),method="RFT")[0] for k,v in thresholds.items() if not v == 'nan'}
            power_predicted.append(powerpred)

        # Check if there are thresholds (mainly BH) missing
        missing = [k for k,v in thresholds.items() if v == 'nan']
        if len(missing) > 0:
            context['MCPwarning']="There is not enough power to estimate a threshold for "+" and ".join(missing)+"."

        # Save power calculation to table and model
        powertable = pd.DataFrame(power_predicted)
        powertable['newsamplesize']=newsubs
        powertableform = PowerTableForm()

        savepowertableform = powertableform.save(commit=False)
        savepowertableform.SID = sid
        savepowertableform.data = powertable
        savepowertableform.save()

        context['plothtml'] = plotPower(sid)['code']

        # Adjust plot with specific power or sample size question
        if request.method == "POST":
            if powerinputform.is_valid():
                savepowerinputform = powerinputform.save(commit=False)
                savepowerinputform.SID = sid
                savepowerinputform.save()
                powerinputdata = PowerModel.objects.filter(SID=sid)[::-1][0]
                pow = float(powerinputdata.reqPow)
                ss = powerinputdata.reqSS
                plotpower = plotPower(sid,powerinputdata.MCP,pow,ss)
                context['plothtml'] = plotpower['code']
                context["textbottom"] = plotpower['text']

    context["powerinputform"] = powerinputform

    # Get step status
    context["steps"] = get_neuropower_steps(template,sid)

    return render(request,template,context)

def neuropowercrosstab(request):

    # Get the template/step status
    sid = get_session_id(request)
    template = "neuropower/neuropowercrosstab.html"
    context = {}

    link = get_db_entries(template,sid)
    if not link == "":
        return HttpResponseRedirect(link)

    mixdata = MixtureModel.objects.filter(SID=sid)[::-1][0]

    if mixdata.mu==0:
        context['message']="\n Our model can't find evidence that there is non-null activation.  As such, a power analysis will not be possible..."
    else:
        context["plot"]
        if mixdata.pi1<0.1:
            context['message']="\nWARNING: The estimates prevalence of activation is very low.  The estimation procedure gets rather unstable in this case. Proceed with caution."

        # Load model data
        peakdata = PeakTableModel.objects.filter(SID=sid)[::-1][0]
        if not peakdata.err == "":
            context["text"] = peakdata.err
            return render(request,template,context)
        powerdata = PowerTableModel.objects.filter(SID=sid)[::-1][0]

        # Restyle power table for export
        names = powerdata.data.columns.tolist()[:-1]
        names.insert(0,'newsamplesize')
        powertable = powerdata.data[names].round(decimals=2)
        repldict = {'BF':'Bonferroni','BH':'Benjamini-Hochberg','UN':'Uncorrected','RFT':'Random Field Theory','newsamplesize':'Samplesize'}
        for word, initial in repldict.items():
            names=[i.replace(word,initial) for i in names]
        powertable.columns=names
        context["power"] = powertable.to_html(index=False,col_space='120px',classes=["table table-striped"])

    # Get step status
    context["steps"] = get_neuropower_steps(template,sid)

    return render(request,template,context)
