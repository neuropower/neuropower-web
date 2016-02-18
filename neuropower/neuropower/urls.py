"""neuropower URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url,include
from django.contrib import admin
from neuropowertoolbox import views, plots
#from django.contrib.staticfiles.urls import staticfiles.urlpatterns
#urlpatterns += staticfile_urlpatterns()

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$',views.home,name='home'),
    url(r'^neuropower/$',views.neuropower,name='neuropower'),
    url(r'^neuropowerviewer/$',views.neuropowerviewer,name='neuropowerviewer'),
    url(r'^neuropowertable/$',views.neuropowertable,name='neuropowertable'),
    url(r'^neuropowermodelplot/$',views.neuropowermodelplot,name='neuropowermodelplot'),
    url(r'^plotpage/$',views.plotpage,name='plotpage'),
    url(r'^plotpage/result.png$', plots.plotResults,name='plot'),
    ]
