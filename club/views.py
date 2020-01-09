import os
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from django.contrib.auth.models import User
from django.contrib import messages

from .models import Member, Event, Project, Update, EventAttendance, EventRSVP, RoadmapMilestone
from .forms import MemberAccountForm
from django.utils import timezone
from django.db import IntegrityError

from .google_api import drive_service

from .twitter_api import tweet


def index(request):
    if request.user.is_authenticated:
        now = timezone.now()
        # Find ongoing event
        try:
            ongoing_event = Event.objects.get(
                start__lte=now, end__gte=now, hidden=False)
        except ObjectDoesNotExist:
            ongoing_event = None

        return render(request, 'club/index.html', {'ongoing_event': ongoing_event})
    else:
        core_team = User.objects.filter(is_staff=True)
        today = timezone.now().date()
        closest_event = upcoming_events = Event.objects.filter(
            start__gte=today, hidden=False).order_by('start').first()
        return render(request, 'club/splash.html', {'core_team': core_team, 'closest_event':closest_event})


# def about(request):
#     core_team = User.objects.filter(is_staff=True)
#     return render(request, 'club/about.html', {'core_team': core_team})

@login_required
def user_account(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = MemberAccountForm(request.POST, request.FILES)
        # check whether it's valid:
        if form.is_valid():
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.member.grade = form.cleaned_data['grade']
            request.user.member.bio = form.cleaned_data['bio']

            if 'profile_image' in request.FILES:
                messages.warning(request, 'Uploaded profile image!')
                profile_image = request.FILES['profile_image']
                request.user.member.profile_image.save(
                    profile_image.name, profile_image)
            request.user.save()
            request.user.member.save()

            messages.success(request, 'Successfully updated your profile!')

            return HttpResponseRedirect('/')
        else:
            messages.error(request, 'Form is invalid for some reason...')
    # if a GET (or any other method) we'll create a blank form
    else:
        form_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'grade': request.user.member.grade,
            'bio': request.user.member.bio
        }
        form = MemberAccountForm(form_data)

    return render(request, 'registration/account.html', {'form': form})

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
    now = timezone.now()
    today = now.date()

    ongoing_events = Event.objects.filter(
        start__lte=now, end__gte=now, hidden=False)
    upcoming_events = Event.objects.filter(
        start__gte=today, hidden=False).order_by('start')
    past_events = Event.objects.filter(
        end__lt=today, hidden=False).order_by('created_at')

    return render(request, 'club/events/index.html', {'ongoing_events': ongoing_events, 'upcoming_events': upcoming_events, 'past_events': past_events})


def event_detail(request, event_id):
    '''
    Display an individual :model:`club.Event`.

    **Context**

    ``event``
        An instance of :model:`club.Event`.
    ``ongoing``
        Whether the event is ongoing at the moment.
    ``attendance_submitted``
        Whether the current user has verified their attendance at this event.
    ``rsvped``
        Whether the current user has RSVPed for the event.
    ``past``
        Whether the event ended in the past.

    **Template:**

    :template:`club/events/detail.html`
    '''

    # Context variables
    now = timezone.now()
    event = get_object_or_404(Event, pk=event_id)
    ongoing = event.start <= now <= event.end
    show_rsvp_form = False

    # Make sure user is logged in to allow attendance, rsvping, etc.
    if request.user.is_authenticated:
        attendance_submitted = event.attendance.filter(
            user=request.user).exists()
        show_rsvp_form = 'rsvp' in request.GET and request.GET['rsvp'] == '1'
        rsvped = event.rsvps.filter(user=request.user).exists()
        show_slideshows = 'select-slideshow' in request.GET and request.GET['select-slideshow'] == '1'
    else:
        attendance_submitted = False
        rsvped = False
        show_slideshows = False

    slideshows = []
    if show_slideshows:
        slideshows = drive_service.files().list(corpora='user',
                                                q=f"'{settings.GOOGLE_DRIVE_SLIDE_DECKS_FOLDER_ID}' in parents").execute().get('files')

    started = event.start < now
    past = event.end < now

    # Handle form submissions
    if request.user.is_authenticated and request.method == 'POST':
        if 'attendance-code' in request.POST:
            if request.POST['attendance-code'] == event.attendance_code:
                # Member submitted correct attendance code
                if ongoing:
                    event_attendance = EventAttendance(
                        user=request.user, event=event)
                    try:
                        event_attendance.save()
                        messages.success(
                            request, 'Successfully recorded your attendance. Thanks for coming!')
                    except IntegrityError:
                        messages.warning(
                            request, 'You already submitted your attendance code for this event!')
                else:
                    messages.error(
                        request, 'You can only submit an attendance code during the event! Please let a Core Team member know if you have an issue.')
            else:
                # Member submitted incorrect code
                messages.warning(
                    request, 'Wrong attendance code. Please make sure you\'re on the right event and have typed in the code correctly.')
        elif 'rsvp' in request.POST:
            if started:
                messages.error(
                    request, 'The event has already started (and possibly finished!). You cannot RSVP.')
            elif rsvped:
                # Already RSVPed!
                messages.warning(request, 'You are already RSVPed!')
            else:
                # RSVP user
                rsvp = EventRSVP(user=request.user, event=event)
                if 'rsvp-message' in request.POST:
                    rsvp.message = request.POST['rsvp-message']
                rsvp.save()
                rsvped = True
        elif 'unrsvp' in request.POST:
            if started:
                messages.error(
                    request, 'The event already started (and possibly finished!). You cannot remove your RSVP.')
            else:
                try:
                    EventRSVP.objects.get(
                        user=request.user, event=event).delete()
                    messages.success(
                        request, 'You successfully removed your RSVP.')
                    rsvped = False
                except ObjectDoesNotExist:
                    messages.error(
                        request, 'Failed to find your RSVP to remove... You should be good.')

    # Staff actions
    if request.user.is_staff and request.method == 'POST':
        if 'create-document' in request.POST and request.POST['create-document'] == 'meeting-notes':
            messages.success(
                request, 'Successfully created meeting notes document!')
            event.create_meeting_notes()
        elif 'slideshow-id' in request.POST:
            if request.POST['slideshow-id'] == 'none':
                event.slideshow_id = None
                event.thumbnail_link = None
            else:
                event.slideshow_id = request.POST['slideshow-id']
                event.get_thumbnail_link()
            event.save()
            messages.success(
                request, 'Successfully selected slideshow for event.')
            show_slideshows = False
        elif 'review' in request.POST:
            event.review = request.POST['review']
            messages.success(
                request, 'Successfully saved event review!')
            event.save()

    context = {
        'event': event,
        'show_rsvp_form': show_rsvp_form,
        'rsvped': rsvped,
        'attendance_submitted': attendance_submitted,
        'ongoing': ongoing,
        'started': started,
        'past': past,
        'show_slideshows': show_slideshows,
        'slideshows': slideshows
    }

    return render(request, 'club/events/detail.html', context)


def project_index(request):
    '''
    Display all :model:`club.Project` that users have created.

    **Context**

    ``projects``
        A list of all projects, ordered by most recently updated.

    **Template:**

    :template:`club/projects/index.html`
    '''
    projects = Project.objects.all().order_by('updated_at')

    return render(request, 'club/projects/index.html', {'projects': projects})


def update_index(request):
    '''
    Lists all club :model:`club.Update` (posts, news, recaps, etc.)

    **Context**
        ``updates`` List of all non-hidden updates ordered by creation date
    '''
    updates = Update.objects.filter(hidden=False).order_by('created_at')
    return render(request, 'club/updates/index.html', {'updates': updates})


def update_detail(request, update_id):
    '''
    Display a specific update (post, news, recap, etc.) and comments.

    **Context**
        ``update`` The :model:`club.Update` to display

    **Template**
    :template:'club/updates/detail.html'
    '''
    update = get_object_or_404(Update, pk=update_id)
    return render(request, 'club/updates/detail.html', {'update': update})


@login_required
def member_index(request):
    members = Member.objects.all()
    return render(request, 'club/members/index.html', {'members': members})


@login_required
def member_detail(request, member_id):
    member = get_object_or_404(Member, pk=member_id)
    return render(request, 'club/members/detail.html', {'member': member})


@staff_member_required
def core_team(request):
    return render(request, 'club/core_team/index.html', {'google_drive_folder_id': settings.GOOGLE_DRIVE_FOLDER_ID})


@staff_member_required
def roadmap_index(request):
    try:
        roadmap_milestones = RoadmapMilestone.objects.all().order_by('deadline')
    except ObjectDoesNotExist:
        roadmap_milestones = []

    selected_milestone = None
    if 'milestone_id' in request.GET:
        selected_milestone = RoadmapMilestone.objects.get(
            pk=request.GET['milestone_id'])

    return render(request, 'club/roadmap/index.html', {'roadmap_milestones': roadmap_milestones, 'selected_milestone': selected_milestone})


@staff_member_required
def social_media(request):
    if 'tweet' in request.POST:
        sent_tweet = tweet(request.POST['tweet'])
        messages.success(
            request, f'Successfully tweeted! <a target="_blank" href="https://www.twitter.com/{sent_tweet.user.screen_name}/status/{sent_tweet.id}">Link to tweet</a>')
    return render(request, 'club/core_team/social_media.html', {'twitter_username': os.environ['TWITTER_USERNAME']})


@login_required
def profile_image(request):
    try:
        profile_image = request.FILES['profile-image']
    except:
        pass
