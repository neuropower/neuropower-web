from django.http import HttpResponse, HttpResponseRedirect
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from neuropower.utils import BUM, cluster, model, peakdistribution
from neuropower.utils import neuropowermodels as npm
from palettable.colorbrewer.qualitative import Paired_12,Set1_9
import scipy
import matplotlib as mpl
from .models import MixtureModel, ParameterModel, PeakTableModel, PowerTableModel
import jinja2
import mpld3
from mpld3 import plugins
import pandas as pd

def get_session_id(request):
    if not request.session.exists(request.session.session_key):
        request.session.create()
    sid = request.session.session_key
    return(sid)


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

def plotPower(sid):
    plt.switch_backend('agg')
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

    css = """
    table
    {
    border-collapse: collapse;
    }
    td
    {
      background-color: rgba(217, 222, 230,50);
    }
    table, th, td
    {
      border: 1px solid;
      border-color: rgba(217, 222, 230,50);
      text-align: right;
      font-size: 12px
    }
    """

    labels_BF = [pd.DataFrame(['Bonferroni','Sample Size: '+str(newsubs[i]),'Power: '+str(np.round(power_predicted_df['BF'][i],decimals=2))]).to_html(header=False,index_names=False,index=False) for i in range(len(power_predicted_df))]
    labels_BH = [pd.DataFrame(['Benjamini-Hochberg','Sample Size: '+str(newsubs[i]),'Power: '+str(np.round(power_predicted_df['BH'][i],decimals=2))]).to_html(header=False,index_names=False,index=False) for i in range(len(power_predicted_df))]
    labels_RFT = [pd.DataFrame(['Bonferroni','Sample Size: '+str(newsubs[i]),'Power: '+str(np.round(power_predicted_df['RFT'][i],decimals=2))]).to_html(header=False,index_names=False,index=False) for i in range(len(power_predicted_df))]
    labels_UN = [pd.DataFrame(['Bonferroni','Sample Size: '+str(newsubs[i]),'Power: '+str(np.round(power_predicted_df['UN'][i],decimals=2))]).to_html(header=False,index_names=False,index=False) for i in range(len(power_predicted_df))]

    fig,axs=plt.subplots(1,1,figsize=(8,5))
    fig.patch.set_facecolor('None')
    lty = ['--' if all(power_predicted_df['BF']==power_predicted_df['RFT']) else '-']
    BF=axs.plot(newsubs,power_predicted_df['BF'],'o',markersize=15,alpha=0,label="")
    BH=axs.plot(newsubs,power_predicted_df['BH'],'o',markersize=15,alpha=0,label="")
    RFT=axs.plot(newsubs,power_predicted_df['RFT'],'o',markersize=15,alpha=0,label="")
    UN=axs.plot(newsubs,power_predicted_df['UN'],'o',markersize=15,alpha=0,label="")
    plugins.clear(fig)
    plugins.connect(fig, plugins.PointHTMLTooltip(BF[0], labels_BF,hoffset=0,voffset=10,css=css))
    plugins.connect(fig, plugins.PointHTMLTooltip(BH[0], labels_BH,hoffset=0,voffset=10,css=css))
    plugins.connect(fig, plugins.PointHTMLTooltip(RFT[0], labels_RFT,hoffset=0,voffset=10,css=css))
    plugins.connect(fig, plugins.PointHTMLTooltip(UN[0], labels_UN,hoffset=0,voffset=10,css=css))
    axs.plot(newsubs,power_predicted_df['BF'],color=colset1[0],lw=2,label="Bonferroni")
    axs.plot(newsubs,power_predicted_df['BH'],color=colset1[1],lw=2,label="Benjamini-Hochberg")
    axs.plot(newsubs,power_predicted_df['RFT'],color=colset1[2],lw=2,linestyle=str(lty[0]),label="Random Field Theory")
    axs.plot(newsubs,power_predicted_df['UN'],color=colset1[3],lw=2,label="Uncorrected")
    axs.set_ylim([0,1])
    axs.set_title("Power curves")
    axs.set_xlabel("Subjects")
    axs.set_ylabel("Average power")
    axs.legend(loc="bottom right",frameon=False,title="")
    code = mpld3.fig_to_html(fig)
    return code
