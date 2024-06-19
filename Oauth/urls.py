from django.contrib import admin
from django.urls import path, include, re_path
from . import views

urlpatterns = [
    path('', views.login),
    path('strava_redirect/', views.strava_redirect, name='strava_redirect'),
    path('strava_signon/', views.strava_signon, name='strava_signon'),

    re_path(r'^.*exchange_token.*$', views.strava_callback, name='strava_callback'),
    path('crafter/', views.to_homepage, name='crafter'),
    path('craft_runs/', include('runcrafter.urls'))
]
