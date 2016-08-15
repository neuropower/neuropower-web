import requests
import os
os.environ['http_proxy']=''
import urllib
from django.conf import settings
from django.http import HttpResponseRedirect
import numpy as np
from models import DesignModel

def get_session_id(request):
    '''get_session_id gets the user session id, and creates one if it doesn't exist'''
    if not request.session.exists(request.session.session_key):
        request.session.create()
    sid = request.session.session_key
    return(sid)

def probs_and_cons(sid):
    desdata = DesignModel.objects.get(SID=sid)

    # contrasts

    C = np.array(
        [
        [desdata.C00,desdata.C01,desdata.C02,desdata.C03,desdata.C04,desdata.C05,desdata.C06,desdata.C07,desdata.C08,desdata.C09],
        [desdata.C10,desdata.C11,desdata.C12,desdata.C13,desdata.C14,desdata.C15,desdata.C16,desdata.C17,desdata.C18,desdata.C19],
        [desdata.C20,desdata.C21,desdata.C22,desdata.C23,desdata.C24,desdata.C25,desdata.C26,desdata.C27,desdata.C28,desdata.C29],
        [desdata.C30,desdata.C31,desdata.C32,desdata.C33,desdata.C34,desdata.C35,desdata.C36,desdata.C37,desdata.C38,desdata.C39],
        [desdata.C40,desdata.C41,desdata.C42,desdata.C43,desdata.C44,desdata.C45,desdata.C46,desdata.C47,desdata.C48,desdata.C49]
        ]
    )
    C = C[:desdata.Clen,:desdata.S]
    for line in range(C.shape[0]):
        if not np.sum(C[line,:])==0:
            cor = np.sum(C[line,:])
        else:
            cor = np.max(C[line,:])-np.min(C[line,:])
        C[line,:] = C[line,:]/cor
    C = np.around(C.astype(np.double),2)

    # probabilities

    P = np.array(
    [desdata.P0,desdata.P1,desdata.P2,desdata.P3,desdata.P4,desdata.P5,desdata.P6,desdata.P7,desdata.P8,desdata.P9]
    )
    P = P[:desdata.S]
    P = P/np.sum(P)
    P = np.around(P.astype(np.double),2)

    ## to html

    Phtml = "".join(["<tr><td>Stimulus "+str(d+1)+":&emsp;</td><td>"+str(P[d])+"</td></tr>" for d in range(len(P))])
    Chtml = "".join(["<tr><td>Contrast "+str(c)+":&emsp;</td>"+"".join(["<td>"+str(C[c][d])+"&emsp;</td>" for d in range(len(C[c]))])+"</tr>" for c in range(C.shape[0])])

    return {"C":C,"P":P,"Phtml":Phtml,"Chtml":Chtml}

def weights_html(weights):
    html = [
        "<tr><td>Estimation efficiency:&emsp;</td><td>"+str(weights[0])+"</td></tr>",
        "<tr><td>Detection power:&emsp;</td><td>"+str(weights[1])+"</td></tr>",
        "<tr><td>Confounds efficiency:&emsp;</td><td>"+str(weights[2])+"</td></tr>",
        "<tr><td>Probabilities efficiency:&emsp;</td><td>"+str(weights[3])+"</td></tr>"]
    html_join = "".join(html)
    return html_join

def get_design_steps(template_page,sid):
    # template name, step class, and color
    pages = {"design/start.html": {"class":"overview","color":"#c9c4c5","enabled":"yes"},
             "design/input.html": {"class":"maininput","color":"#c9c4c5","enabled":"yes"},
             "design/cons.html": {"class":"consandprobs","color":"#c9c4c5","enabled":"yes"},
             "design/review.html": {"class":"review","color":"#c9c4c5","enabled":"yes"},
             "design/options.html": {"class":"options","color":"#c9c4c5","enabled":"yes"},
             "design/runGA.html": {"class":"run","color":"#c9c4c5","enabled":"yes"}
             }


    # Set the active page
    pages["active"] = pages[template_page]
    return pages
