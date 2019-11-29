from django.db import models
from django.contrib.auth.models import User

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

    # (optional) Link to slideshow
    presentation_link = models.URLField(blank=True, null=True, help_text='An optional link to presentation slides for the event. Most likely Google Slides.')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Update "{self.title}" on {self.created_at.strftime("%m/%d/%Y")}'