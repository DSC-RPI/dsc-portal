import os
import random
import requests
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from .logger import logger
from .email import send_templated_email

from django.contrib.auth.models import User, Group
from django.contrib import messages

from .models import Member, FAQ, Event, Project, Update, EventAttendance, EventRSVP, EventFeedback, RoadmapMilestone
from .forms import MemberAccountForm, EventFeedbackForm
from django.utils import timezone
from django.db import IntegrityError

from .google_api import drive_service

from .twitter_api import tweet


def verified_member_check(user):
    return user.is_authenticated and (user.member.verified or user.is_staff)


def index(request):
    if request.user.is_authenticated:
        now = timezone.now()

        upcoming_rsvps = filter(
            lambda rsvp: not rsvp.event.has_started, request.user.rsvps.all())

        # Find ongoing event
        try:
            ongoing_event = Event.objects.get(
                start__lte=now, end__gte=now, hidden=False)
        except ObjectDoesNotExist:
            ongoing_event = None

        return render(request, 'club/index.html', {'ongoing_event': ongoing_event, 'upcoming_rsvps': upcoming_rsvps})
    else:
        core_team = User.objects.filter(is_staff=True)
        today = timezone.now().date()
        try:
            closest_event = Event.public_events.latest()
        except ObjectDoesNotExist:
            closest_event = None
        return render(request, 'club/splash.html', {'core_team': core_team, 'closest_event': closest_event})


def faq(request):
    '''
    Displays *answered* Frequently Asked Questions and allows anyone to submit questions of their own.
    '''
    if request.method == 'POST' and 'new-question' in request.POST:
        new_faq = FAQ(question=request.POST['new-question'])
        new_faq.save()
        messages.success(
            request, 'Submitted your question! If a Core Team member answers it, it will show up here.')
        logger.info(f'A new FAQ Question was submitted: "{new_faq.question}"')
        return HttpResponseRedirect(request.path_info)

    faqs = FAQ.objects.filter(answer__isnull=False)
    return render(request, 'club/faq.html', {'faqs': faqs})

def conduct(request):
    '''
    Displays the Code of Conduct.
    '''

    return render(request, 'club/conduct.html')

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
            request.user.member.tags.set(form.cleaned_data['dietary_restrictions'] | form.cleaned_data['skills'])

            if request.user.member.school_username != form.cleaned_data['school_username']:
                # School username was set or changed! Start verification process.
                request.user.member.school_username = form.cleaned_data['school_username']
                request.user.member.verified = False
                request.user.member.verification_code = ''.join(
                    random.choice('abcdefghijklmnopqrstuvwxyz') for i in range(6))
                email_data = {
                    'user': request.user,
                    'verification_code': request.user.member.verification_code,
                    'website': settings.DOMAIN
                }
                send_templated_email('Verify School Account', 'verification_code', email_data, [
                                     request.user.member.school_email])

            if 'profile_image' in request.FILES:
                messages.warning(request, 'Uploaded profile image!')
                profile_image = request.FILES['profile_image']
                name, extension = os.path.splitext(profile_image.name)
                request.user.member.profile_image.save(
                    f'{request.user.username}{extension}', profile_image)
            request.user.save()
            request.user.member.save()

            logger.info(f'User {request.user} updated their profile.')
            messages.success(request, 'Successfully updated your profile!')
        else:
            messages.error(request, 'Form is invalid for some reason...')
        return HttpResponseRedirect(request.path_info)
    # if a GET (or any other method) we'll create a blank form
    else:
        if 'resend-verification-email' in request.GET and request.GET['resend-verification-email'] == '1':
            # Resend verification email
            # Regenerate verification code to prevent hijacking
            request.user.member.verification_code = ''.join(
                random.choice('abcdefghijklmnopqrstuvwxyz') for i in range(6))
            request.user.member.save()
            email_data = {
                'user': request.user,
                'verification_code': request.user.member.verification_code,
                'website': settings.DOMAIN
            }
            send_templated_email('Verify School Account', 'verification_code', email_data, [
                                 request.user.member.school_email])
            logger.info(
                f'Resent school account verification email for user {request.user} to {request.user.member.school_email}')
            messages.info(
                request, f'Resent verification email to {request.user.member.school_email}.')
        
        elif 'reset-school-username' in request.GET and request.GET['reset-school-username'] == '1':
            # Reset school username
            request.user.member.school_username = None
            request.user.member.verification_code = None
            request.user.member.verified = False
            request.user.member.save()
            messages.warning(request, 'Please enter your <a href="#id_school_username">school username</a> to verify your account.')
        elif not request.user.member.verified:
            if not request.user.member.school_username:
                messages.warning(request, 'Please enter your <a href="#id_school_username">school username</a> to verify your account.')

        form_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'school_username': request.user.member.school_username,
            'grade': request.user.member.grade,
            'bio': request.user.member.bio,
            'skills': request.user.member.skills(),
            'dietary_restrictions': request.user.member.dietary_restrictions()
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
        request.user.member.verify()
        request.user.member.save()

        messages.success(
            request, f'Congratulations, you verified your account and are now an official <b>DSC {settings.SCHOOL_NAME_SHORT}</b> member! Check your email for an invite to the Slack.')
    else:
        # Wrong code!
        messages.warning(
            request, f'That was not the correct code! Please check the email again.')

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

    if request.user.is_authenticated:
        user_rsvped_events = list(
            map(lambda rsvp: rsvp.event, request.user.rsvps.all()))
        user_attended_events = list(
            map(lambda attnd: attnd.event, request.user.attendance.all()))
    else:
        user_rsvped_events = []
        user_attended_events = []

    # Start by getting ALL events and then filter based on user
    if request.user.is_staff:
        ongoing_events = Event.objects.filter(
            start__lte=now, end__gte=now)
        upcoming_events = Event.objects.filter(
            start__gte=today).order_by('start')
        past_events = Event.objects.filter(
            end__lt=today)
    else:
        # Non-core team
        ongoing_events = Event.public_events.filter(
            start__lte=now, end__gte=now)
        upcoming_events = Event.public_events.filter(
            start__gte=today).order_by('start')
        past_events = Event.public_events.filter(
            end__lt=today)

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

    # Prevent acces if event is hidden or Core Team only
    if not event.is_publicly_visible and not request.user.is_staff:
        messages.warning(request, 'You cannot view that event.')
        return HttpResponseRedirect('/events')

    show_rsvp_form = False
    show_submit_attendance = False
    show_submit_feedback = False
    
    # Make sure user is logged in to allow attendance, rsvping, etc.
    if request.user.is_authenticated:
        attendance_submitted = event.attendance.filter(
            user=request.user).exists()
        show_rsvp_form = 'rsvp' in request.GET and request.GET['rsvp'] == '1'
        rsvp = event.rsvps.filter(user=request.user).first()
        show_slideshows = 'select-slideshow' in request.GET and request.GET['select-slideshow'] == '1'
        show_submit_attendance = 'submit-attendance' in request.GET and request.GET['submit-attendance'] == '1'
        show_submit_feedback = 'submit-feedback' in request.GET and request.GET['submit-feedback'] == '1'
        feedback_form = EventFeedbackForm()
    else:
        feedback_form = None
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
        'show_submit_feedback': show_submit_feedback,
        'slideshows': slideshows,
        'feedback_form': feedback_form
    }

    return render(request, 'club/events/detail.html', context)


@staff_member_required
def event_planning(request, event_id):
    now = timezone.now()
    event = get_object_or_404(Event, pk=event_id)

    pre_event_count = sum([event.registered_with_google, event.sent_club_email, event.advertised_on_social_media])
    during_event_count = sum([event.recorded_session, event.took_photos])
    post_event_count = sum([event.reported_to_google, event.posted_review_to_social_media])

    context = {
        'event': event,
        'pre_event_count': pre_event_count,
        'during_event_count': during_event_count,
        'post_event_count': post_event_count
    }

    return render(request, 'club/events/event_planning.html', context)

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
        messages.warning(
            request, 'This event has already started so you change your RSVP. You can still attend though!')
    elif rsvp:
        # User is already RSVPed
        if remove:
            rsvp.delete()
            logger.info(f'User {request.user} removed their RSVP for {event}')
            messages.success(request, 'Your RSVP has been removed.')
        else:
            messages.warning(
                request, 'You have already RSVPed for this event.')
    else:
        # New RSVP
        if remove:
            messages.warning(
                request, 'We could not find your RSVP to remove. You should be fine...')
        else:
            rsvp = EventRSVP(user=request.user, event=event)
            if 'rsvp-message' in request.POST:
                rsvp.message = request.POST['rsvp-message']
            rsvp.save()
            logger.info(f'User {request.user} RSVPed for {event}')
            messages.success(request, 'You have RSVPed for the event!')

    return HttpResponseRedirect(f'/events/{event_id}')


@user_passes_test(verified_member_check, login_url='/account', redirect_field_name=None)
def event_attendance(request, event_id):
    now = timezone.now()
    event = get_object_or_404(Event, pk=event_id)

    if request.method != 'POST':
        return HttpResponseRedirect(f'/events/{event_id}?submit-attendance=1')

    if not event.is_ongoing:
        messages.warning(
            request, 'You can only submit the attendance code during the event. Reach out to a Core Team meber if you have issues.')
        return HttpResponseRedirect(f'/events/{event_id}')

    # All good, check submitted code

    if 'attendance-code' not in request.POST or request.POST['attendance-code'] != event.attendance_code:
        # Missing or invalid code
        messages.warning(
            request, 'Wrong attendance code. Please make sure you\'re on the right event and have typed in the code correctly.')
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

@user_passes_test(verified_member_check, login_url='/account', redirect_field_name=None)
def event_feedback(request, event_id):
    now = timezone.now()
    event = get_object_or_404(Event, pk=event_id)

    # If a GET request, redirect to event detail page with feedback modal open
    if request.method != 'POST':
        return HttpResponseRedirect(f'/events/{event_id}?submit-feedback=1')

    # Only allow feedback for past events
    if not event.is_over:
        messages.warning(
            request, 'You can only submit feedback after the event. Reach out to a Core Team meber if you have issues.')
        return HttpResponseRedirect(f'/events/{event_id}')

    # Submit feedback
    form = EventFeedbackForm(request.POST)
    if form.is_valid():
        messages.success(request, 'Thank you for the feedback!')
        feedback = EventFeedback(event=event, user=request.user)

        feedback.overall_rating = form.cleaned_data['overall_rating']
        feedback.date_time_rating = form.cleaned_data['date_time_rating']
        feedback.location_rating = form.cleaned_data['location_rating']
        feedback.pacing_rating = form.cleaned_data['pacing_rating']

        # Optional ratings
        if 'speaker_rating' in form.cleaned_data:
            feedback.speaker_rating = form.cleaned_data['speaker_rating']
        if 'food_rating' in form.cleaned_data:
            feedback.food_rating = form.cleaned_data['food_rating']
        if 'comments' in form.cleaned_data:
            feedback.comments = form.cleaned_data['comments']

        feedback.save()
    else:
        logger.error(form.errors)
        messages.error(request, 'There was an issue submitting your feedback.')

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
        messages.warning(
            request, 'This user has not yet verified their account!')
    return render(request, 'club/members/detail.html', {'member': member})


@staff_member_required
def core_team(request):
    # TODO: docstring
    core_team = User.objects.filter(is_staff=True)
    links = [
        ('Community Leads Portal', 'https://communityleads.dev/home/'),
        ('Google Cloud Console', 'https://console.cloud.google.com/'),
        ('Club Google Drive', 'https://drive.google.com/drive/u/1/folders/{{ google_drive_folder_id }}'),
        ('DSC Lead Home', 'https://sites.google.com/google.com/developerstudentclubleads/home'),
        ('DSC Resources Spreadsheet', 'https://docs.google.com/spreadsheets/d/1qHvNvuYzI0Wjt_QUU85JMsKUZIQLmwg0VKYMpifZ914/edit#gid=0'),
        ('Cloud Study Jams Organizer Guide', 'https://docs.google.com/presentation/d/1_YaJ4YJC2vXL16m0feYijtYZQa3809k2mzMPALozBeU/edit#slide=id.g707393ed40_0_1980')
    ]
    if settings.SCHOOL_NAME_SHORT == 'RPI':
        links.append(('RPI Event Scheduler', 'https://rpi.emscloudservice.com/web/'))

    context = {
        'core_team': core_team,
        'google_drive_folder_id': settings.GOOGLE_DRIVE_FOLDER_ID,
        'links': links
    }
    return render(request, 'club/core_team/index.html', context)

@staff_member_required
def core_team_role(request, role_name):
    groups = {}
    for group in Group.objects.all():
        formatted_group_name = group.name.lower().replace(' ', '_')
        groups[formatted_group_name] = group
    
    print(groups)

    # Ensure core team member is in specified group
    if role_name in groups and request.user.groups.filter(name=groups[role_name]).exists():
        return render(request, f'club/core_team/roles/{role_name}.html')
    else:
        messages.warning(request, 'You do not have permission to view that Core Team page!')
        return HttpResponseRedirect('/core-team')

@staff_member_required
def core_team_email(request):
    verified_member_email_list = list(map(lambda member: member.user.email, Member.objects.filter(verified=True)))
    verified_member_emails = '; '.join(verified_member_email_list)
    all_member_emails = '; '.join(list(map(lambda member: member.user.email, Member.objects.all())))
    all_user_emails = '; '.join(list(map(lambda user: user.email, User.objects.all())))
    context = {
        'verified_member_emails': verified_member_emails,
        'all_member_emails': all_member_emails,
        'all_user_emails': all_user_emails
    }

    if request.method == 'POST':
        # Send email
        sections = [{'title': z[0], 'image': z[1], 'content': z[2]} for z in zip(request.POST.getlist('section-title'), request.POST.getlist('section-image'), request.POST.getlist('section-content'))]
        data = {
            'sections': sections
        }
        if 'show-preview' in request.POST and request.POST['show-preview'] == '1':
            return render(request, 'club/emails/update.html', data)
        else:
            if settings.DEBUG:
                messages.warning(request, f'Sent to only {settings.GOOGLE_ACCOUNT} since in dev mode.')
                send_templated_email(request.POST['email-subject'], 'update', data, [settings.GOOGLE_ACCOUNT])
            else:
                send_templated_email(request.POST['email-subject'], 'update', data, verified_member_email_list)
                messages.success(request, f'Sent email to all verified members!')
            return HttpResponseRedirect(request.path_info)


    return render(request, 'club/core_team/email.html', context)

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

@staff_member_required
def member_management(request):
    unverified_members = Member.objects.filter(verified=False, school_username__isnull=False)
    verified_members = Member.verified_members.all()

    if request.method == 'POST' and 'verify-member-id' in request.POST:
        # Verify specified member
        member = Member.objects.get(pk=request.POST['verify-member-id'])
        if member is None:
            messages.warning(request, f'No such member found!')
        elif member.verified:
            messages.warning(request, f'{member.user.get_full_name()} is already verfified!')
        else:
            member.verify()
            member.save()
            messages.success(request, f'Successfully verified {member.user.get_full_name()}!')
            return HttpResponseRedirect(request.path_info)

    context = {
        'unverified_members': unverified_members,
        'verified_members': verified_members
    }
    return render(request, 'club/core_team/member_management.html', context)

@login_required
def profile_image(request):
    try:
        profile_image = request.FILES['profile-image']
    except:
        pass
