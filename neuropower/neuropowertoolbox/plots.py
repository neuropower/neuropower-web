from django.http import HttpResponse, HttpResponseRedirect
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from neuropower.utils import BUM, cluster, model, peakdistribution
from neuropower.utils import neuropowermodels as npm
from palettable.colorbrewer.qualitative import Paired_12,Set1_9
import scipy
from .views import get_session_id
import matplotlib as mpl
from .models import MixtureModel, ParameterModel, PeakTableModel, PowerTableModel

def plotModel(request):
    plt.switch_backend('agg')
    sid = get_session_id(request)
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

    axs[1].hist(peaks.peak,lw=0,facecolor=twocol[0],normed=True,bins=np.arange(min(peaks.peak),10,0.3),label="observed distribution")
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

def plotPower(request):
    plt.switch_backend('agg')
    sid = get_session_id(request)
    powerdata = PowerTableModel.objects.filter(SID=sid).reverse()[0]
    power_predicted_df = powerdata.data
    colset1 = Set1_9.mpl_colors
    parsdata = ParameterModel.objects.filter(SID=sid).reverse()[0]
    sub = float(parsdata.Subj)
    newsubs = power_predicted_df['newsamplesize']
    BFmin = np.min([i for i,elem in enumerate(power_predicted_df['BF']>0.8,1) if elem])+sub
    RFTmin = np.min([i for i,elem in enumerate(power_predicted_df['RFT']>0.8,1) if elem])+sub
    BHmin = np.min([i for i,elem in enumerate(power_predicted_df['BH']>0.8,1) if elem])+sub
    UNmin = np.min([i for i,elem in enumerate(power_predicted_df['UN']>0.8,1) if elem])+sub
    fig,axs=plt.subplots(1,1,figsize=(8,5))
    fig.patch.set_facecolor('None')
    # axs.plot([RFTmin,RFTmin],[0,power_predicted_df['RFT'][RFTmin-sub]],color=colset1[2])
    # axs.plot([sub,RFTmin],[power_predicted_df['RFT'][RFTmin-sub],power_predicted_df['RFT'][RFTmin-sub]],color=colset1[2])
    # axs.plot([BFmin,BFmin],[0,power_predicted_df['BF'][BFmin-sub]],color=colset1[0])
    # axs.plot([sub,BFmin],[power_predicted_df['BF'][BFmin-sub],power_predicted_df['BF'][BFmin-sub]],color=colset1[0])
    # axs.plot([BHmin,BHmin],[0,power_predicted_df['BH'][BHmin-sub]],color=colset1[1])
    # axs.plot([sub,BHmin],[power_predicted_df['BH'][BHmin-sub],power_predicted_df['BH'][BHmin-sub]],color=colset1[1])
    # axs.plot([UNmin,UNmin],[0,power_predicted_df['UN'][UNmin-sub]],color=colset1[3])
    # axs.plot([sub,UNmin],[power_predicted_df['UN'][UNmin-sub],power_predicted_df['UN'][UNmin-sub]],color=colset1[3])
    lty = ['--' if all(power_predicted_df['BF']==power_predicted_df['RFT']) else '-']
    axs.plot(newsubs,power_predicted_df['BF'],color=colset1[0],lw=2,label="Bonferroni")
    axs.plot(newsubs,power_predicted_df['BH'],color=colset1[1],lw=2,label="Benjamini-Hochberg")
    axs.plot(newsubs,power_predicted_df['RFT'],color=colset1[2],lw=2,linestyle=str(lty[0]),label="Random Field Theory")
    axs.plot(newsubs,power_predicted_df['UN'],color=colset1[3],lw=2,label="Uncorrected")
    # axs.text(RFTmin+1,0.02,str(RFTmin),color=colset1[2])
    # axs.text(BFmin-2.5,0.02,str(BFmin),color=colset1[0])
    # axs.text(UNmin-2.5,0.02,str(UNmin),color=colset1[3])
    # axs.text(BHmin-2.5,0.02,str(BHmin),color=colset1[1])
    axs.set_ylim([0,1])
    axs.set_title("Power curves")
    axs.set_xlabel("Subjects")
    axs.set_ylabel("Average power")
    axs.legend(loc="center right",frameon=False)
    canvas = FigureCanvas(fig)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response
