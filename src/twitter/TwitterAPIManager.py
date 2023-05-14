import re
import time
import pyshorteners
import tweepy
import os
from dotenv import load_dotenv
from utils.Logging import error, info
from utils.Utilities import TWEET_LENGTH_CHAR_LIMIT, TWEET_CONTENT_BUFFER, TWEET_ONE_TIME_POST_LIMIT
import json
load_dotenv()


class TwitterAPIManager:
    def __init__(self):
        self.api = self.create_api()

    def create_api(self):
        consumer_key = os.getenv("TWITTER_POSTING_ACCOUNT_CONSUMER_API_KEY")
        consumer_secret = os.getenv(
            "TWITTER_POSTING_ACCOUNT_CONSUMER_API_SECRET")
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

    def upload_daily_summary(self, enriched_summary_file_path):
        if not os.path.exists(enriched_summary_file_path):
            error(f"Summary file {enriched_summary_file_path} does not exist")
            return
        clean_content_list = []
        short_url_list = []
        with open(enriched_summary_file_path, 'r') as f:
            for l in f.readlines():
                data = json.loads(l)
                summary_text = data['summary']
                cleaned_summary_text = self.clean_text(summary_text)
                if len(cleaned_summary_text) == 0:
                    continue
                if data['unwound_url'] is None or len(data['unwound_url']) == 0:
                    continue
                url = data['unwound_url']
                try:
                    short_url = self.shorten_url(url)
                except Exception as e:
                    error(f"Error shortening url {url}: {e}")
                    continue
                clean_content_list.append(cleaned_summary_text)
                short_url_list.append(short_url)

        tweet_count = 0
        while len(clean_content_list) > 0 and tweet_count < TWEET_ONE_TIME_POST_LIMIT:
            clean_content = clean_content_list.pop(0)
            short_url = short_url_list.pop(0)
            if len(clean_content) > TWEET_LENGTH_CHAR_LIMIT - TWEET_CONTENT_BUFFER:
                continue
            tweet_content = f"{clean_content}\n{short_url}".strip()
            info(f"Posting tweet:\n{tweet_content}")
            try:
                self.api.update_status(tweet_content)
                tweet_count += 1
            except Exception as e:
                error(f"Error posting tweet: {e}")
                break
            time.sleep(1)
        info(
            f"Posted {tweet_count} tweets successfully.")

    def clean_text(self, text: str):
        cleaned_text = text.strip()
        cleaned_text = re.sub(r'^\d+\.?\s*', '', cleaned_text)
        cleaned_text = re.sub(r'^-\s*', '', cleaned_text)
        cleaned_text = re.sub(r'^\"|\"$', '', cleaned_text)
        return cleaned_text

    def shorten_url(self, url):
        url_shortener = pyshorteners.Shortener()
        return url_shortener.tinyurl.short(url)

    def get_api(self):
        return self.api
