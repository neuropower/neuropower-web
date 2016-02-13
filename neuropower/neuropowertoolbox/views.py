from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from .forms import ParameterForm, NiftiForm
# Create your views here.

def home(request):
    return render(request,"home.html",{})

def neuropower(request):
    niftiform = NiftiForm(request.POST or None,default="URL to nifti image")
    parsform = ParameterForm(None)
    context = {
    "niftiform": niftiform,
    "parsform": parsform
    }
    if niftiform.is_valid():
        url = niftiform.cleaned_data['file']
        return HttpResponseRedirect('/neuropowerviewer')
        print(url)
    else:
        niftiform=NiftiForm(request.POST)
    return render(request,"neuropower.html",context)

def neuropowerviewer(request):
    niftiform = NiftiForm(request.POST or None,default="URL to nifti image")
    parsform = ParameterForm(request.POST or None)
    context = {
    "niftiform": niftiform,
    "parsform": parsform
    }
    if parsform.is_valid():
        niftidata = niftiform.cleaned_data
        print(niftidata)
        parsform=ParameterForm(request.POST or None)
        context = {
        "niftiform":niftiform,
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
