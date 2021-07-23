from django.conf.urls import url, include
from django.urls import path
from .views import wire_down_events, gen_csv, tooltip, gen_pdf, events_modal, WireDownView


app_name = 'events'
urlpatterns = [
    url(r'^$', WireDownView.as_view(), name='events'),
    url(r'^gen_csv/$', gen_csv, name='gen_csv'),
    url(r'^gen_pdf/$', gen_pdf, name='gen_pdf'),
    url(r'^', tooltip, name='tooltip'),
    url(r'^', tooltip, name='events_modal'),
]