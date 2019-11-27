from django.db import models

### Events represent one-time club meetings. 
class Event(models.Model):
    # Recognized types of events
    # Taken from https://sites.google.com/google.com/developerstudentclubleads/dsc-activities-reporting
    EVENT_TYPES = [
        ('IS', 'Info Session'),
        ('WS', 'Workshop'),
        ('SJ', 'Study Jam Workshop'),
        ('HO', 'Hands-on Workshop'),
        ('HA', 'Hackathon'),
        ('SS', 'Speaker Session'),
        ('SC', 'Showcase')
    ]
    event_type = models.CharField(max_length=2, choices=EVENT_TYPES)
    
    # Title of Event limited to 100 characters
    title = models.CharField(max_length=100)
    
    # (Optional) Event tagline
    tagline = models.CharField(max_length=200, blank=True, null=True)
    
    # Required event description
    description = models.CharField(max_length=5000)

    # Date and time range of event
    start = models.DateTimeField()
    end = models.DateTimeField()

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # String representation of an Event
    # e.g. "Welcome!: Info Session on 11/14/2019"
    def __str__(self):
        return f'{self.title}: {self.get_event_type_display()} on {self.start.strftime("%m/%d/%Y")}'