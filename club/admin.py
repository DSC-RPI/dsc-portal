from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Member, Event, EventAttendance, Project, Update

admin.site.register(Member)
admin.site.register(Event)
admin.site.register(EventAttendance)
admin.site.register(Project)
admin.site.register(Update)

# Define an inline admin descriptor for Employee model
# which acts a bit like a singleton
class MemberInline(admin.StackedInline):
    model = Member
    can_delete = False
    verbose_name_plural = 'member'

# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (MemberInline,)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)