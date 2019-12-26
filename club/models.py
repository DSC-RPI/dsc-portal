from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save

from random import choice
from string import ascii_uppercase

from .google import docs_service, drive_service, slides_service, calendar_service
from django.utils import timezone

class SchoolYear(models.Model):
    '''A SchoolYear represents a full year of school...'''
    start_date = models.DateField(help_text='The first day of the school year.')
    end_date = models.DateField(help_text='The last day of the school year.')

    def is_ongoing(self):
        return self.start_date <= timezone.now().date() <= self.end_date
    
    @property
    def title(self):
        return f'{self.start_date.month}/{str(self.start_date.year)[2:]}-{self.end_date.month}/{str(self.end_date.year)[2:]}'

    @classmethod
    def get_current_school_year(cls):
        now = timezone.now().date()
        return SchoolYear.objects.get(start_date__gte=now, end_date__gte=now)

    def __str__(self):
        return f'School Year {self.title}'

class Member(models.Model):
    '''
    Member represents a club member, an extension of the base user model.
    This holds club member info such as school grade and dietary restrictions.
    '''
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=False)
    GRADE_TYPES = [
        ('Fr', 'Freshman'),
        ('So', 'Sophomore'),
        ('Ju', 'Junior'),
        ('Se', 'Senior'),
        ('G', 'Graduate'),
        ('F', 'Faculty')
    ]
    grade = models.CharField(max_length=2, blank=True, null=True, choices=GRADE_TYPES, help_text='The grade of the student (or faculty status)')
    # dietary_restrictions = ???
    # TODO: make an tag system for dietary restrictions to easily query

    @classmethod
    def post_user_save(cls, sender, instance, created, *args, **kwargs):
        try:
            has_member = instance.member is not None
        except:
            instance.member = Member()
            instance.member.save()
post_save.connect(Member.post_user_save, sender=settings.AUTH_USER_MODEL)

class Event(models.Model):
    '''Events represent one-time club meetings.'''

    # Recognized types of events
    # Taken from https://sites.google.com/google.com/developerstudentclubleads/dsc-activities-reporting
    EVENT_TYPES = [
        ('IS', 'Info Session'),
        ('WS', 'Workshop'),
        ('SJ', 'Study Jam Workshop'),
        ('HO', 'Hands-on Workshop'),
        ('HA', 'Hackathon'),
        ('SS', 'Speaker Session'),
        ('SC', 'Showcase'),
        ('CT', 'Core Team Meeting')
    ]

    event_type = models.CharField(max_length=2, choices=EVENT_TYPES, help_text='Whether the event is a Workshop, Info session, etc.')
    
    # Who can see the event
    VISIBILITY_TYPES = [
        ('P', 'Public'),
        ('M', 'Members'),
        ('C', 'Core Team')
    ]
    visibility = models.CharField(max_length=1, choices=VISIBILITY_TYPES, help_text='Determines who can see/register for the event.')
    
    hidden = models.BooleanField(default=False, help_text='If true then the event will not be shown anywhere. Use this to create event drafts.')

    # Title of Event limited to 100 characters
    title = models.CharField(max_length=100, help_text='The headline title of the event. Should be very concise.')
    
    # (Optional) Event tagline
    tagline = models.CharField(max_length=200, blank=True, null=True, help_text='An optional tagline that will be displayed with the event title if it exists.')
    
    # Required event description
    description = models.CharField(max_length=5000, help_text='Long descriptionf of the event. Supports Markdown.')

    # Date and time range of event
    start = models.DateTimeField(help_text='The exact start date and time of the event.')
    end = models.DateTimeField(help_text='The exact end date and time of the event.')

    location = models.CharField(max_length=100, help_text='Where the event is being held.')

    attendance_code = models.CharField(max_length=6, blank=True, null=True, help_text='Random attendance code for members to submit to verify their attendance.')

    slideshow_id = models.CharField(max_length=300, blank=True, null=True, help_text='(optional) The ID of the Google Slides slideshow.')

    thumbnail_link = models.URLField(max_length=500, blank=True, null=True, help_text='An optional link to an image to show for the event. If a slideshow is associated with the event, it will automatically use the slide thumbnail.')

    meeting_notes_id = models.CharField(max_length=300, blank=True, null=True, help_text='The ID of the Google Docs meeting notes. This is most likely to an auto-generated Google Docs.')
    
    @property
    def meeting_notes_link(self):
        '''A direct link to the Google Doc meeting notes generated for the event.'''
        return 'https://docs.google.com/document/d/' + self.meeting_notes_id

    @property
    def slideshow_link(self):
        '''A direct link to the Google Slides slideshow generated or chosen for the event.'''
        return 'https://docs.google.com/presentation/d/' + self.slideshow_id

    calendar_event_id = models.CharField(max_length=300, blank=True, null=True, help_text='The Google Calendar event ID')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def create_google_calendar_event(self):
        '''
        Creates a Google Calendar event for the club event with the right title, location, time, etc.
        and adds it to the official club Google Calendar.
        '''
        event = {
            'summary': f'{self.title}: {self.get_event_type_display()}',
            'location': self.location,
            'description': self.description,
            'start': {
                'dateTime': self.start.isoformat(),
                'timeZone': settings.TIME_ZONE
            },
            'end': {
                'dateTime': self.end.isoformat(),
                'timeZone': settings.TIME_ZONE
            },
            'source': {
                'title': self.title,
                'url': settings.DOMAIN + '/events/' + str(self.id)
            }
        }

        calendar_event = calendar_service.events().insert(calendarId=settings.GOOGLE_CALENDAR_ID, body=event).execute()

        self.calendar_event_id = calendar_event.get('id')

        self.save()
    
    def update_google_calendar_event(self):
        '''
        Updates the Google Calendar event associated with the club event with the proper title, location, time, etc.
        '''
        calendar_service.events().patch(calendarId=settings.GOOGLE_CALENDAR_ID, eventId=self.calendar_event_id, body={
            'summary': f'{self.title}: {self.get_event_type_display()}',
            'location': self.location,
            'description': self.description,
            'start': {
                'dateTime': self.start.isoformat(),
                'timeZone': settings.TIME_ZONE
            },
            'end': {
                'dateTime': self.end.isoformat(),
                'timeZone': settings.TIME_ZONE
            },
        }).execute()

    def delete_google_calendar_event(self):
        '''
        Deletes the Google Calendar event associated with the club event.
        '''
        calendar_service.events().delete(calendarId=settings.GOOGLE_CALENDAR_ID, eventId=self.calendar_event_id).execute()

    def create_meeting_notes(self):
        '''
        Creates a Google Doc from the Meeting Notes template in the club's Google Drive,
        fills in the template with the specified values, and moves it to the meeting notes folder.
        '''
        if self.meeting_notes_id:
            return

        # This will be the document name
        name = self.start.strftime("[%y/%m/%d] DSC " + settings.SCHOOL_NAME_SHORT + " Meeting Notes")

        document = drive_service.files().copy(fileId=settings.GOOGLE_DRIVE_MEETING_NOTES_TEMPLATE_ID, body={
            'name': name,  # Name document
            # Place document in meeting notes folder
            'parents': [settings.GOOGLE_DRIVE_MEETING_NOTES_FOLDER_ID]
        }).execute()

        # The template document has placeholders like {{event_title}}, {{event_type}}, etc.
        # Here we craft a request that will replace the placeholders in the copied document
        # with their actual value.
        requests = [
            {
                'replaceAllText': {
                    'containsText': {
                        'text': '{{event_title}}',
                        'matchCase':  'true'
                    },
                    'replaceText': self.title,
                }
            },
            {
                'replaceAllText': {
                    'containsText': {
                        'text': '{{event_type}}',
                        'matchCase':  'true'
                    },
                    'replaceText': self.get_event_type_display(),
                }
            },
            {
                'replaceAllText': {
                    'containsText': {
                        'text': '{{date}}',
                        'matchCase':  'true'
                    },
                    'replaceText': self.start.strftime('%A, %B %-m %Y'),
                }
            },
            {
                'replaceAllText': {
                    'containsText': {
                        'text': '{{short_date}}',
                        'matchCase':  'true'
                    },
                    'replaceText': self.start.strftime('%m/%d/%y'),
                }
            }
            # Add more replacements here!
        ]

        # Send the update request to Google.
        # We use a "batch" update since we are sendig many "replaceAllText" requests
        # combined into one to save bandwidth.
        result = docs_service.documents().batchUpdate(
            documentId=document.get('id'), body={'requests': requests}).execute()

        # Save the ID of the copied document to the model
        self.meeting_notes_id = document.get('id')

        self.save()
    
    def delete_meeting_notes(self):
        '''
        Deletes the Google Doc meeting notes for the event (if they exist).
        '''
        if not self.meeting_notes_id:
            return
        drive_service.files().delete(fileId=self.meeting_notes_id).execute()

    def generate_thumbnail_link(self):
        '''Generates a thumbnail from the first page of the slideshow.'''
        # Get slideshow
        slideshow = slides_service.presentations().get(presentationId=self.slideshow_id).execute()
        # Get ID of first page
        first_page = slideshow.get('slides')[0]

        thumbnail = slides_service.presentations().pages().getThumbnail(presentationId=self.slideshow_id, pageObjectId=first_page.get('objectId')).execute()
        self.thumbnail_link = thumbnail.get('contentUrl')

    @classmethod
    def post_save(cls, sender, instance, created, *args, **kwargs):
        '''
        This is called *after* an event is saved. It is "saved" because
        some of its details have been updated OR it has been newly created.
        We either create or update the Google Calendar event for it.
        '''
        if created:
            if instance.visibility == 'P' or instance.visibility == 'M':
                instance.create_google_calendar_event()
        else:
            instance.update_google_calendar_event()
        
    def save(self, *args, **kwargs):
        if not self.attendance_code:
            self.attendance_code = ''.join(choice(ascii_uppercase) for i in range(6))
        if self.slideshow_id != None and not self.thumbnail_link:
            self.generate_thumbnail_link()

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        '''
        This is run when a event is deleted. It deletes any associated Google Drive documents
        or Google Calendar events.
        '''
        # Delete meeting notes if they were made when event is deleted
        if self.meeting_notes_id:
            self.delete_meeting_notes()
            
        if self.calendar_event_id:
            self.delete_google_calendar_event()

        # Carry on with actual event delete
        super().delete(*args, **kwargs)

    # String representation of an Event
    # e.g. "Welcome!: Info Session on 11/14/2019"
    def __str__(self):
        return f'{self.title}: {self.get_event_type_display()} on {self.start.strftime("%m/%d/%Y")}'
post_save.connect(Event.post_save, sender=Event)

class EventAttendance(models.Model):
    '''Represents a verifed attendance of one user to one event.'''
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=False, on_delete=models.CASCADE, related_name='attendance')
    event = models.ForeignKey(Event, null=False, on_delete=models.CASCADE, related_name='attendance')

    def __str__(self):
        return self.user.get_full_name()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'event'], name='unique user-event')
        ]

class EventRSVP(models.Model):
    ''''''
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=False, on_delete=models.CASCADE, related_name='rsvps')
    event = models.ForeignKey(Event, null=False, on_delete=models.CASCADE, related_name='rsvps')
    message = models.CharField(max_length=200, help_text='(optional) A condition for RSVPing', blank=True, null=True)

    def is_conditional(self):
        return self.message is not None

    def __str__(self):
        return self.user.get_full_name() + (f' ({self.message})' if self.message else '')

class Project(models.Model):
    '''Project represents a tech-based solution.'''

    # Title of the project
    title = models.CharField(max_length=200, help_text='Required title for project.')
    
    # Description of the project
    description = models.CharField(max_length=3000, help_text='Long description of the project.')

    # Link to project code
    repository_link = models.URLField(help_text='Link to where the code can be found. Most likely GitHub.')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Project "{self.title}" ({self.repository_link})'

class Update(models.Model):
    '''Update represents a post for an update, news article, etc.'''

    title = models.CharField(max_length=200, help_text='Required title for post')

    body = models.TextField(max_length=10000, help_text='The body of the post. Supports Markdown.')

    hidden = models.BooleanField(default=False, help_text='If true then post is not shown anywhere. Use this to create drafts.')

    image_url = models.URLField(blank=True, null=True, help_text='Optional url of cover image to display on top of update and on index page.')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Update "{self.title}" on {self.created_at.strftime("%m/%d/%Y")}'

class UpdateComment(models.Model):
    '''Represents a user comment on an Update.'''

    update = models.ForeignKey(Update, on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    body = models.TextField(max_length=2000, help_text='The text of the comment.')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class RoadmapMilestone(models.Model):
    '''A RoadmapItem represents a reachable milestone for the club.'''

    title = models.CharField(max_length=200, help_text='The title of the milestone')

    description = models.TextField(max_length=10000, help_text='The description of the milestone and what it fully involves.')

    deadline = models.DateField(help_text='When this milestone should be reached at the latest.')

    complete = models.BooleanField(default=False, help_text='Whether this milestone has been achieved yet.')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return 'Milestone: ' + self.title + ' by ' + str(self.deadline)
    
    def passed_deadline(self):
        return timezone.now() > self.deadline