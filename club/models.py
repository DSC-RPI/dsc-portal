from django.db import models

### Events represent one-time club meetings. 
class Event(models.Model):
    # Recognized types of events
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
    
    # Optional event tagline
    tagline = models.CharField(max_length=200, null=True)
    
    # Required event description
    description = models.CharField(max_length=5000)

    # Date and time range of event
    start = models.DateTimeField()
    end = models.DateTimeField()

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)