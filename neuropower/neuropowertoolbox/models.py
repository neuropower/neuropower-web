from __future__ import unicode_literals
from django.db import models
from picklefield.fields import PickledObjectField
import numpy as np
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session
import nibabel
import os
#import tempfile

#temp_dir = tempfile.gettempdir()

class ParameterModel(models.Model):
    SID = models.CharField(max_length=300,default="")
    mapID = models.CharField(max_length=300,default="")
    peaktable = models.CharField(max_length=300,default="")
    url = models.URLField(default="")
    location = models.CharField(max_length=300,default="")
    spmfile = models.FileField(upload_to=os.path.join(settings.MEDIA_ROOT,"maps"),default="")
    masklocation = models.CharField(max_length=300,default="")
    maskfile = models.FileField(upload_to=os.path.join(settings.MEDIA_ROOT,"maps"),default="")
    nvox = models.CharField(max_length=300,default="")
    ZorT_c = (("Z","Z"),("T","T"))
    Samples_c = ((1, ("One-sample")),(2, ("Two-sample")))
    ZorT = models.CharField(max_length=10,choices=ZorT_c)
    Exc = models.DecimalField(max_digits=5,decimal_places=4)
    ExcZ = models.DecimalField(max_digits=5,decimal_places=2,default='NaN')
    DoF = models.DecimalField(max_digits=5,decimal_places=2,default='NaN')
    Subj = models.IntegerField()
    alpha = models.DecimalField(max_digits=5,decimal_places=4,default=0.05)
    Samples = models.IntegerField(choices=Samples_c)
    SmoothEst_c = ((1,"Manual"),(2,"Estimate"))
    SmoothEst = models.IntegerField(choices=SmoothEst_c,default=1)
    Smoothx = models.DecimalField(max_digits=5,decimal_places=2,null=True)
    Smoothy = models.DecimalField(max_digits=5,decimal_places=2,null=True)
    Smoothz = models.DecimalField(max_digits=5,decimal_places=2,null=True)
    Voxx = models.DecimalField(max_digits=5,decimal_places=2,null=True)
    Voxy = models.DecimalField(max_digits=5,decimal_places=2,null=True)
    Voxz = models.DecimalField(max_digits=5,decimal_places=2,null=True)
    def __unicode__(self): # Python 3: __str__
        return self

class PeakTableModel(models.Model):
    SID = models.CharField(max_length=300,default="")
    data = PickledObjectField(default="")
    def __unicode__(self): # Python 3: __str__
        return self

class MixtureModel(models.Model):
    SID = models.CharField(max_length=300,default="")
    pi1 = models.DecimalField(max_digits=10,decimal_places=4)
    a = models.DecimalField(max_digits=10,decimal_places=4,default="NaN")
    mu = models.DecimalField(max_digits=10,decimal_places=4)
    sigma = models.DecimalField(max_digits=10,decimal_places=4)
    def __unicode__(self): # Python 3: __str__
        return self

class PowerTableModel(models.Model):
    SID = models.CharField(max_length=300,default="")
    data = PickledObjectField(default="")
    def __unicode__(self): # Python 3: __str__
        return self

class PowerModel(models.Model):
    SID = models.CharField(max_length=300,default="")
    reqPow = models.DecimalField(max_digits=10,decimal_places=4,null=True, blank=True)
    reqSS = models.IntegerField(default=0,null=True, blank=True)
    MCP_c = (("RFT", "Random Field Theory"),("BH", "Benjamini-Hochberg"),("BF","Bonferroni"),("UN","Uncorrected"))
    MCP = models.CharField(max_length=10,choices=MCP_c)
    def __unicode__(self):
        return self
