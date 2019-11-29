from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Member, Event, Project, Update

admin.site.register(Member)
admin.site.register(Event)
admin.site.register(Project)
admin.site.register(Update)