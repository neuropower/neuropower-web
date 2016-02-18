from __future__ import unicode_literals
from django.db import models
from picklefield.fields import PickledObjectField
import numpy as np
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session

class NiftiModel(models.Model):
    SID = models.CharField(max_length=300,default="")
    url = models.URLField()
    location = models.CharField(max_length=300,default="/Users/Joke/Documents/Onderzoek/neuropower/neuropower-dev/neuropower/static_in_pro/our_static/img/zstat1.nii.gz")
    def __unicode__(self): # Python 3: __str__
        self

class ParameterModel(models.Model):
    SID = models.CharField(max_length=300,default="")
    ZorT_c = (("Z","Z"),("T","T"))
    ExcUnits_c = (("p","units = p-values (SPM default)"),("t","units = t-values (FSL default)"))
    Samples_c = ((1, ("One-sample")),(2, ("Two-sample")))
    ZorT = models.CharField(max_length=10,choices=ZorT_c)
    ExcUnits = models.CharField(max_length=10,choices=ExcUnits_c)
    Exc = models.DecimalField(max_digits=5,decimal_places=2)
    ExcZ = models.DecimalField(max_digits=5,decimal_places=2,default='NaN')
    DoF = models.DecimalField(max_digits=5,decimal_places=2,default='NaN')
    Subj = models.IntegerField()
    Samples = models.IntegerField(choices=Samples_c)
    Smoothx = models.DecimalField(max_digits=5,decimal_places=2)
    Smoothy = models.DecimalField(max_digits=5,decimal_places=2)
    Smoothz = models.DecimalField(max_digits=5,decimal_places=2)
    Voxx = models.DecimalField(max_digits=5,decimal_places=2)
    Voxy = models.DecimalField(max_digits=5,decimal_places=2)
    Voxz = models.DecimalField(max_digits=5,decimal_places=2)
    def __unicode__(self): # Python 3: __str__
        return self

class PeakTableModel(models.Model):
    SID = models.CharField(max_length=300,default="")
    data = PickledObjectField()
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
