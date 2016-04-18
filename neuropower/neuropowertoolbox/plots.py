from neuropowertoolbox.models import MixtureModel, ParameterModel, PeakTableModel, PowerTableModel
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from palettable.colorbrewer.qualitative import Paired_12,Set1_9
from neuropower.utils import BUM, cluster, peakdistribution
from django.http import HttpResponse, HttpResponseRedirect
from neuropower.utils import neuropowermodels as npm
from neuropowertoolbox.utils import get_session_id
import matplotlib.pyplot as plt
from mpld3 import plugins
import matplotlib as mpl
import pandas as pd
import numpy as np
mpl.use('Agg')
import jinja2
import scipy
import mpld3


def plotModel(request):
    plt.switch_backend('agg')
    sid = get_session_id(request)
    mixdata = MixtureModel.objects.filter(SID=sid)[::-1][0]
    parsdata = ParameterModel.objects.filter(SID=sid)[::-1][0]
    peakdata = PeakTableModel.objects.filter(SID=sid)[::-1][0]
    peaks = peakdata.data
    twocol = Paired_12.mpl_colors
    xn = np.arange(-10,30,0.01)
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
    axs[1].hist(peaks.peak,lw=0,facecolor=twocol[0],normed=True,bins=np.arange(min(peaks.peak),30,0.3),label="observed distribution")
    axs[1].set_xlim([float(parsdata.ExcZ),np.max(peaks.peak)])
    axs[1].set_ylim([0,1])
    axs[1].plot(xn,nul,color=twocol[3],lw=2,label="null distribution")
    axs[1].plot(xn,alt,color=twocol[5],lw=2, label="alternative distribution")
    axs[1].plot(xn,mix,color=twocol[1],lw=2,label="total distribution")

    peak_heights_string = str(round(float(mixdata.mu)/np.sqrt(parsdata.Subj),2))
    axs[1].set_title("Distribution of peak heights \n $\delta_1$ = %s" %(peak_heights_string))
    axs[1].set_xlabel("Peak heights (z-values)")
    axs[1].set_ylabel("Density")
    axs[1].legend(loc="upper right",frameon=False)
    canvas = FigureCanvas(fig)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response

def plotPower(sid,MCP='',pow=0,ss=0):
    powerdata = PowerTableModel.objects.filter(SID=sid)[::-1][0]
    parsdata = ParameterModel.objects.filter(SID=sid)[::-1][0]
    powtab = powerdata.data
    powtxt = powtab.round(2)
    cols = dict(zip(['BF','BH','RFT','UN'],Set1_9.mpl_colors))
    sub = int(parsdata.Subj)
    newsubs = powtab.newsamplesize
    amax = int(50)

    css = """
    table{border-collapse: collapse}
    td{background-color: rgba(217, 222, 230,50)}
    table, th, td{border: 1px solid;border-color: rgba(217, 222, 230,50);text-align: right;font-size: 12px}
    """

    hover_BF = [pd.DataFrame(['Bonferroni','Sample Size: '+str(newsubs[i]),'Power: '+str(powtxt['BF'][i])]).to_html(header=False,index_names=False,index=False) for i in range(len(powtab))]
    hover_BH = [pd.DataFrame(['Benjamini-Hochberg','Sample Size: '+str(newsubs[i]),'Power: '+str(powtxt['BH'][i])]).to_html(header=False,index_names=False,index=False) for i in range(len(powtab))]
    hover_RFT = [pd.DataFrame(['Random Field Theory','Sample Size: '+str(newsubs[i]),'Power: '+str(powtxt['RFT'][i])]).to_html(header=False,index_names=False,index=False) for i in range(len(powtab))]
    hover_UN = [pd.DataFrame(['Uncorrected','Sample Size: '+str(newsubs[i]),'Power: '+str(powtxt['UN'][i])]).to_html(header=False,index_names=False,index=False) for i in range(len(powtab))]

    fig,axs=plt.subplots(1,1,figsize=(8,5))
    fig.patch.set_facecolor('None')
    lty = ['--' if all(powtab.BF==powtab.RFT) else '-']
    BF=axs.plot(newsubs,powtab.BF,'o',markersize=15,alpha=0,label="")
    BH=axs.plot(newsubs,powtab.BH,'o',markersize=15,alpha=0,label="")
    RFT=axs.plot(newsubs,powtab.RFT,'o',markersize=15,alpha=0,label="")
    UN=axs.plot(newsubs,powtab.UN,'o',markersize=15,alpha=0,label="")
    plugins.clear(fig)
    plugins.connect(fig, plugins.PointHTMLTooltip(BF[0], hover_BF,hoffset=0,voffset=10,css=css))
    plugins.connect(fig, plugins.PointHTMLTooltip(BH[0], hover_BH,hoffset=0,voffset=10,css=css))
    plugins.connect(fig, plugins.PointHTMLTooltip(RFT[0], hover_RFT,hoffset=0,voffset=10,css=css))
    plugins.connect(fig, plugins.PointHTMLTooltip(UN[0], hover_UN,hoffset=0,voffset=10,css=css))
    axs.plot(newsubs,powtab.BF,color=cols['BF'],lw=2,label="Bonferroni")
    axs.plot(newsubs,powtab.BH,color=cols['BH'],lw=2,label="Benjamini-Hochberg")
    axs.plot(newsubs,powtab.RFT,color=cols['RFT'],lw=2,linestyle=str(lty[0]),label="Random Field Theory")
    axs.plot(newsubs,powtab.UN,color=cols['UN'],lw=2,label="Uncorrected")
    text = "None"
    if pow != 0:
        if all(powtab[MCP]<pow):
            text = "To obtain a statistical power of "+str(pow)+" this study would require a sample size larger than 300 subjects."
        else:
            min = int(np.min([i for i,elem in enumerate(powtab[MCP]>pow,1) if elem])+sub-1)
            axs.plot([min,min],[0,powtab[MCP][min-sub]],color=cols[MCP])
            axs.plot([sub,min],[powtab[MCP][min-sub],powtab[MCP][min-sub]],color=cols[MCP])
            text = "To obtain a statistical power of %s this study would require a sample size of %s subjects." %(pow,min)
            amax = max(min,amax)
    if ss != 0:
        ss_pow = powtab[MCP][ss]
        axs.plot([ss,ss],[0,ss_pow],color=cols[MCP],linestyle="--")
        axs.plot([sub,ss],[ss_pow,ss_pow],color=cols[MCP],linestyle="--")
        xticks = [x for x in list(np.arange((np.ceil(sub/10.))*10,100,10)) if not x == np.round(ss/10.)*10]
        axs.set_xticks(xticks+[ss])
        axs.set_yticks(list(np.arange(0,1.1,0.1)))
        text = "A sample size of %s subjects with %s control comes with a power of %s." %(ss,MCP,str(np.round(ss_pow,decimals=2)))
        amax = max(ss,amax)
    axs.set_ylim([0,1])
    axs.set_xlim([sub,amax])
    axs.set_title("Power curves")
    axs.set_xlabel("Subjects")
    axs.set_ylabel("Average power")
    axs.legend(loc="lower right",frameon=False,title="")
    code = mpld3.fig_to_html(fig)
    out = {
        "code":code,
        "text":text
    }
    return out
