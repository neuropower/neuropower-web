from . import views, plots
from django.conf.urls import url
from django.contrib import admin
import django.views.defaults

urlpatterns = [
    url(r'^neuropowerFAQ/$',views.npFAQ,name='npFAQ'),
    url(r'^tutorial/$',views.tutorial,name='npTutorial'),
    url(r'^methods/$',views.methods,name='npMethods'),
    url(r'^end/$',views.end_session,name='end_session'),
    #url(r'^neuropowerdata/$',views.neuropowerdata,name='neuropowerdata'),
    url(r'^neuropowerstart/$',views.neuropowerstart,name='neuropowerstart'),
    url(r'^neuropowerinput/$',views.neuropowerinput,name='neuropowerinput'),
    url(r'^neuropowerinput/(?P<neurovault>\w+)/$',views.neuropowerinput,name='neuropowerinput'),
    url(r'^neuropowerviewer/$',views.neuropowerviewer,name='neuropowerviewer'),
    url(r'^neuropowertable/$',views.neuropowertable,name='neuropowertable'),
    url(r'^neuropowermodel/$',views.neuropowermodel,name='neuropowermodel'),
    url(r'^neuropowermodel/result.png$', plots.plotModel,name='plotmodel'),
    url(r'^neuropowersamplesize/$',views.neuropowersamplesize,name='neuropowersamplesize'),
    url(r'^neuropowercrosstab/$',views.neuropowercrosstab,name='neuropowercrosstab'),
    url(r'^404/$', django.views.defaults.page_not_found, ),
    # with message
    url(r'^neuropowerinput/(?P<message>\w+)/$',views.neuropowerinput,name='neuropowerinput'),
    url(r'^neuropowertable/(?P<message>\w+)/$',views.neuropowertable,name='neuropowertable'),
    url(r'^neuropowermodel/(?P<message>\w+)/$',views.neuropowermodel,name='neuropowermodel'),
    url(r'^neuropowersamplesize/(?P<message>\w+)/$',views.neuropowersamplesize,name='neuropowersamplesize')
    ]
