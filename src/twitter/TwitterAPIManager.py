import re
import time
import pyshorteners
import tweepy
import os
import redis
from dotenv import load_dotenv
from utils.Logging import error, info, warn
from utils.Utilities import TWEET_LENGTH_CHAR_LIMIT, TWEET_CONTENT_BUFFER, TWEET_DEFAULT_POST_LIMIT, DEFAULT_REDIS_CACHE_EXPIRE_SEC, REDIS_POSTED_TWEETS_KEY
import json
from utils.TweetSummaryEnricher import TweetSummaryEnricher
load_dotenv()


class TwitterAPIManager:
    def __init__(self):
        self.api = self.create_api()
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.tagger = TweetSummaryEnricher()

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

    def should_post(self, tweet_json_data):
        summary_text = tweet_json_data['summary']
        if len(summary_text) == 0:
            return False
        if tweet_json_data['unwound_url'] is None or len(tweet_json_data['unwound_url']) == 0:
            return False
        posted_tweets = self.redis_client.get(REDIS_POSTED_TWEETS_KEY)
        if not posted_tweets:
            return True
        posted_tweets = json.loads(posted_tweets)
        for posted_tweet in posted_tweets:
            similarity = self.tagger.get_similarity(
                summary_text, posted_tweet)
            if similarity > 0.9:
                warn(
                    f'Tweet is too similar to a previously posted tweet, similarity: {similarity}. posted_tweet: {posted_tweet}, summary_text: {summary_text}')
                return False
        return True

    def upload_summary_items(self, enriched_summary_file_path, max_items=None):
        if not os.path.exists(enriched_summary_file_path):
            error(f"Summary file {enriched_summary_file_path} does not exist")
            return
        post_limit = max_items if max_items else TWEET_DEFAULT_POST_LIMIT
        summary_text_list = []
        short_url_list = []
        with open(enriched_summary_file_path, 'r') as f:
            for l in f.readlines():
                data = json.loads(l)
                summary_text = data['summary']
                if self.should_post(data) == False:
                    continue
                url = data['unwound_url']
                try:
                    short_url = self.shorten_url(url)
                except Exception as e:
                    error(f"Error shortening url {url}: {e}")
                    continue
                summary_text_list.append(summary_text)
                short_url_list.append(short_url)

        tweet_count = 0
        while len(summary_text_list) > 0 and tweet_count < post_limit:
            clean_content = summary_text_list.pop(0)
            short_url = short_url_list.pop(0)
            if len(clean_content) > TWEET_LENGTH_CHAR_LIMIT - TWEET_CONTENT_BUFFER:
                continue
            tweet_content = f"{clean_content}\n{short_url}".strip()
            info(f"Posting tweet:\n{tweet_content}")
            try:
                self.api.update_status(tweet_content)
                posted_tweets = self.redis_client.get(REDIS_POSTED_TWEETS_KEY)
                if not posted_tweets:
                    posted_tweets = []
                else:
                    posted_tweets = json.loads(posted_tweets)
                posted_tweets.append(clean_content)
                self.redis_client.set(
                    REDIS_POSTED_TWEETS_KEY, json.dumps(posted_tweets),  ex=DEFAULT_REDIS_CACHE_EXPIRE_SEC)
                tweet_count += 1
            except Exception as e:
                error(f"Error posting tweet: {e}")
                continue
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

if __name__ == "__main__":
    api_manager = TwitterAPIManager()
    api_manager.upload_summary_items(
        '/Users/chengjiang/Dev/NewsBite/data/tweet_summaries/finance/20230517/summary_24_enriched')
