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
    today = date.today()

    upcoming_events = Event.objects.filter(start__gt=today)
    past_events = Event.objects.filter(end__lt=today)

    return render(request, 'club/events/index.html', {'upcoming_events':upcoming_events, 'past_events':past_events})

def event_detail(request, event_id):
    '''
    Display an individual :model:`club.Event`.

    **Context**

    ``event``
        An instance of :model:`club.Event`.

    **Template:**

    :template:`club/event_detail.html`
    '''
    event = get_object_or_404(Event, pk=event_id)
    return render(request, 'club/events/detail.html', {'event':event})