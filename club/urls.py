from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about', views.about, name='about'),
    path('events/', views.event_index, name='events'),
    path('projects/', views.project_index, name='projects'),
    path('updates/', views.update_index, name='updates'),
    path('updates/<int:update_id>', views.update_detail, name='update_detail'),
    path('events/<int:event_id>', views.event_detail, name='event_detail')
]