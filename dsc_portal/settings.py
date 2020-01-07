"""
Django settings for dsc_portal project.

Generated by 'django-admin startproject' using Django 2.2.6.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os
from google.oauth2 import service_account
import django_heroku

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['SECRET_KEY']

GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ['ENV'] == 'development'

ALLOWED_HOSTS = ['127.0.0.1', os.environ['WEBSITE']]

# DSC GOOGLE ACCOUNT
GOOGLE_ACCOUNT = os.environ['GOOGLE_ACCOUNT']
DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'

# SCHOOL INFO
SCHOOL_NAME = os.environ['SCHOOL_NAME']
SCHOOL_NAME_SHORT = os.environ['SCHOOL_NAME_SHORT']
INSTAGRAM_LINK = os.environ['INSTAGRAM_LINK']
FACEBOOK_LINK = os.environ['FACEBOOK_LINK']
GITHUB_LINK = 'https://github.com/DSC-RPI/dsc-portal'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admindocs',
    'social_django',
    'club'
]

MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware'
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

ROOT_URLCONF = 'dsc_portal.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'club.context_processors.add_school',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect'
            ],
        },
    },
]

WSGI_APPLICATION = 'dsc_portal.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

if os.environ['ENV'] != 'development':
    # SECURE_CONTENT_TYPE_NOSNIFF = True
    # SECURE_BROWSER_XSS_FILTER = True
    # SECURE_SSL_REDIRECT = True
    # CSRF_COOKIE_SECURE = True
    # SESSION_COOKIE_SECURE = True
    X_FRAME_OPTIONS = 'DENY'

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

LOGIN_REDIRECT_URL = '/'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.github.GithubOAuth2',
    'django.contrib.auth.backends.ModelBackend'
)

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.social_auth.associate_by_email',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)

SOCIAL_AUTH_GITHUB_KEY=os.environ['SOCIAL_AUTH_GITHUB_KEY']
SOCIAL_AUTH_GITHUB_SECRET=os.environ['SOCIAL_AUTH_GITHUB_SECRET']

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=os.environ['GOOGLE_OAUTH_CLIENT_ID']
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=os.environ['GOOGLE_OAUTH_CLIENT_SECRET']
SOCIAL_AUTH_GOOGLE_PLUS_AUTH_EXTRA_ARGUMENTS = {
      'access_type': 'offline'
}
# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/New_York'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

DOMAIN = 'https://' + os.environ['WEBSITE']

# Google
GOOGLE_SERVICE_ACCOUNT_FILE = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
GOOGLE_DRIVE_FOLDER_ID = os.environ['GOOGLE_DRIVE_FOLDER_ID']
GOOGLE_DRIVE_MEETING_NOTES_FOLDER_ID = os.environ['GOOGLE_DRIVE_MEETING_NOTES_FOLDER_ID']
GOOGLE_DRIVE_MEETING_NOTES_TEMPLATE_ID = os.environ['GOOGLE_DRIVE_MEETING_NOTES_TEMPLATE_ID']
GOOGLE_DRIVE_SLIDE_DECKS_FOLDER_ID = os.environ['GOOGLE_DRIVE_SLIDE_DECKS_FOLDER_ID']
GOOGLE_CALENDAR_ID = os.environ['GOOGLE_CALENDAR_ID']
GS_PROJECT_ID = os.environ['GS_PROJECT_ID']
GS_BUCKET_NAME = os.environ['GS_BUCKET_NAME']
GS_DEFAULT_ACL = 'publicRead'
GS_SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/devstorage.full_control']
GS_CREDENTIALS = service_account.Credentials.from_service_account_file(GOOGLE_SERVICE_ACCOUNT_FILE, scopes=GS_SCOPES)

FACEBOOK_ACCESS_TOKEN = os.environ['FACEBOOK_ACCESS_TOKEN']

# Activate Django-Heroku.
# https://devcenter.heroku.com/articles/django-app-configuration
django_heroku.settings(locals())