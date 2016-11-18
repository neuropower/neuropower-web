from . import views
from django.conf.urls import url
from django.contrib import admin
import django.views.defaults

urlpatterns = [
    url(r'^start/$',views.start,name='DStart'),
    url(r'^maininput/$',views.maininput,name='DMainInput'),
    url(r'^consinput/$',views.consinput,name='DConsInput'),
    url(r'^nested/$',views.nested,name='DNested'),
    url(r'^review/$',views.review,name='DReview'),
    url(r'^runGA/(?P<retrieve>\w+)/$',views.review,name='DReview'),
    url(r'^runGA/$',views.runGA,name='DRunGA'),
    url(r'^settings/$',views.options,name='DSettings'),
    url(r'^DFAQ/$',views.DFAQ,name='DFAQ'),
    url(r'^tutorial/$',views.tutorial,name='DTutorial'),
    url(r'^methods/$',views.methods,name='DMethods'),
    url(r'^end/$',views.end_session,name='DReset'),
    url(r'^updatepage/$',views.updatepage,name='DUpdate'),
        ]
