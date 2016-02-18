from django.http import HttpResponse, HttpResponseRedirect
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from neuropower.utils import BUM, cluster, model, peakdistribution
from neuropower.utils import neuropowermodels as npm
from palettable.colorbrewer.qualitative import Paired_12
import scipy
import matplotlib as mpl
from .models import MixtureModel, ParameterModel, PeakTableModel

def plotModel(request):
    if not request.session.exists(request.session.session_key):
        request.session.create()
    sid = request.session.session_key
    mixdata = MixtureModel.objects.filter(SID=sid).reverse()[0]
    parsdata = ParameterModel.objects.filter(SID=sid).reverse()[0]
    peakdata = PeakTableModel.objects.filter(SID=sid).reverse()[0]
    peaks = peakdata.data
    twocol = Paired_12.mpl_colors
    xn = np.arange(-10,10,0.01)
    nul = [1-float(mixdata.pi1)]*npm.nulPDF(xn,exc=float(parsdata.ExcZ),method="RFT")
    alt = float(mixdata.pi1)*npm.altPDF(xn,mu=float(mixdata.mu),sigma=float(mixdata.sigma),exc=float(parsdata.ExcZ),method="RFT")
    mix = npm.mixprobdens(xn,pi1=float(mixdata.pi1),mu=float(mixdata.mu),sigma=float(mixdata.sigma),exc=2,method="RFT")
    xn_p = np.arange(0,1,0.01)
    alt_p = [1-float(mixdata.pi1)]*scipy.stats.beta.pdf(xn_p, float(mixdata.a), 1)+1-float(mixdata.pi1)
    print(alt_p)
    null_p = [1-float(mixdata.pi1)]*len(xn_p)
    mpl.rcParams['font.size']='11.0'

    fig,axs=plt.subplots(1,2,figsize=(14,5))
    fig.patch.set_facecolor('None')
    fig.subplots_adjust(hspace=.5,wspace=0.3)
    axs=axs.ravel()

    axs[0].hist(peaks.pval,lw=0,normed=True,facecolor=twocol[0],bins=np.arange(0,1.1,0.1),label="observed distribution")
    axs[0].set_ylim([0,3])
    axs[0].plot(xn_p,null_p,color=twocol[3],lw=2,label="null distribution")
    axs[0].plot(xn_p,alt_p,color=twocol[5],lw=2,label="alternative distribution")
    axs[0].legend(loc="upper right",frameon=False)
    axs[0].set_title("Distribution of "+str(len(peaks))+" peak p-values \n $\pi_1$ = "+str(round(float(mixdata.pi1),2)))
    axs[0].set_xlabel("Peak p-values")
    axs[0].set_ylabel("Density")

    axs[1].hist(peaks.peak,lw=0,facecolor=twocol[0],normed=True,bins=np.arange(2,10,0.3),label="observed distribution")
    axs[1].set_xlim([2,7])
    axs[1].set_ylim([0,1])
    axs[1].plot(xn,nul,color=twocol[3],lw=2,label="null distribution")
    axs[1].plot(xn,alt,color=twocol[5],lw=2, label="alternative distribution")
    axs[1].plot(xn,mix,color=twocol[1],lw=2,label="total distribution")
    axs[1].set_title("Distribution of peak heights \n $\delta_1$ = "+str(round(float(mixdata.mu)/np.sqrt(parsdata.Subj),2)))
    axs[1].set_xlabel("Peak heights (z-values)")
    axs[1].set_ylabel("Density")
    axs[1].legend(loc="upper right",frameon=False)
    canvas = FigureCanvas(fig)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response
