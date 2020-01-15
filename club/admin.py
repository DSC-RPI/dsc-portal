from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import SchoolYear, FAQ, Member, Event, EventAgendaItem, EventRSVP, EventAttendance, Project, Update, RoadmapMilestone

admin.site.register(SchoolYear)
admin.site.register(Member)
admin.site.register(FAQ)
admin.site.register(EventRSVP)
admin.site.register(EventAttendance)
admin.site.register(Project)
admin.site.register(Update)
admin.site.register(RoadmapMilestone)

# Define an inline admin descriptor for Employee model
# which acts a bit like a singleton
class MemberInline(admin.StackedInline):
    model = Member
    can_delete = False
    verbose_name_plural = 'member'

# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (MemberInline,)

# EVENT INLINES
class EventAgendaItemInline(admin.StackedInline):
    model = EventAgendaItem
class EventRSVPInline(admin.StackedInline):
    model = EventRSVP
class EventAttendanceInline(admin.StackedInline):
    model = EventAttendance

class EventAdmin(admin.ModelAdmin):
    inlines = [
        EventAgendaItemInline,
        EventRSVPInline,
        EventAttendanceInline
    ]
admin.site.register(Event, EventAdmin)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)