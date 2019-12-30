from django.conf import settings
from googleapiclient.discovery import build

credentials = settings.GS_CREDENTIALS

docs_service = build('docs', 'v1', credentials=credentials)
slides_service = build('slides', 'v1', credentials=credentials)
drive_service = build('drive', 'v3', credentials=credentials)
calendar_service = build('calendar', 'v3', credentials=credentials)