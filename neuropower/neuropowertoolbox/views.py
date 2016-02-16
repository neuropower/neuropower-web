from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from neuropowertoolbox.forms import ParameterForm, NiftiForm
from django.db import models
from django.conf import settings
from neuropowertoolbox.models import NiftiModel
from neuropower.utils import BUM, cluster, model, neuropower,peakdistribution
import nibabel as nib
import os

def home(request):
    return render(request,"home.html",{})

def neuropower(request):
    niftiform = NiftiForm(request.POST or None,default="URL to nifti image")
    parsform = ParameterForm(None)
    context = {
    "niftiform": niftiform,
    "parsform": parsform
    }
    if not niftiform.is_valid():
        niftiform=NiftiForm(request.POST)
        return render(request,"neuropower.html",context)
    else:
        newform = niftiform.save()
        request.session["url"] = niftiform.cleaned_data['file']
        return HttpResponseRedirect('/neuropowerviewer')

def neuropowerviewer(request):
    url = request.session["url"]
    niftiform2 = NiftiForm(request.POST or None,default=url)
    parsform = ParameterForm(request.POST or None)
    context = {
    "niftiform": niftiform2,
    "parsform": parsform,
    "url": url
    }
    ## THIS PART SHOULD BE REMOVED AND GET THE REAL FILE!! ##########
    name="zstat1.nii.gz"
    new_name = os.path.join(settings.STATICFILES_DIRS[0],"img",name)
    SPM=nib.load(new_name).get_data()
    #################################################################

    if parsform.is_valid():
        niftidata = niftiform2.cleaned_data
        print(niftidata)
        parsform=ParameterForm(request.POST or None)
        context = {
        "niftiform":niftiform2,
        "parsform": parsform
        }
    return render(request,"neuropowerviewer.html",context)

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
