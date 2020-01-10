import os
import random
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from .email import send_templated_email

from django.contrib.auth.models import User
from django.contrib import messages

from .models import Member, FAQ, Event, Project, Update, EventAttendance, EventRSVP, RoadmapMilestone
from .forms import MemberAccountForm
from django.utils import timezone
from django.db import IntegrityError

from .google_api import drive_service

from .twitter_api import tweet

def verified_member_check(user):
    return user.member.verified or user.is_staff

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

def faq(request):
    '''
    Displays *answered* Frequently Asked Questions and allows anyone to submit questions of their own.
    '''
    if request.method == 'POST' and 'new-question' in request.POST:
        new_faq = FAQ(question=request.POST['new-question'])
        new_faq.save()
        messages.success(request, 'Submitted your question! If a Core Team member answers it, it will show up here.')
        return HttpResponseRedirect(request.path_info)

    faqs = FAQ.objects.filter(answer__isnull=False)
    return render(request, 'club/faq.html', {'faqs':faqs})

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
            
            if request.user.member.school_username != form.cleaned_data['school_username']:
                # School username was set or changed! Start verification process.
                request.user.member.school_username = form.cleaned_data['school_username']
                request.user.member.verified = False
                request.user.member.verification_code = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for i in range(6))
                email_data = {
                    'user': request.user,
                    'verification_code': request.user.member.verification_code,
                    'website': settings.DOMAIN
                }
                send_templated_email('Verify School Account', 'verification_code', email_data, [request.user.member.school_email])
                messages.warning(request, f'You must verify that you are <b>{request.user.member.school_username}</b>. You have been sent a verification link to your school email address. Please check spam if you cannot find it!')


            if 'profile_image' in request.FILES:
                messages.warning(request, 'Uploaded profile image!')
                profile_image = request.FILES['profile_image']
                request.user.member.profile_image.save(
                    profile_image.name, profile_image)
            request.user.save()
            request.user.member.save()

            messages.success(request, 'Successfully updated your profile!')
        else:
            messages.error(request, 'Form is invalid for some reason...')
        return HttpResponseRedirect(request.path_info)
    # if a GET (or any other method) we'll create a blank form
    else:
        if 'resend-verification-email' in request.GET and request.GET['resend-verification-email'] == '1':
            # Resend verification email
            # Regenerate verification code to prevent hijacking
            request.user.member.verification_code = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for i in range(6))
            request.user.member.save()
            email_data = {
                'user': request.user,
                'verification_code': request.user.member.verification_code,
                'website': settings.DOMAIN
            }
            send_templated_email('Verify School Account', 'verification_code', email_data, [request.user.member.school_email])
            messages.info(request, f'Resent verification email to {request.user.member.school_email}.')
        elif not request.user.member.verified:
            messages.warning(request, 'Please verify your account to RSVP, submit attendance, etc. <a href="?resend-verification-email=1">Resend verification email</a>')
        
        
        form_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'school_username': request.user.member.school_username,
            'grade': request.user.member.grade,
            'bio': request.user.member.bio
        }
        form = MemberAccountForm(form_data)

    return render(request, 'registration/account.html', {'form': form})

@login_required
def verify_account(request):
    if not request.method == 'GET' or not 'code' in request.GET:
        return HttpResponse(status=400)
    
    code = request.GET['code']

    if code == request.user.member.verification_code:
        # Successfully verified user
        messages.success(request, f'Congratulations, you verified your account and are now an official <b>DSC {settings.SCHOOL_NAME_SHORT}</b> member!')
        request.user.member.verified = True
        request.user.member.verification_code = None
        request.user.member.save()
    else:
        # Wrong code!
        messages.warning(request, f'That was not the correct code! Please check the email again.')

    return HttpResponseRedirect('/account')

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

    user_rsvped_events = list(map(lambda rsvp: rsvp.event, request.user.rsvps.all()))
    user_attended_events = list(map(lambda attnd: attnd.event, request.user.attendance.all()))
    
    ongoing_events = Event.objects.filter(
        start__lte=now, end__gte=now, hidden=False)
    upcoming_events = Event.objects.filter(
        start__gte=today, hidden=False).order_by('start')
    past_events = Event.objects.filter(
        end__lt=today, hidden=False).order_by('created_at')

    context = {
        'user_rsvped_events': user_rsvped_events,
        'user_attended_events': user_attended_events,
        'ongoing_events': ongoing_events,
        'upcoming_events': upcoming_events, 
        'past_events': past_events,
        'google_calendar_id': settings.GOOGLE_CALENDAR_ID
    }

    return render(request, 'club/events/index.html', context)


def event_detail(request, event_id):
    '''
    Display an individual :model:`club.Event`.

    **Context**

    ``event``
        An instance of :model:`club.Event`.
    ``attendance_submitted``
        Whether the current user has verified their attendance at this event.
    ``rsvp``
        The RSVP for the current user (if exists).

    **Template:**

    :template:`club/events/detail.html`
    '''

    # Context variables
    now = timezone.now()
    event = get_object_or_404(Event, pk=event_id)
    show_rsvp_form = False
    show_submit_attendance = False
    
    # Make sure user is logged in to allow attendance, rsvping, etc.
    if request.user.is_authenticated:
        attendance_submitted = event.attendance.filter(
            user=request.user).exists()
        show_rsvp_form = 'rsvp' in request.GET and request.GET['rsvp'] == '1'
        rsvp = event.rsvps.filter(user=request.user).first()
        show_slideshows = 'select-slideshow' in request.GET and request.GET['select-slideshow'] == '1'
        show_submit_attendance = 'submit-attendance' in request.GET and request.GET['submit-attendance'] == '1'
    else:
        attendance_submitted = False
        rsvp = None
        show_slideshows = False

    slideshows = []
    if show_slideshows:
        slideshows = drive_service.files().list(corpora='user',
                                                q=f"'{settings.GOOGLE_DRIVE_SLIDE_DECKS_FOLDER_ID}' in parents").execute().get('files')

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
        
        return HttpResponseRedirect(request.path_info)

    context = {
        'event': event,
        'show_rsvp_form': show_rsvp_form,
        'rsvp': rsvp,
        'attendance_submitted': attendance_submitted,
        'show_slideshows': show_slideshows,
        'show_submit_attendance': show_submit_attendance,
        'slideshows': slideshows
    }

    return render(request, 'club/events/detail.html', context)

@user_passes_test(verified_member_check, login_url='/account', redirect_field_name=None)
def event_rsvp(request, event_id):
    now = timezone.now()
    event = get_object_or_404(Event, pk=event_id)
    remove = 'remove' in request.GET and request.GET['remove'] == '1'

    if request.method != 'POST':
        return HttpResponseRedirect(f'/events/{event_id}?rsvp=1')

    rsvp = event.rsvps.filter(user=request.user).first()

    if request.user.is_staff:
        messages.warning(request, 'Core Team members can\'t RSVP for events.')
    elif event.has_started:
        # Event has started so no more RSVPs are accepted
        messages.warning(request, 'This event has already started so you change your RSVP. You can still attend though!')
    elif rsvp:
        # User is already RSVPed
        if remove:
            rsvp.delete()
            messages.success(request, 'Your RSVP has been removed.')
        else:
            messages.warning(request, 'You have already RSVPed for this event.')
    else:
        # New RSVP
        if remove:
            messages.warning(request, 'We could not find your RSVP to remove. You should be fine...')
        else:
            rsvp = EventRSVP(user=request.user, event=event)
            if 'rsvp-message' in request.POST:
                rsvp.message = request.POST['rsvp-message']
            rsvp.save()
            messages.success(request, 'You have RSVPed for the event!')

    return HttpResponseRedirect(f'/events/{event_id}')

@user_passes_test(verified_member_check, login_url='/account', redirect_field_name=None)
def event_attendance(request, event_id):
    now = timezone.now()
    event = get_object_or_404(Event, pk=event_id)

    if request.method != 'POST':
        return HttpResponseRedirect(f'/events/{event_id}?submit-attendance=1')
    
    if not event.is_ongoing:   
        messages.warning(request, 'You can only submit the attendance code during the event. Reach out to a Core Team meber if you have issues.')
        return HttpResponseRedirect(f'/events/{event_id}')

    # All good, check submitted code

    if 'attendance-code' not in request.POST or request.POST['attendance-code'] != event.attendance_code:
        # Missing or invalid code
        messages.warning(request, 'Wrong attendance code. Please make sure you\'re on the right event and have typed in the code correctly.')
    else:
        # Correct code, record their attendance!
        event_attendance = EventAttendance(user=request.user, event=event)
        try:
            event_attendance.save()
            messages.success(
                request, 'Successfully recorded your attendance. Thanks for coming!')
        except IntegrityError:
            messages.warning(
                request, 'You already submitted your attendance code for this event!')

    return HttpResponseRedirect(f'/events/{event_id}')

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


@user_passes_test(verified_member_check, login_url='/account', redirect_field_name=None)
def member_index(request):
    # TODO: docstring
    members = Member.verified_members.all()
    return render(request, 'club/members/index.html', {'members': members})


@user_passes_test(verified_member_check, login_url='/account', redirect_field_name=None)
def member_detail(request, member_id):
    # TODO: docstring
    member = get_object_or_404(Member, pk=member_id)
    if not member.verified:
        messages.warning(request, 'This user has not yet verified their account!')
    return render(request, 'club/members/detail.html', {'member': member})


@staff_member_required
def core_team(request):
    # TODO: docstring
    return render(request, 'club/core_team/index.html', {'google_drive_folder_id': settings.GOOGLE_DRIVE_FOLDER_ID})


@staff_member_required
def roadmap_index(request):
    # TODO: docstring
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
    # TODO: docstring
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
