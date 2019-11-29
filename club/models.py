from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

from .google import docs_service, drive_service

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
    meeting_notes_link = models.URLField(blank=True, null=True, help_text='An optional link to the meeting notes for the event. This is most likely to an auto-generated Google Docs.')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def create_meeting_notes(self):
        if self.meeting_notes_link:
            return

        name = start.strftime("[%y/%m/%d] DSC RPI Meeting Notes")

        document = drive_service.files().copy(fileId=settings.GOOGLE_DRIVE_MEETING_NOTES_TEMPLATE_ID, body={
            'name': name,  # Name document
            # Place document in meeting notes folder
            'parents': [settings.GOOGLE_DRIVE_MEETING_NOTES_FOLDER_ID]
        }).execute()

        requests = [
            {
                'replaceAllText': {
                    'containsText': {
                        'text': '{{date}}',
                        'matchCase':  'true'
                    },
                    'replaceText': start.strftime('%A, %B %-m %Y | %y/%m/%d'),
                }
            }
        ]

        result = docs_service.documents().batchUpdate(
            documentId=document.get('id'), body={'requests': requests}).execute()

        self.meeting_notes_link = 'https://docs.google.com/document/d/' + document.get('id')

        self.save()
    
    # String representation of an Event
    # e.g. "Welcome!: Info Session on 11/14/2019"
    def __str__(self):
        return f'{self.title}: {self.get_event_type_display()} on {self.start.strftime("%m/%d/%Y")}'

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