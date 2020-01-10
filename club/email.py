from django.core.mail import send_mail as sm
from django.template.loader import render_to_string
from django.conf import settings
from .logger import logger

FROM = f'DSC {settings.SCHOOL_NAME_SHORT} <{settings.GOOGLE_ACCOUNT}>'

def send_templated_email(subject, template, data, recipients):
    # https://stackoverflow.com/questions/2809547/creating-email-templates-with-django
    html_message = render_to_string(f'club/emails/{template}.html', data)
    try:
        # Try to find the plaintext template
        plain_message = render_to_string(f'club/emails/{template}.txt', data)
    except:
        # If it doesn't exist, fallback to just HTML
        plain_message = html_message

    logger.info(f'Sending email with subject "{subject}" to {recipients} with template "{template}"')
    return sm(subject, plain_message, FROM, recipients, html_message=html_message)

def send_email(subject, body, recipients):
    '''
    Sends an email to the recipients.

    subject: str
    body: str
    recipients: list
    '''
    logger.info(f'Sending email with subject "{subject}" to {recipients}')
    return sm(subject, body, FROM, recipients, html_message=body)