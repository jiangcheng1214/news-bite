import tweepy
import os
from dotenv import load_dotenv
from utils.Logging import error, info
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

    def upload_daily_summary(self, date, topic):
        enriched_summary_path = os.path.join(os.path.dirname(
            __file__),  '..', '..', 'data', 'tweets', topic, date, "daily_sum_enriched.jsons")
        if not os.path.exists(enriched_summary_path):
            error(f"Summary file {enriched_summary_path} does not exist")
            return
        tweet_content = ""
        with open(enriched_summary_path, 'r') as f:
            current_tweet_count = 0
            for l in f.readlines():
                data = json.loads(l)
                if not 'unwound_url' in data:
                    continue
                summary_text = data['summary'].strip()
                url = data['unwound_url']
                tweet_content += f"{summary_text}\n{url}\n"
                current_tweet_count += 1
                if current_tweet_count == 2:
                    tweet_content = tweet_content.strip()
                    info(f"Posting tweet {tweet_content}")
                    self.api.update_status(tweet_content)
                    tweet_content = ""
                    current_tweet_count = 0
