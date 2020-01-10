from django.core.mail import send_mail as sm
from django.conf import settings

def send_email(subject, body, recipients):
    '''
    Sends an email to the recipients.

    subject: str
    body: str
    recipients: list
    '''
    return sm(subject, body, f'DSC {settings.SCHOOL_NAME_SHORT} <{settings.GOOGLE_ACCOUNT}>', recipients)