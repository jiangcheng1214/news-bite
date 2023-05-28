import re
import time
import pyshorteners
import tweepy
import os
from dotenv import load_dotenv
from utils.TextEmbeddingCache import TextEmbeddingCache
from utils.Logging import error, info, warn
from utils.Utilities import get_clean_text
from utils.Constants import TWEET_LENGTH_CHAR_LIMIT, TWEET_DEFAULT_POST_LIMIT, TWEET_MATCH_SCORE_THRESHOLD, TWEET_TOPIC_RELAVANCE_SCORE_THRESHOLD, TWEET_SIMILARITY_FOR_POSTING_GUARD_THRESHOLD, TWITTER_ACCOUNT_FOLLOWER_COUNT_REACTION_THRESHOLD, TWEET_REPLY_MAX_AGE_SEC, TWEET_THREAD_COVERAGE_SEC, TWEET_SIMILARITY_FOR_REPLY
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

    def get_recent_posted_tweets(self):
        recent_posted_tweets = []
        for tweet in tweepy.Cursor(self.api.user_timeline).items():
            try:
                second_since_created = int(
                    time.time() - tweet.created_at.timestamp())
                if second_since_created > TWEET_THREAD_COVERAGE_SEC:
                    continue
                recent_posted_tweets.append([tweet.text, tweet.id])
            except Exception as e:
                error("Error getting posted tweet" + str(e))
                continue
        return recent_posted_tweets

    def should_post(self, tweet_json_data, recent_posted_tweets_with_id, pending_tweets_to_post_with_reply_id):
        summary_text = tweet_json_data['summary']
        if len(summary_text) == 0:
            return False
        if tweet_json_data['topic_relavance_score'] < TWEET_TOPIC_RELAVANCE_SCORE_THRESHOLD:
            return False
        if tweet_json_data['match_score'] < TWEET_MATCH_SCORE_THRESHOLD:
            return False
        recent_posted_tweets = [tweet[0]
                                for tweet in recent_posted_tweets_with_id]
        for recent_posted_tweet in recent_posted_tweets:
            similarity = TextEmbeddingCache.get_instance().get_text_similarity_score(
                summary_text, recent_posted_tweet)
            if similarity > TWEET_SIMILARITY_FOR_POSTING_GUARD_THRESHOLD:
                warn(
                    f'Tweet is too similar to a recently posted tweet, similarity: {similarity}. recent_posted_tweet: {recent_posted_tweet}, summary_text: {summary_text}')
                return False
        pending_tweets_to_post = [tweet[0]
                                  for tweet in pending_tweets_to_post_with_reply_id]
        for pending_tweet in pending_tweets_to_post:
            similarity = TextEmbeddingCache.get_instance().get_text_similarity_score(
                summary_text, pending_tweet)
            if similarity > TWEET_SIMILARITY_FOR_POSTING_GUARD_THRESHOLD:
                warn(
                    f'Tweet is too similar to a pending tweet, similarity: {similarity}. pending_tweet: {pending_tweet}, summary_text: {summary_text}')
                return False
        return True

    def get_most_similar_score_text_id(self, text, recent_posted_tweets_with_id):
        if len(text) == 0:
            return []
        result = []
        for recent_posted_tweet_with_id in recent_posted_tweets_with_id:
            recent_posted_tweet = recent_posted_tweet_with_id[0]
            recent_posted_tweet_id = recent_posted_tweet_with_id[1]
            similarity = TextEmbeddingCache.get_instance().get_text_similarity_score(
                text, recent_posted_tweet)
            if similarity > TWEET_SIMILARITY_FOR_REPLY:
                result.append(
                    [similarity, recent_posted_tweet, recent_posted_tweet_id])
        return result

    def upload_summary_items(self, enriched_summary_file_path, max_items=None):
        if not os.path.exists(enriched_summary_file_path):
            error(f"Summary file {enriched_summary_file_path} does not exist")
            return
        info(f"Uploading summary items from {enriched_summary_file_path}")
        post_limit = max_items if max_items else TWEET_DEFAULT_POST_LIMIT
        candidate_limit = post_limit * 2
        tweets_to_post_with_reply_id = []
        recent_posted_tweets_with_id = self.get_recent_posted_tweets()
        info(f"Found {len(recent_posted_tweets_with_id)} recent posted tweets")
        with open(enriched_summary_file_path, 'r') as f:
            for l in f.readlines():
                data = json.loads(l)
                summary_text = data['summary']
                if self.should_post(data, recent_posted_tweets_with_id, tweets_to_post_with_reply_id) == False:
                    continue
                tweet_content = f"{summary_text}".strip()
                if len(data['video_urls']) > 0:
                    try:
                        for media_url in data['video_urls']:
                            tweet_content = f"{tweet_content}\n{media_url}".strip(
                            )
                    except Exception as e:
                        error(f"Error adding video_url {media_url}: {e}")
                else:
                    if len(data['image_urls']) > 0:
                        try:
                            for media_url in data['image_urls']:
                                tweet_content = f"{tweet_content}\n{media_url}".strip(
                                )
                        except Exception as e:
                            error(f"Error adding image_url {media_url}: {e}")
                    if len(data['external_urls']) > 0:
                        try:
                            url = data['external_urls'][0]
                            short_url = self.shorten_url(url)
                            tweet_content = f"{summary_text}\n{short_url}".strip(
                            )
                        except Exception as e:
                            error(f"Error shortening url {url}: {e}")
                            continue
                recent_posts_similarity = self.get_most_similar_score_text_id(
                    summary_text, recent_posted_tweets_with_id)
                reply_id = None
                if (recent_posts_similarity):
                    reply_candidate = max(recent_posts_similarity)[0]
                    similar_score = reply_candidate[0]
                    reply_id = reply_candidate[2]
                    similar_recent_posted_tweet = reply_candidate[1]
                    info(
                        f"Found similar tweet for thread, score: {similar_score}, similar_recent_posted_tweet: {similar_recent_posted_tweet}, reply_id: {reply_id}")
                tweets_to_post_with_reply_id.append([tweet_content, reply_id])
                if len(tweets_to_post_with_reply_id) >= candidate_limit:
                    break
        info(f"{len(tweets_to_post_with_reply_id)} candidate tweets to post")
        tweet_count = 0
        while len(tweets_to_post_with_reply_id) > 0 and tweet_count < post_limit:
            tweet_to_post_with_reply_id = tweets_to_post_with_reply_id.pop(0)
            tweet_content = tweet_to_post_with_reply_id[0]
            reply_id = tweet_to_post_with_reply_id[1]
            if len(tweet_content) > TWEET_LENGTH_CHAR_LIMIT:
                continue
            info(f"Posting tweet:\n{tweet_content}")
            try:
                if reply_id:
                    self.api.update_status(
                        tweet_content, in_reply_to_status_id=reply_id)
                    info(f"Posted reply to {reply_id}, tweet: {tweet_content}")
                else:
                    self.api.update_status(tweet_content)
                    info(f"Posted tweet: {tweet_content}")
                time.sleep(10)
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

    def should_react(self, data):
        topic_relavance_score = data['topic_relavance_score']
        match_score = data['match_score']
        author_follower_count = data['author_follower_count']
        if float(topic_relavance_score) < TWEET_TOPIC_RELAVANCE_SCORE_THRESHOLD or float(match_score) < TWEET_MATCH_SCORE_THRESHOLD:
            return False
        if int(author_follower_count) > TWITTER_ACCOUNT_FOLLOWER_COUNT_REACTION_THRESHOLD:
            return False
        if len(data['video_urls']) > 0 or len(data['image_urls']) > 0:
            return False
        return True

    def untweet_and_unlike_expired_replies(self):
        info("Untweeting and unliking replies")
        for tweet in tweepy.Cursor(self.api.user_timeline).items():
            try:
                second_since_created = int(
                    time.time() - tweet.created_at.timestamp())
                if second_since_created < TWEET_REPLY_MAX_AGE_SEC:
                    continue
                if tweet.in_reply_to_status_id is None:
                    continue

                info(f"Untweeting reply to {tweet.in_reply_to_status_id}")
                self.api.destroy_status(tweet.id)
                time.sleep(1)
                try:
                    info(f"Unliking tweet {tweet.in_reply_to_status_id}")
                    self.api.destroy_favorite(tweet.in_reply_to_status_id)
                    time.sleep(1)
                except Exception as e:
                    error(
                        f"Error unliking tweet {tweet.in_reply_to_status_id}: {e}")
            except Exception as e:
                error(f"Error untweeting and unliking replies: {e}")
                continue

    def react_to_quality_tweets_from_file(self, enriched_tweet_summary_file_path, limit=20):
        if not os.path.exists(enriched_tweet_summary_file_path):
            error(
                f"Quality tweets file {enriched_tweet_summary_file_path} does not exist")
            return
        info(
            f"Reacting to quality tweets from {enriched_tweet_summary_file_path}")
        reacted_tweet_ids = []
        with open(enriched_tweet_summary_file_path, 'r') as f:
            lines = f.readlines()
            for l in lines:
                if len(reacted_tweet_ids) >= limit:
                    break
                data = json.loads(l)
                if not self.should_react(data):
                    continue
                tweet_id = data['tweet_url'].split('/')[-1]
                try:
                    reply_text = f'The AI algorithms by @FinancialNewsAI recognized this as a high-quality tweet (top 1% out of {len(lines)* 100} finance-related tweets in the past 2 hrs). LIKE for more AI endorsements or it will be removed after 24 hrs. We appreciate your feedback!'
                    self.like_and_reply_to_tweet(tweet_id, reply_text)
                    info(f"Reacted to tweet {tweet_id}")
                    time.sleep(15)
                    reacted_tweet_ids.append(tweet_id)
                except Exception as e:
                    error(f"Error reacting to tweet {tweet_id}: {e}")
                    time.sleep(1)
        info(
            f"Reacted to {len(reacted_tweet_ids)} tweets successfully.")

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
    # info(api_manager.get_api().user_timeline(user_id='Forbes'))
    # api_manager.upload_summary_items(
    #     '/Users/chengjiang/Dev/NewsBite/data/tweet_summaries/technology_finance/20230527/summary_24_enriched')
    recent_posted_tweets_with_id = api_manager.get_recent_posted_tweets()
    similar_score_text_id = api_manager.get_most_similar_score_text_id(
        'US government striving to prevent default on national debt after budget breakthrough', recent_posted_tweets_with_id)
    info(similar_score_text_id.sort(key=lambda x: x[0], reverse=True))
    # api_manager.react_to_quality_tweets_from_file(
    #     '/Users/chengjiang/Dev/NewsBite/src/scripts/../../data/tweet_summaries/finance/20230523/summary_24_enriched')
    # for timeline_item in api_manager.get_api().user_timeline(count=500):
    #     second_since_created = int(
    #         time.time() - timeline_item.created_at.timestamp())
    #     info(f"created_at:{timeline_item.created_at}, second_since_created:{second_since_created} {timeline_item.id}, {timeline_item.in_reply_to_status_id}, {timeline_item.favorite_count}, {timeline_item.retweet_count}")
    # api_manager.untweet_and_unlike_expired_replies()
