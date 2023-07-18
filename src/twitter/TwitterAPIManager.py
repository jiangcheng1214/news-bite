import re
import time
import pyshorteners
import tweepy
import os
from dotenv import load_dotenv
from langChain.LangChainAPIManager import LangChainAPIManager
from newsAPI.NewsAPIManager import GeneralNewsType, NewsAPIManager, NewsAPIType
from openAI.OpenaiGptApiManager import OpenaiGptApiManager
from openAI.OpenaiClipFeatureGenerator import OpenaiClipFeatureGenerator
from utils.TextEmbeddingCache import TextEmbeddingCache
from utils.Logging import error, info, warn
from utils.Utilities import OpenaiModelVersion, get_clean_text, shorten_url
from utils.Constants import TWEET_LENGTH_CHAR_LIMIT, TWEET_DEFAULT_POST_LIMIT, TWEET_MATCH_SCORE_THRESHOLD, TWEET_TOPIC_RELAVANCE_SCORE_THRESHOLD, TWEET_SIMILARITY_FOR_POSTING_GUARD_THRESHOLD, TWEET_VIDEO_DURATION_LIMIT_IN_SECOND_DEFAULT, TWITTER_ACCOUNT_FOLLOWER_COUNT_REACTION_THRESHOLD, TWEET_REPLY_MAX_AGE_SEC, TWEET_THREAD_COVERAGE_SEC, TWEET_SIMILARITY_FOR_REPLY, TWITTER_BEARER_TOKEN_EVAR_KEY
from utils.Utilities import trim_video
import json
from enum import Enum
from typing import List

from youtube.YoutubeDownloader import YoutubeDownloader
load_dotenv()


class TwitterAPIManagerAccountType(Enum):
    TwitterAPIManagerAccountTypeCrypto = 0
    TwitterAPIManagerAccountTypeFintech = 1


class TwitterPostCandidate:
    def __init__(self, initial_dict: dict):
        self.news_url = initial_dict.get("news_url")
        self.image_url = initial_dict.get("image_url")
        self.news_content = initial_dict.get("news_content")
        self.hashtags = initial_dict.get("hashtags")
        self.sentiment = initial_dict.get("sentiment")
        self.is_event = initial_dict.get("is_event")
        self.is_video = initial_dict.get("is_video")


class TwitterAPIManager:
    def __init__(self, accountType: TwitterAPIManagerAccountType):
        self.api = self.create_api(accountType)
        self.openaiApiManager = OpenaiGptApiManager(
            OpenaiModelVersion.GPT3_5.value)
        self.youtubeDownloader = YoutubeDownloader()

    def create_api(self, accountType: TwitterAPIManagerAccountType):
        if accountType == TwitterAPIManagerAccountType.TwitterAPIManagerAccountTypeCrypto:
            consumer_key = os.getenv("TWITTER_CRYPTO_ACCOUNT_CONSUMER_API_KEY")
            consumer_secret = os.getenv(
                "TWITTER_CRYPTO_ACCOUNT_CONSUMER_API_SECRET")
            access_token = os.getenv("TWITTER_CRYPTO_ACCOUNT_ACCESS_TOKEN")
            access_token_secret = os.getenv(
                "TWITTER_CRYPTO_ACCOUNT_ACCESS_SECRET")

        elif accountType == TwitterAPIManagerAccountType.TwitterAPIManagerAccountTypeFintech:
            consumer_key = os.getenv(
                "TWITTER_FINTECH_ACCOUNT_CONSUMER_API_KEY")
            consumer_secret = os.getenv(
                "TWITTER_FINTECH_ACCOUNT_CONSUMER_API_SECRET")
            access_token = os.getenv("TWITTER_FINTECH_ACCOUNT_ACCESS_TOKEN")
            access_token_secret = os.getenv(
                "TWITTER_FINTECH_ACCOUNT_ACCESS_SECRET")
        else:
            raise Exception("Invalid account type")
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth, wait_on_rate_limit=True)
        try:
            api.verify_credentials()
        except Exception as e:
            error("Error creating API" + str(e))
            raise e
        info("Twitter API created")
        return api

    def get_recent_posted_tweets(self, retry=False) -> List:
        try:
            recent_posted_tweets = []
            for tweet in tweepy.Cursor(self.api.user_timeline).items():
                try:
                    second_since_created = int(
                        time.time() - tweet.created_at.timestamp())
                    if second_since_created > TWEET_THREAD_COVERAGE_SEC:
                        continue
                    recent_posted_tweets.append([tweet.text, tweet.id])
                except Exception as e:
                    error("Error getting posted tweet: " + str(e))
                    continue
            return recent_posted_tweets
        except Exception as e:
            if retry:
                error("Error getting posted tweets: " + str(e))
                return []
            else:
                time.sleep(10)
                return self.get_recent_posted_tweets(retry=True)

    def get_most_similar_posted_tweet_id_and_similarity_score(self, content, recent_posted_tweets=None):
        if not recent_posted_tweets:
            recent_posted_tweets = self.get_recent_posted_tweets()
        most_similar_posted_tweet_id = None
        most_similar_posted_tweet_similarity_score = 0
        for recent_posted_tweet in recent_posted_tweets:
            recent_posted_tweet_content = recent_posted_tweet[0].replace(
                '\n', ' ')
            similarity = TextEmbeddingCache.get_instance().get_text_similarity_score(
                content, recent_posted_tweet_content)
            # similarity = OpenaiClipFeatureGenerator.get_instance().get_similarity_score(
            #     content, recent_posted_tweet_content)
            if similarity > most_similar_posted_tweet_similarity_score:
                most_similar_posted_tweet_similarity_score = similarity
                most_similar_posted_tweet_id = recent_posted_tweet[1]
        return most_similar_posted_tweet_id, most_similar_posted_tweet_similarity_score

    def compose_tweet(self, content: str, hashtags: str or List[str]):
        tweet_content = content
        hashtag_list = []
        if type(hashtags) == list:
            hashtag_list = hashtags
        elif type(hashtags) == str:
            hashtag_list = hashtags.split(',')
        clean_hashtags = []
        for h in hashtag_list:
            tag = h.strip().replace('-', '').replace('.', '')
            if not tag.startswith('#'):
                clean_hashtags.append(f"#{tag}")
            else:
                clean_hashtags.append(tag)

        # Compose hashtags
        hashtags_string = ''
        while len(clean_hashtags) > 0:
            tag = clean_hashtags.pop()
            if not tag or len(tag) <= 2:
                continue
            # if len(tag) + len(hashtags_string) + len(tweet_content) + len(shorten_url_to_use) > TWEET_LENGTH_CHAR_LIMIT - 5:
            #     continue
            if tweet_content.find(tag) != -1:
                continue
            hashtags_string = f'{hashtags_string} {tag}'.strip()

        # Compose tweet content
        if hashtags_string:
            tweet_content = f'{tweet_content}\n\n{hashtags_string}'

        # if shorten_url_to_use:
        #     tweet_content = f'{tweet_content}\n\n{shorten_url_to_use}'
        return tweet_content

    def upload_video(self, video_path: str, retry=0):
        try:
            info(f"Uploading video {video_path}")
            media = self.api.media_upload(
                video_path, media_category='tweet_video')
            info(f"Video uploaded {video_path}")
            return media.media_id_string
        except Exception as e:
            if retry > 2:
                error("Error uploading video" + str(e))
                return None
            else:
                time.sleep(5)
                return self.upload_video(video_path, retry=retry+1)

    def post_tweets(self, tweets: List[TwitterPostCandidate], post_limit: int = TWEET_DEFAULT_POST_LIMIT):
        if len(tweets) == 0:
            return
        post_count = 0
        composed_tweets = []
        recent_posted_tweets = self.get_recent_posted_tweets()
        if len(recent_posted_tweets) == 0:
            warn('No recent posted tweets found')
        for t in tweets:
            composed_tweet = self.compose_tweet(t.news_content, t.hashtags)
            similar_id, similar_score = self.get_most_similar_posted_tweet_id_and_similarity_score(
                t.news_content, recent_posted_tweets)
            composed_tweets.append(
                (composed_tweet, t.is_video, t.news_url, similar_id, similar_score))

        for (tweet_content, is_video, news_url, most_similar_id, most_similar_score) in composed_tweets:
            try:
                if not is_video and most_similar_score > TWEET_SIMILARITY_FOR_POSTING_GUARD_THRESHOLD:
                    warn(
                        f'Tweet is too similar to a recently posted tweet, similarity: {most_similar_score}. recent_posted_tweet_id: {most_similar_id}')
                    continue
                elif is_video:
                    # only support Youtube video for now
                    if news_url.find('youtube.com') == -1:
                        warn(
                            f'Video is not from Youtube, not posting: {news_url}, {tweet_content}')
                        continue
                    try:
                        video_id = news_url.split('v=')[1]
                        video_path = self.youtubeDownloader.download(
                            news_url, f'{video_id}.mp4')
                        trimmed_video_path = trim_video(
                            video_path, 1, TWEET_VIDEO_DURATION_LIMIT_IN_SECOND_DEFAULT)
                        info(
                            f'Trimmed video: {video_path} to {trimmed_video_path}')
                        media_id = self.upload_video(trimmed_video_path)
                        info(f'Uploaded video: {media_id}')
                        if media_id:
                            self.api.update_status(
                                status=tweet_content, media_ids=[media_id])
                            info(f'Tweet posted with video: {tweet_content}')
                            post_count += 1
                            # remove video file
                            try:
                                if os.path.exists(trimmed_video_path):
                                    os.remove(trimmed_video_path)
                                    info(
                                        f'Removed video file: {trimmed_video_path}')
                                if os.path.exists(video_path):
                                    os.remove(video_path)
                                    info(f'Removed video file: {video_path}')
                            except Exception as e:
                                error(
                                    f'Error removing video files: {trimmed_video_path}, {video_path}')
                        else:
                            error(f'Video upload failed: {news_url}')
                    except Exception as e:
                        error('Error posting video tweet: ' + str(e))
                        continue
                elif most_similar_score > TWEET_SIMILARITY_FOR_REPLY:
                    tweet_content = f'{tweet_content}\n\n{news_url}'
                    self.api.update_status(
                        tweet_content, in_reply_to_status_id=most_similar_id)
                    info(
                        f'Tweet posted with reply id ({most_similar_score}): {most_similar_id} - {tweet_content}')
                    post_count += 1
                else:
                    tweet_content = f'{tweet_content}\n\n{news_url}'
                    self.api.update_status(tweet_content)
                    info(f'Tweet posted: {tweet_content}')
                    post_count += 1
            except Exception as e:
                error("Error posting tweet: " + str(e))
                continue
            if post_count >= post_limit:
                break
        info(f'Posted {post_count} tweets')
        return post_count

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
            # similarity = OpenaiClipFeatureGenerator().get_instance().get_similarity_score(
            #     summary_text, recent_posted_tweet)
            if similarity > TWEET_SIMILARITY_FOR_POSTING_GUARD_THRESHOLD:
                warn(
                    f'Tweet is too similar to a recently posted tweet, similarity: {similarity}. recent_posted_tweet: {recent_posted_tweet}, summary_text: {summary_text}')
                return False
        pending_tweets_to_post = [tweet[0]
                                  for tweet in pending_tweets_to_post_with_reply_id]
        for pending_tweet in pending_tweets_to_post:
            similarity = TextEmbeddingCache.get_instance().get_text_similarity_score(
                summary_text, pending_tweet)
            # similarity = OpenaiClipFeatureGenerator().get_instance().get_similarity_score(
            #     summary_text, pending_tweet)
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
            # similarity = OpenaiClipFeatureGenerator().get_instance().get_similarity_score(
            #     text, recent_posted_tweet)
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
        text_reply_id_for_pending_tweets = []
        hashtags_for_pending_tweets = []
        urls_for_pending_tweets = []
        topic_for_pending_tweets = []
        recent_posted_tweets_with_id = self.get_recent_posted_tweets()
        info(f"Found {len(recent_posted_tweets_with_id)} recent posted tweets")
        source_tweet_url_for_pending_tweets = set()
        with open(enriched_summary_file_path, 'r') as f:
            for l in f.readlines():
                data = json.loads(l)
                source_tweet_url = data['tweet_url']
                if source_tweet_url in source_tweet_url_for_pending_tweets:
                    continue
                summary_text = data['summary']
                if not self.should_post(data, recent_posted_tweets_with_id, text_reply_id_for_pending_tweets):
                    continue
                tweet_content = f"{summary_text}".strip()
                if len(data['video_urls']) > 0:
                    urls_for_pending_tweets.append(data['video_urls'])
                else:
                    urls = []
                    if len(data['image_urls']) > 0:
                        urls = data['image_urls']
                    if len(data['external_urls']) > 0:
                        try:
                            url = data['external_urls'][0]
                            short_url = self.shorten_url(url)
                            urls.append(short_url)
                        except Exception as e:
                            error(f"Error shortening url {url}: {e}")
                    urls_for_pending_tweets.append(urls)
                try:
                    topic = ""
                    tweet_topic = data['topic']
                    if tweet_topic == 'technology news' or tweet_topic == 'artificial intelligence' or tweet_topic == 'technology announcement':
                        topic = 'Technology'
                    elif tweet_topic == 'financial news' or tweet_topic == 'stock market':
                        topic = "Finance"
                    elif tweet_topic == 'fiscal policy' or tweet_topic == 'monetory policy' or tweet_topic == 'federal reserve':
                        topic = 'Policy'
                    elif tweet_topic == 'celebrity scandal' or tweet_topic == 'celebrity affair' or tweet_topic == 'breaking news':
                        topic = 'BREAKING NEWS'
                    else:
                        warn(f"Unknown topic {tweet_topic}")
                except Exception as e:
                    error(f"Error getting topic {e}")
                    topic = ""
                topic_for_pending_tweets.append(topic)
                recent_posts_similarity = self.get_most_similar_score_text_id(
                    summary_text, recent_posted_tweets_with_id)
                reply_id = None
                if (recent_posts_similarity):
                    reply_candidate = max(recent_posts_similarity)
                    similar_score = reply_candidate[0]
                    reply_id = reply_candidate[2]
                    similar_recent_posted_tweet = reply_candidate[1]
                    info(
                        f"Found similar tweet for thread, score: {similar_score}, similar_recent_posted_tweet: {similar_recent_posted_tweet}, reply_id: {reply_id}")
                text_reply_id_for_pending_tweets.append(
                    [tweet_content, reply_id])
                source_tweet_url_for_pending_tweets.add(source_tweet_url)
                if len(text_reply_id_for_pending_tweets) >= candidate_limit:
                    break
        hashtags_for_pending_tweets = self.openaiApiManager.generate_hashtags(
            [t[0] for t in text_reply_id_for_pending_tweets])
        if len(text_reply_id_for_pending_tweets) != len(hashtags_for_pending_tweets):
            hashtags_for_pending_tweets = []
            warn(
                f"Hashtags length mismatch: text_reply_id_for_pending_tweets: {len(text_reply_id_for_pending_tweets)}, hashtags_for_pending_tweets: {len(hashtags_for_pending_tweets)}")
            for i in range(len(text_reply_id_for_pending_tweets)):
                tweet_text = text_reply_id_for_pending_tweets[i][0]
                hashtags_for_pending_tweet = self.openaiApiManager.generate_hashtags_for_single_tweet(
                    tweet_text)
                hashtags_for_pending_tweets.append(hashtags_for_pending_tweet)
        if len(text_reply_id_for_pending_tweets) != len(urls_for_pending_tweets) or len(text_reply_id_for_pending_tweets) != len(hashtags_for_pending_tweets or len(text_reply_id_for_pending_tweets) != len(topic_for_pending_tweets)):
            error(
                f"Pending tweets length mismatch: text_reply_id_for_pending_tweets: {len(text_reply_id_for_pending_tweets)}, urls_for_pending_tweets: {len(urls_for_pending_tweets)}, hashtags_for_pending_tweets: {len(hashtags_for_pending_tweets)}, topic_for_pending_tweets: {len(topic_for_pending_tweets)}")
            return
        self._assamble_and_post_tweets(text_reply_id_for_pending_tweets,
                                       urls_for_pending_tweets, hashtags_for_pending_tweets, topic_for_pending_tweets, post_limit)

    def _assamble_and_post_tweets(self, text_reply_id_list, url_group_list, hashtag_list, topic_list, limit):
        text_reply_id_for_pending_tweets = text_reply_id_list
        urls_for_pending_tweets = url_group_list
        hashtags_for_pending_tweets = hashtag_list
        topics_for_pending_tweets = topic_list
        post_limit = min(limit, len(text_reply_id_for_pending_tweets))
        info(f"{len(text_reply_id_for_pending_tweets)} candidate tweets to post")
        tweet_count = 0
        while len(text_reply_id_for_pending_tweets) > 0 and tweet_count < post_limit:
            text_reply_id = text_reply_id_for_pending_tweets.pop(
                0)
            tweet_content = text_reply_id[0]
            topic = topics_for_pending_tweets.pop(0)
            if len(topic) > 0:
                tweet_content = f"[{topic}] {tweet_content}".strip()
            reply_id = text_reply_id[1]
            url_list = urls_for_pending_tweets.pop(0)
            hashtags = sorted(hashtags_for_pending_tweets.pop(
                0).split(' '), key=lambda x: len(x))[:3]
            if len(hashtags) > 0:
                hashtags_string = ''
                while len(hashtags_string) < 25 and len(hashtags) > 0:
                    clean_hashtag = hashtags.pop(0)
                    clean_hashtag = clean_hashtag.replace('-', '')
                    clean_hashtag = clean_hashtag.replace('.', '')
                    hashtags_string = f"{hashtags_string} {clean_hashtag}".strip(
                    )
                tweet_content = f"{tweet_content}\n\n{hashtags_string}".strip()
            if len(url_list) > 0:
                tweet_content = f"{tweet_content}\n{url_list[0]}".strip()
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
                time.sleep(60)
                tweet_count += 1
            except Exception as e:
                error(f"Error posting tweet: {e}")
                continue
            time.sleep(5)
        info(
            f"Posted {tweet_count} tweets successfully.")
        if (tweet_count == 0):
            error("No tweets posted, retrying in 60 seconds...")
            time.sleep(60)
            return self._assamble_and_post_tweets(text_reply_id_list, url_group_list, hashtag_list, limit)

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

    def get_timeline_contents(self, user_id, include_retweets=False, exclude_replies=True, limit=None):
        timeline_contents = []
        for tweet in self.api.user_timeline(user_id=user_id, count=200, include_rts=include_retweets, exclude_replies=exclude_replies):
            clean_text = get_clean_text(tweet.text)
            if clean_text is not None and len(clean_text) > 0:
                timeline_contents.append(clean_text)
            if limit and len(timeline_contents) >= limit:
                break
        return timeline_contents

    def generate_product_recommendation_for_user(self, user_id):
        tweets = self.get_timeline_contents(user_id)
        info(
            f"Getting product recommendations for user {user_id}, tweet count: {len(tweets)}")
        products = self.openaiApiManager.product_recommend_based_on_user_like_contents(
            tweets)
        return products


if __name__ == "__main__":
    api_manager = TwitterAPIManager(
        TwitterAPIManagerAccountType.TwitterAPIManagerAccountTypeCrypto)
    cryptoNewsAPIManager = NewsAPIManager(NewsAPIType.NewsAPITypeCrypto)
    langChainAPIManager = LangChainAPIManager()
    video_news_list = cryptoNewsAPIManager.get_general_news(True)
    video_news = video_news_list[:5]
    candidates = []
    for n in video_news:
        tweet_dict = langChainAPIManager.generate_tweet_dict(
            title=n.news_title, abstract=n.news_text, topics=n.topics, source=n.source_name)
        content = tweet_dict['tweet_content']
        candidate = TwitterPostCandidate({
            'news_content': content,
            "news_url": n.news_url,
            "media_url": n.image_url,
            "hashtags": tweet_dict['hashtags'],
            "sentiment": n.sentiment,
            "is_event": n.event_id is not None,
            "is_video": n.type == GeneralNewsType.Video.value,
        })
        candidates.append(candidate)
    api_manager.post_tweets(candidates)
    # downloader = YoutubeDownloader()
    # downloader.download(
    #     "https://www.youtube.com/watch?v=MkBZIfSyeD0", "1min.mp4", small_size=True)
    # upload_result = api_manager.get_api().media_upload(
    #     '/Users/chengjiang/Dev/NewsBite/data/videos/trimmed_1min.mp4', media_category='tweet_video')
    # print(upload_result)
    # api_manager.get_api().update_status(
    #     status="test video", media_ids=['1678538254247927809'])
    # trimmed_video_path = trim_video(
    #     '/Users/chengjiang/Dev/NewsBite/data/videos/1min.mp4', 0, 45)

    # recent_posted_tweets_with_id = api_manager.get_recent_posted_tweets()
    # print(recent_posted_tweets_with_id)
    # api_manager.get_api().update_status_with_media(
    #     status='test', filename='/Users/chengjiang/Dev/NewsBite/data/videos/test1.mp4')
    # info(api_manager.get_api().user_timeline(user_id='Forbes'))
    # api_manager.upload_summary_items(
    #     '/Users/chengjiang/Dev/NewsBite/data/tweet_summaries/technology_finance/20230601/summary_18_enriched')
    # recent_posted_tweets_with_id = api_manager.get_recent_posted_tweets()
    # similar_score_text_id = api_manager.get_most_similar_score_text_id(
    #     'US government striving to prevent default on national debt after budget breakthrough', recent_posted_tweets_with_id)
    # info(similar_score_text_id.sort(key=lambda x: x[0], reverse=True))
    # api_manager.react_to_quality_tweets_from_file(
    #     '/Users/chengjiang/Dev/NewsBite/src/scripts/../../data/tweet_summaries/finance/20230523/summary_24_enriched')
    # for timeline_item in api_manager.get_api().user_timeline(count=500):
    #     second_since_created = int(
    #         time.time() - timeline_item.created_at.timestamp())
    #     info(f"created_at:{timeline_item.created_at}, second_since_created:{second_since_created} {timeline_item.id}, {timeline_item.in_reply_to_status_id}, {timeline_item.favorite_count}, {timeline_item.retweet_count}")
    # api_manager.untweet_and_unlike_expired_replies()
    # metadata = api_manager.get_api().get_user(user_id=187756121)
    # info(metadata)
    # openaiApiManager = OpenaiGptApiManager(
    #     OpenaiModelVersion.GPT3_5.value)
    # all_twitter_user_id_url = []
    # with open('/Users/chengjiang/Dev/NewsBite/data/influencers/english_20230527', 'r') as f:
    #     for line in f.readlines():
    #         json_data = json.loads(line)
    #         id = json_data['id']
    #         url = json_data['user_url']
    #         all_twitter_user_id_url.append((id, url))
    #         if len(all_twitter_user_id_url) == 10:
    #             break
    # for (id, url) in all_twitter_user_id_url:
    #     products = api_manager.generate_product_recommendation_for_user(id)
    #     info(f"{products} for user {url}")
    # products = api_manager.generate_product_recommendation_for_user(
    #     '1205226529455632385')
    # info(f"{products}")
