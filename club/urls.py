from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # path('about', views.about, name='about'),
    path('events/', views.event_index, name='events'),
    path('projects/', views.project_index, name='projects'),
    path('updates/', views.update_index, name='updates'),
    path('updates/<int:update_id>', views.update_detail, name='update_detail'),
    path('events/<int:event_id>', views.event_detail, name='event_detail'),
    path('members/', views.member_index, name='members'),
    path('members/<int:member_id>', views.member_detail, name='member_detail'),
    path('core-team/', views.core_team, name='core_team'),
    path('core-team/roadmap', views.roadmap_index, name='roadmap'),
    path('core-team/social-media', views.social_media, name='social_media'),
    path('account/', views.user_account, name='user_account')
]