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
import django.views.defaults

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$',views.home,name='home'),
    url(r'^FAQ/$',views.FAQ,name='FAQ'),
    url(r'^tutorial/$',views.tutorial,name='tutorial'),
    url(r'^methods/$',views.methods,name='methods'),
    url(r'^end/$',views.end_session,name='end_session'),
    url(r'^neuropowerstart/$',views.neuropowerstart,name='neuropowerstart'),
    url(r'^neuropowerinput/$',views.neuropowerinput,name='neuropowerinput'),
    url(r'^neuropowerinput/(?P<neurovault_id>\w+)/$',views.neuropowerinput,name='neuropowerinput'),
    url(r'^neuropowerviewer/$',views.neuropowerviewer,name='neuropowerviewer'),
    url(r'^neuropowertable/$',views.neuropowertable,name='neuropowertable'),
    url(r'^neuropowermodel/$',views.neuropowermodel,name='neuropowermodel'),
    url(r'^neuropowermodel/result.png$', plots.plotModel,name='plotmodel'),
    url(r'^neuropowersamplesize/$',views.neuropowersamplesize,name='neuropowersamplesize'),
    url(r'^neuropowercrosstab/$',views.neuropowercrosstab,name='neuropowercrosstab'),
    url(r'^404/$', django.views.defaults.page_not_found, )
    ]
