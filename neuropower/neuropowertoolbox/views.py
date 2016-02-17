from __future__ import unicode_literals
from django.shortcuts import render
from django.core.files import File
from django.http import HttpResponse, HttpResponseRedirect
from .forms import ParameterForm, NiftiForm
from django.db import models
from django.conf import settings
from .models import NiftiModel, PeakTableModel
from neuropower.utils import BUM, cluster, model, neuropower,peakdistribution
from django.forms import model_to_dict
import nibabel as nib
import os
import numpy as np
from scipy.stats import norm

def home(request):
    return render(request,"home.html",{})

def neuropower(request):
    niftiform = NiftiForm(request.POST or None,default="URL to nifti image")
    context = {
        "niftiform": niftiform,
    }
    if not niftiform.is_valid():
        return render(request,"neuropower.html",context)
    else:
        saveniftiform = niftiform.save()
        request.session["NiftiID"] = saveniftiform.pk
        return HttpResponseRedirect('/neuropowerviewer/')

def neuropowerviewer(request):
    url = NiftiModel.objects.get(id=request.session["NiftiID"]).url
    location = NiftiModel.objects.get(id=request.session["NiftiID"]).location
    niftiform = NiftiForm(None,default=url)
    parsform = ParameterForm(request.POST or None)
    context = {
        "niftiform": niftiform,
        "parsform": parsform,
        "url":url,
    }
    if not parsform.is_valid():
        return render(request,"neuropowerviewer.html",context)
    else:
        saveparsform = parsform.save()
        request.session["ParsID"] = saveparsform.pk
        pars = parsform.cleaned_data
        dof = [pars['Subj']-1 if pars['Samples']==1 else pars['Subj']-2]
        SPM=nib.load(location).get_data()
        if parsform.cleaned_data['ZorT']=='T':
            SPM = -norm.ppf(t.cdf(-SPM,df=float(dof)))
        excZ = [float(pars['Exc']) if pars['ExcUnits']=='Z' else -norm.ppf(float(pars['Exc']))]
        print(excZ[0])
        print(type(SPM))
        peaks = cluster.cluster(SPM,excZ[0])
        peakfile = PeakTableModel()
        peakfile.data = peaks
        savepeak = peakfile.save()
        return HttpResponseRedirect('/neuropowertable/')

def neuropowertable(request):
    url = NiftiModel.objects.get(id=request.session["NiftiID"]).url
    niftiform = NiftiForm(None,default=url)
    parsform = ParameterForm(None)
    #peaks = PeakTableModel.objects.get(id=request.session["PeakID"]).data
    #print(type(peaks))
    context = {
    "url":url,
    "niftiform": niftiform,
    "parsform": parsform,
    }
    #a = NiftiModel.objects.get(id=request.session["NiftiID"]).url
    #print(a.location)
    return render(request,"neuropowertable.html",context)

def plotpage(request):
    return render(request,"plotpage.html",{})

def plotResults(request):
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    t = np.arange(0.0, 2.0, 0.01)
    s = np.sin(2*np.pi*t)
    fig = plt.figure()
    ax=fig.add_subplot(1,1,1)
    ax.plot(t, s)
    ax.set_xlabel('time (s)')
    ax.set_ylabel('voltage (mV)')
    ax.set_title('About as simple as it gets, folks')
    #ax.grid(True)
    canvas = FigureCanvas(fig)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response
