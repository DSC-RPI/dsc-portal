from django.conf import settings
import facebook

facebook_graph = facebook.GraphAPI(
    access_token=settings.FACEBOOK_ACCESS_TOKEN, version='3.1')