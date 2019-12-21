import twitter
import os

twitter_api = twitter.Api(consumer_key=os.environ['TWITTER_CONSUMER_API_KEY'],
    consumer_secret=os.environ['TWITTER_CONSUMER_API_SECRET_KEY'],
    access_token_key=os.environ['TWITTER_ACCESS_TOKEN'],
    access_token_secret=os.environ['TWITTER_ACCESS_TOKEN_SECRET'])

def tweet(message):
    return twitter_api.PostUpdate(message)