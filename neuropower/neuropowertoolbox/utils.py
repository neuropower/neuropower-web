from neuropowertoolbox.models import ParameterModel, MixtureModel
import requests

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

    # Need to ask @jokedurnez about this flow
    #if not not MixtureModel.objects.filter(SID=session_id):
    #    pages["neuropower/neuropowersamplesize.html"]["enabled"] = "no"
    #    pages["neuropower/neuropowercrosstab.html"]["enabled"] = "no"


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

