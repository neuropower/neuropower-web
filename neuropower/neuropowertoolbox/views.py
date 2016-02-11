from django.shortcuts import render
from django.http import HttpResponse
from .forms import SimpleForm, CartForm, CreditCardForm,ParameterForm, NiftiForm
# Create your views here.

def home(request):
    return render(request,"home.html",{})

def neuropower(request):
    form = NiftiForm(request.POST or None)
    context = {"form":form}
    if form.is_valid():
        context={"title":"Thank you"}
    return render(request,"neuropower.html",context)

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
