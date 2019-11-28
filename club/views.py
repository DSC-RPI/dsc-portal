from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from .models import Event

from datetime import date

def index(request):
    if request.user.is_authenticated:
        return render(request, 'club/index.html')
    else:
        return render(request, 'club/splash.html')

def about(request):
    return render(request, 'club/about.html')

# EVENTS
def event_index(request):
    '''
    Display upcoming and past Events. Also shows a Google Calendar widget displaying all
    events.

    **Context**

    ``upcoming_events``
        A list of all non-hidden :model:`club.Event` that start on or after the current day.
    
    ``past_events``
        A list of all non-hidden :model:`club.Event` that ended before the current day. 

    **Template:**

    :template:`club/events/index.html`
    '''
    today = date.today()

    upcoming_events = Event.objects.filter(start__gt=today, hidden=False)
    past_events = Event.objects.filter(end__lt=today, hidden=False)

    return render(request, 'club/events/index.html', {'upcoming_events':upcoming_events, 'past_events':past_events})

def event_detail(request, event_id):
    '''
    Display an individual :model:`club.Event`.

    **Context**

    ``event``
        An instance of :model:`club.Event`.

    **Template:**

    :template:`club/events/detail.html`
    '''
    event = get_object_or_404(Event, pk=event_id)
    return render(request, 'club/events/detail.html', {'event':event})

def project_index(request):
    projects = []
    return render(request, 'club/projects/index.html', {'projects':projects})

def update_index(request):
    updates = []
    return render(request, 'club/updates/index.html')