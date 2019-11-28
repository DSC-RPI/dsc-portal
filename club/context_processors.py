from django.conf import settings

def add_school(request):
    return {
        'school_name': settings.SCHOOL_NAME,
        'school_name_short': settings.SCHOOL_NAME_SHORT
    }