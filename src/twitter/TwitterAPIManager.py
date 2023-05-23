import re
import time
import pyshorteners
import tweepy
import os
import redis
from dotenv import load_dotenv
from utils.Logging import error, info, warn
from utils.Utilities import TWEET_LENGTH_CHAR_LIMIT, TWEET_DEFAULT_POST_LIMIT, DEFAULT_REDIS_CACHE_EXPIRE_SEC, REDIS_POSTED_TWEETS_KEY, TWEET_MATCH_SCORE_THRESHOLD, TWEET_TOPIC_RELAVANCE_SCORE_THRESHOLD, TWEET_SIMILARITY_FOR_POSTING_GUARD_THRESHOLD, get_clean_text
import json
from twitter.TweetSummaryEnricher import TweetSummaryEnricher
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
        if tweet_json_data['topic_relavance_score'] < TWEET_TOPIC_RELAVANCE_SCORE_THRESHOLD:
            return False
        if tweet_json_data['match_score'] < TWEET_MATCH_SCORE_THRESHOLD:
            return False
        posted_tweets = self.redis_client.get(REDIS_POSTED_TWEETS_KEY)
        if not posted_tweets:
            return True
        posted_tweets = json.loads(posted_tweets)
        for posted_tweet in posted_tweets:
            similarity = self.tagger.get_similarity(
                summary_text, posted_tweet)
            if similarity > TWEET_SIMILARITY_FOR_POSTING_GUARD_THRESHOLD:
                warn(
                    f'Tweet is too similar to a previously posted tweet, similarity: {similarity}. posted_tweet: {posted_tweet}, summary_text: {summary_text}')
                return False
        return True

    def upload_summary_items(self, enriched_summary_file_path, max_items=None):
        if not os.path.exists(enriched_summary_file_path):
            error(f"Summary file {enriched_summary_file_path} does not exist")
            return
        info(f"Uploading summary items from {enriched_summary_file_path}")
        post_limit = max_items if max_items else TWEET_DEFAULT_POST_LIMIT
        tweet_to_post = []
        with open(enriched_summary_file_path, 'r') as f:
            for l in f.readlines():
                data = json.loads(l)
                summary_text = data['summary']
                if self.should_post(data) == False:
                    continue
                tweet_content = f"{summary_text}".strip()
                media_url_added = False
                if len(data['video_urls']) > 0:
                    try:
                        for media_url in data['video_urls']:
                            tweet_content = f"{tweet_content}\n{media_url}".strip(
                            )
                            media_url_added = True
                    except Exception as e:
                        error(f"Error adding video_url {media_url}: {e}")
                if len(data['image_urls']) > 0:
                    try:
                        for media_url in data['image_urls']:
                            tweet_content = f"{tweet_content}\n{media_url}".strip(
                            )
                            media_url_added = True
                    except Exception as e:
                        error(f"Error adding image_url {media_url}: {e}")

                if not media_url_added and len(data['external_urls']) > 0:
                    try:
                        url = data['external_urls'][0]
                        short_url = self.shorten_url(url)
                        tweet_content = f"{summary_text}\n{short_url}".strip()
                    except Exception as e:
                        error(f"Error shortening url {url}: {e}")
                        continue
                tweet_to_post.append(tweet_content)
        info(f"{len(tweet_to_post)} tweets to post")
        tweet_count = 0
        while len(tweet_to_post) > 0 and tweet_count < post_limit:
            tweet_content = tweet_to_post.pop(0)
            if len(tweet_content) > TWEET_LENGTH_CHAR_LIMIT:
                continue
            info(f"Posting tweet:\n{tweet_content}")
            try:
                self.api.update_status(tweet_content)
                posted_tweets = self.redis_client.get(REDIS_POSTED_TWEETS_KEY)
                if not posted_tweets:
                    posted_tweets = []
                else:
                    posted_tweets = json.loads(posted_tweets)
                posted_tweets.append(get_clean_text(tweet_content))
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

    def react_to_quality_tweets_from_file(self, quality_tweets_file, limit=20):
        if not os.path.exists(quality_tweets_file):
            error(
                f"Quality tweets file {quality_tweets_file} does not exist")
            return
        reacted_tweet_ids = []
        with open(quality_tweets_file, 'r') as f:
            lines = f.readlines()
            for l in lines:
                if len(reacted_tweet_ids) >= limit:
                    break
                data = json.loads(l)
                tweet_id = data['id']
                quality = data['quality']
                if float(quality) < 0.5:
                    continue
                try:
                    reply_text = f'The AI algorithms by @FinancialNewsAI has recognized this tweet as a high-quality one, ranking it in the top 1% out of {len(lines)* 100} (±5%) finance-related tweets in the past 2 hours. DO NOT follow us but LIKE this reply for more AI endorsements. We appreciate your feedback!'
                    self.like_and_reply_to_tweet(tweet_id, reply_text)
                    info(f"Reacted to tweet {tweet_id}")
                    time.sleep(15)
                    reacted_tweet_ids.append(tweet_id)
                except Exception as e:
                    error(f"Error reacting to tweet {tweet_id}: {e}")
                    time.sleep(1)

    def like_and_reply_to_tweet(self, tweet_id, reply_text):
        self.api.create_favorite(tweet_id)
        self.api.update_status(
            status=reply_text, in_reply_to_status_id=tweet_id, auto_populate_reply_metadata=True)
        info(f"Replied to tweet {tweet_id}, reply_text: {reply_text}")

    def shorten_url(self, url):
        url_shortener = pyshorteners.Shortener()
        return url_shortener.tinyurl.short(url)

    def get_api(self):
        return self.api


if __name__ == "__main__":
    api_manager = TwitterAPIManager()
    api_manager.upload_summary_items(
        '/Users/chengjiang/Dev/NewsBite/data/tweet_summaries/finance/20230521/summary_21_enriched')
    # api_manager.react_to_quality_tweets_from_file(
    #     '/Users/chengjiang/Dev/NewsBite/data/tweet_extracted_news/finance/20230519/news_23')
