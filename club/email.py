from django.core.mail import send_mail as sm
from django.conf import settings

def send_email(subject, body, recipients):
    return sm(subject, body, settings.GOOGLE_ACCOUNT, recipients)