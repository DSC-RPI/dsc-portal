from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # path('about', views.about, name='about'),
    path('faq', views.faq, name='faq'),
    path('conduct', views.conduct, name='conduct'),
    path('events/', views.event_index, name='events'),
    path('projects/', views.project_index, name='projects'),
    path('updates/', views.update_index, name='updates'),
    path('updates/<int:update_id>', views.update_detail, name='update_detail'),
    path('events/<int:event_id>', views.event_detail, name='event_detail'),
    path('events/<int:event_id>/rsvp', views.event_rsvp, name='event_rsvp'),
    path('events/<int:event_id>/attendance', views.event_attendance, name='event_attendance'),
    path('events/<int:event_id>/feedback', views.event_feedback, name='event_feedback'),
    path('members/', views.member_index, name='members'),
    path('members/<int:member_id>', views.member_detail, name='member_detail'),
    path('core-team/', views.core_team, name='core_team'),
    path('core-team/email', views.core_team_email, name='core_team_email'),
    path('core-team/roadmap', views.roadmap_index, name='roadmap'),
    path('core-team/social-media', views.social_media, name='social_media'),
    path('core-team/member-management', views.member_management, name='member_management'),
    path('core-team/<str:role_name>', views.core_team_role, name='core_team_role'),
    path('account/', views.user_account, name='user_account'),
    path('account/verify', views.verify_account, name='verify_account')
]