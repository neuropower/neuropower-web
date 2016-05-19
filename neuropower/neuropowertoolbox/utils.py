from neuropowertoolbox.models import ParameterModel, MixtureModel, PeakTableModel
import requests
import os
os.environ['http_proxy']=''
import urllib
from django.conf import settings

def get_neuropower_steps(template_page,session_id=None):
    '''get_neuropower_steps returns a complete dictionary object with button colors, active status, and  currently active based on a template page and session data object.
    '''
    # template name, step class, and color
    pages = {"neuropower/neuropowerstart.html": {"class":"overview","color":"#F7F7F7","enabled":"yes"},
             "neuropower/neuropowerinput.html": {"class":"start","color":"#F7941E","enabled":"yes"},
             "neuropower/neuropowerviewer.html": {"class":"viewer","color":"#FFDE16","enabled":"yes"},
             "neuropower/neuropowertable.html": {"class":"peak-table","color":"#D7DF21","enabled":"yes"},
             "neuropower/neuropowermodel.html": {"class":"fit","color":"#0BA14B","enabled":"yes"},
             "neuropower/neuropowersamplesize.html": {"class":"power-calculation","color":"#25AAE1","enabled":"yes"},
             "neuropower/neuropowercrosstab.html": {"class":"power-table","color":"#25AAE1","enabled":"yes"}}

    # Set enabled or disabled page status depending on session data
    if not ParameterModel.objects.filter(SID=session_id):
        pages["neuropower/neuropowerviewer.html"]["enabled"] = "no"
        pages["neuropower/neuropowertable.html"]["enabled"] = "no"
        pages["neuropower/neuropowermodel.html"]["enabled"] = "no"
        pages["neuropower/neuropowersamplesize.html"]["enabled"] = "no"
        pages["neuropower/neuropowercrosstab.html"]["enabled"] = "no"

    if not PeakTableModel.objects.filter(SID=session_id):
        pages["neuropower/neuropowermodel.html"]["enabled"] = "no"
        pages["neuropower/neuropowersamplesize.html"]["enabled"] = "no"
        pages["neuropower/neuropowercrosstab.html"]["enabled"] = "no"

    if not MixtureModel.objects.filter(SID=session_id):
        pages["neuropower/neuropowersamplesize.html"]["enabled"] = "no"
        pages["neuropower/neuropowercrosstab.html"]["enabled"] = "no"

    # Set the active page
    pages["active"] = pages[template_page]
    return pages



def get_url(url,return_json=True):
    '''get_url uses requests to return a url. Default return format is json. If return_json is set to false, will return raw data
    :param url: the url to retrieve
    :param return_json: boolean, default True, to return json
    '''
    response = requests.get(url)
    if return_json == True:
        return response.json()
    else:
        return response.text


def get_session_id(request):
    '''get_session_id gets the user session id, and creates one if it doesn't exist'''
    if not request.session.exists(request.session.session_key):
        request.session.create()
    sid = request.session.session_key
    return(sid)


def create_temporary_copy(file,mapID,mask=False,url=False):
    temp_dir = os.path.join(settings.MEDIA_ROOT,"maps")
    end = file[-3:]
    newext = ".nii.gz" if end == ".gz" else ".nii"
    if not mask:
        newfilename = os.path.join(temp_dir,'SPM_'+mapID+newext)
    else:
        newfilename = os.path.join(temp_dir,"mask_"+mapID+newext)

    if url:
        newfilename = os.path.join(temp_dir,'SPM_'+mapID+newext)
        urllib.urlretrieve(file, newfilename)
    else:
        os.rename(file,newfilename)
    return newfilename
