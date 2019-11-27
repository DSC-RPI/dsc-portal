from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('splash', views.splash, name='splash'),
    path('events/', views.event_index),
    path('events/<int:event_id>', views.event_detail)
]