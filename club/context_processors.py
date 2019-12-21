from django.conf import settings

def add_school(request):
    return {
        'school_name': settings.SCHOOL_NAME,
        'school_name_short': settings.SCHOOL_NAME_SHORT,
        'google_account': settings.GOOGLE_ACCOUNT,
        'instagram_link': settings.INSTAGRAM_LINK,
        'facebook_link': settings.FACEBOOK_LINK,
        'github_link': settings.GITHUB_LINK
    }