from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about', views.about, name='about'),
    path('events/', views.event_index, name='events'),
    path('events/<int:event_id>', views.event_detail)
]