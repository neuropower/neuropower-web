from __future__ import unicode_literals
from django.db import models
from picklefield.fields import PickledObjectField
import os
from django.conf import settings

#import tempfile

#temp_dir = tempfile.gettempdir()

class NeuropowerModel(models.Model):
    SID = models.CharField(max_length=300,default="")
    step = models.IntegerField(default=0) #0 = nothing, 1 = parameters, 2 = peaktable done, 3 = model fit, 4 = powertable done
    map_url = models.URLField(default="")
    mask_url = models.URLField(default="")
    map_local = models.CharField(max_length=300,default="")
    mask_local = models.CharField(max_length=300,default="")
    peaktable = PickledObjectField(default="")
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
    data = PickledObjectField(default="")
    err = models.CharField(max_length=1000,default="")
    pi1 = models.DecimalField(max_digits=10,decimal_places=4,null=True)
    a = models.DecimalField(max_digits=10,decimal_places=4,default="NaN")
    mu = models.DecimalField(max_digits=10,decimal_places=4,null=True)
    sigma = models.DecimalField(max_digits=10,decimal_places=4,null=True)
    data = PickledObjectField(default="")
    reqPow = models.DecimalField(max_digits=10,decimal_places=4,null=True, blank=True)
    reqSS = models.IntegerField(default=0,null=True, blank=True)
    MCP_c = (("RFT", "Random Field Theory"),("BH", "Benjamini-Hochberg"),("BF","Bonferroni"),("UN","Uncorrected"))
    MCP = models.CharField(max_length=10,choices=MCP_c)
    def __unicode__(self):
        return "<PowerModel:%s>" %self.SID
