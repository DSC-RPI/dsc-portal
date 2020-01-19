from django.contrib import admin
from django.conf import settings
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import SchoolYear, FAQ, Member, Event, EventAgendaItem, EventRSVP, EventAttendance, Project, Update, RoadmapMilestone, Tag

admin.site.register(SchoolYear)
admin.site.register(FAQ)
admin.site.register(EventRSVP)
admin.site.register(EventAttendance)
admin.site.register(Project)
admin.site.register(Update)
admin.site.register(RoadmapMilestone)
admin.site.register(Tag)

admin.site.site_title = f'DSC {settings.SCHOOL_NAME_SHORT} Management'
admin.site.site_header = 'Club Management'

class TagInline(admin.TabularInline):
    model = Tag

class MemberAdmin(admin.ModelAdmin):
    inlines = (TagInline),
# admin.site.register(Member, MemberAdmin)

# Define an inline admin descriptor for Employee model
# which acts a bit like a singleton
class MemberInline(admin.StackedInline):
    model = Member
    can_delete = False
    verbose_name_plural = 'member'

# Define a new User admin
class NewUserAdmin(BaseUserAdmin):
    list_filter = ['member__verified', 'is_staff']
    inlines = (MemberInline,)

class EventAgendaItemAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('event', 'title', 'description', ('estimated_start_time', 'estimated_duration'))
        }),
    )
admin.site.register(EventAgendaItem, EventAgendaItemAdmin)

# EVENT INLINES
class EventAgendaItemInline(admin.StackedInline):
    model = EventAgendaItem
    fieldsets = (
        (None, {
            'fields': ('title', 'description', ('estimated_start_time', 'estimated_duration'))
        }),
    )
class EventRSVPInline(admin.TabularInline):
    model = EventRSVP
class EventAttendanceInline(admin.TabularInline):
    model = EventAttendance

class EventAdmin(admin.ModelAdmin):
    date_hierarchy = 'start'
    search_fields = ['title', 'tagline', 'description']

    # https://docs.djangoproject.com/en/dev/ref/contrib/admin/#modeladmin-options
    fieldsets = (
        (None, {
            'fields': ('event_type', ('title', 'tagline'), ('start', 'end'), 'description', ('visibility', 'hidden'), ('location', 'what_to_bring'), 'review')
        }),
        ('Advanced options', {
            'classes': ('collapse',),
            'fields': ('attendance_code', 'slideshow_id', 'thumbnail_link', 'meeting_notes_id', 'calendar_event_id')
        })
    )

    inlines = [
        EventAgendaItemInline,
        EventRSVPInline,
        EventAttendanceInline
    ]
admin.site.register(Event, EventAdmin)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, NewUserAdmin)