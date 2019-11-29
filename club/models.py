from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save

from .google import docs_service, drive_service, calendar_service

class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    

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

    # (optional) Link to slideshow
    presentation_link = models.URLField(blank=True, null=True, help_text='An optional link to presentation slides for the event. Most likely Google Slides.')

    # (optonal) Link to meeting notes
    meeting_notes_id = models.CharField(max_length=300, blank=True, null=True, help_text='The ID of the Google Docs meeting notes. This is most likely to an auto-generated Google Docs.')
    
    @property
    def meeting_notes_link(self):
        return 'https://docs.google.com/document/d/' + self.meeting_notes_id

    calendar_event_id = models.CharField(max_length=300, blank=True, null=True, help_text='The Google Calendar event ID')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def create_google_calendar_event(self):
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

    def create_meeting_notes(self):
        if self.meeting_notes_id:
            return

        name = self.start.strftime("[%y/%m/%d] DSC RPI Meeting Notes")

        document = drive_service.files().copy(fileId=settings.GOOGLE_DRIVE_MEETING_NOTES_TEMPLATE_ID, body={
            'name': name,  # Name document
            # Place document in meeting notes folder
            'parents': [settings.GOOGLE_DRIVE_MEETING_NOTES_FOLDER_ID]
        }).execute()

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
        ]

        result = docs_service.documents().batchUpdate(
            documentId=document.get('id'), body={'requests': requests}).execute()

        self.meeting_notes_id = document.get('id')

        self.save()
    
    @classmethod
    def post_save(cls, sender, instance, created, *args, **kwargs):
        if created:
            instance.create_google_calendar_event()
        else:
            instance.update_google_calendar_event()
        


    def delete(self, *args, **kwargs):
        # Delete meeting notes if they were made when event is deleted
        if self.meeting_notes_id:
            drive_service.files().delete(fileId=self.meeting_notes_id).execute()
        
        # Carry on with actual event delete
        super().delete(*args, **kwargs)

    # String representation of an Event
    # e.g. "Welcome!: Info Session on 11/14/2019"
    def __str__(self):
        return f'{self.title}: {self.get_event_type_display()} on {self.start.strftime("%m/%d/%Y")}'
post_save.connect(Event.post_save, sender=Event)

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