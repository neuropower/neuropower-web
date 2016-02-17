from django.shortcuts import render
from django.core.files import File
from django.http import HttpResponse, HttpResponseRedirect
from neuropowertoolbox.forms import ParameterForm, NiftiForm
from django.db import models
from django.conf import settings
from neuropowertoolbox.models import NiftiModel
from neuropower.utils import BUM, cluster, model, neuropower,peakdistribution
from django.forms import model_to_dict
import nibabel as nib
import os
import numpy as np

def home(request):
    return render(request,"home.html",{})

def neuropower(request):
    #/Users/Joke/Documents/Onderzoek/neuropower/neuropower-dev/neuropower/static_in_pro/our_static/img/zstat1.nii.gz
    niftiform = NiftiForm(request.POST or None,default="URL to nifti image")
    context = {
    "niftiform": niftiform,
    }
    if not niftiform.is_valid():
        return render(request,"neuropower.html",context)
    else:
        saveniftiform = niftiform.save()
        request.session["url"] = niftiform.cleaned_data['url']
        request.session["location"] = niftiform.cleaned_data['location']
        return HttpResponseRedirect('/neuropowerviewer/')

def neuropowerviewer(request):
    url = request.session["url"]
    niftiform = NiftiForm(None,default=url)
    parsform = ParameterForm(request.POST or None)
    #print(location)
    #location = request.session["location"]
    #SPM=nib.load(location).get_data()
    #peaks = cluster.cluster(SPM,2.3)
    #print(peaks)
    context = {
    "niftiform": niftiform,
    "parsform": parsform,
    "url": url,
    }
    if not parsform.is_valid():
        return render(request,"neuropowerviewer.html",context)
    else:
        saveparsform = parsform.save()
        request.session = parsform.cleaned_data
        return HttpResponseRedirect('/neuropowertable/')

def neuropowertable(request):
    context = {
    "niftiform": niftiform,
    "parsform": parsform,
    "url": url,
    }
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
