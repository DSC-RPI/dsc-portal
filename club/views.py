from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from .models import Event

def index(request):
    return render(request, 'club/index.html')

def splash(request):
    return render(request, 'club/splash.html')

# EVENTS
def event_index(request):
    events = Event.objects.all()
    return render(request, 'club/events/index.html', {'events':events})

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