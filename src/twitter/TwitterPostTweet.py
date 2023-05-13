import tweepy
import os
from dotenv import load_dotenv
from utils.Logging import error, info
load_dotenv()


def create_api():
    consumer_key = os.getenv("TWITTER_POSTING_ACCOUNT_CONSUMER_API_KEY")
    consumer_secret = os.getenv("TWITTER_POSTING_ACCOUNT_CONSUMER_API_SECRET")
    access_token = os.getenv("TWITTER_POSTING_ACCOUNT_ACCESS_TOKEN")
    access_token_secret = os.getenv(
        "TWITTER_POSTING_ACCOUNT_ACCESS_SECRET")

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True)
    try:
        api.verify_credentials()
    except Exception as e:
        error("Error creating API" + str(e))
        raise e
    info("API created")
    return api


create_api().update_status_with_media(
    'test', '/Users/chengjiang/Dev/NewsBite/src/twitter/cat.jpg')
