from __future__ import unicode_literals
import sys
sys.path = sys.path[1:]
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.conf import settings
from scipy.stats import norm, t
import pandas as pd
import numpy as np
import tempfile
import uuid
import os

### MAIN TEMPLATE PAGES ################################################

def home(request):
    return render(request,"main/home.html",{})
