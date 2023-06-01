import json
import os
from dotenv import load_dotenv
from twitter.TwitterFilterRulesManager import TwitterFilterRulesManager
from utils.Constants import TWITTER_BEARER_TOKEN_DEV_EVAR_KEY
from utils.Decorators import rabbitmq_decorator
from utils.Logging import info, warn
from utils.BufferedFileWriter import BufferedFileWriter
from twitter.TwitterFilteredStreamer import TwitterFilteredStreamer
from twitter.TwitterUserLooker import TwitterUserLooker
from utils.Utilities import TwitterTopic

"""
This script is used to monitor twitter stream and save tweets to file.
usage: python start_twitter_stream_monitor.py
"""

load_dotenv()
bearer_token = os.getenv(TWITTER_BEARER_TOKEN_DEV_EVAR_KEY)

assert (len(bearer_token) > 0, "Twitter key is not set")

user_looker = TwitterUserLooker(bearer_token)
deteceted_influencers = {}
monitored_topics = [TwitterTopic.INFLUENCERS.value,
                    TwitterTopic.POSSIBLE_PORN_INFLUENCERS.value]
for monitored_topic in monitored_topics:
    if os.path.exists(os.path.join(os.path.dirname(__file__), '..', '..', 'data', monitored_topic)):
        for influencer_data_file in os.listdir(os.path.join(os.path.dirname(__file__), '..', '..', 'data', monitored_topic)):
            if not (influencer_data_file.startswith('english_') or influencer_data_file.startswith('chinese_')):
                continue
            for line in open(os.path.join(os.path.dirname(__file__), '..', '..', 'data', monitored_topic, influencer_data_file)):
                try:
                    influencer_data_json = json.loads(line)
                    deteceted_influencers[influencer_data_json['id']] = 1
                except:
                    continue
info(f'Loaded {len(deteceted_influencers)} influencers from file')
total_received = 0
file_writer_by_lang_by_topic = {
    'chinese': {
        TwitterTopic.INFLUENCERS.value: BufferedFileWriter(os.path.join(os.path.dirname(
            __file__),  '..', '..', 'data', TwitterTopic.INFLUENCERS.value), 'chinese_', daily_only=True)
    },
    'english': {
        TwitterTopic.INFLUENCERS.value: BufferedFileWriter(os.path.join(os.path.dirname(
            __file__),  '..', '..', 'data', TwitterTopic.INFLUENCERS.value), 'english_', daily_only=True),
        TwitterTopic.POSSIBLE_PORN_INFLUENCERS.value: BufferedFileWriter(os.path.join(os.path.dirname(
            __file__),  '..', '..', 'data', TwitterTopic.POSSIBLE_PORN_INFLUENCERS.value), 'english_', daily_only=True)
    }
}

# @rabbitmq_decorator('twitter_raw_data')


def callback(tweet, matching_topic):
    if matching_topic not in monitored_topics:
        warn(
            f'Unexpected topic {matching_topic} received. Expected {monitored_topics}')
        return
    global total_received, deteceted_influencers
    author_id = tweet['author_id']
    if author_id in deteceted_influencers:
        info(f'{matching_topic} Influencer {author_id} already detected.')
        deteceted_influencers[author_id] += 1
        most_active_influencers_and_count = [f"{i[0]} {i[1]}" for i in sorted(
            deteceted_influencers.items(), key=lambda x: x[1], reverse=True)[:5]]
        info(f'Most active influencers: {most_active_influencers_and_count}')
        return
    influencer_metadata = user_looker.lookup_user_metadata(author_id)

    total_received += 1
    author_name = influencer_metadata['name']
    language = tweet['lang']
    user_name = influencer_metadata['username']
    user_url = f'https://twitter.com/{user_name}'
    followers_count = influencer_metadata['public_metrics']['followers_count']
    influencer_metadata['tweet'] = tweet['text']
    influencer_metadata['tweet_url'] = f'https://twitter.com/{user_name}/status/{tweet["id"]}'
    influencer_metadata['user_url'] = user_url
    text = tweet["text"].replace("\n", " ").strip()
    stats_string = f'({total_received}) {matching_topic}: {author_name}({user_url}) with {followers_count} followers. tweet: {text}'
    info(stats_string)
    if language == 'zh-CN' or language == 'zh-TW':
        file_writer_by_lang_by_topic['chinese'][matching_topic].append(
            json.dumps(influencer_metadata))
    elif language == 'en':
        file_writer_by_lang_by_topic['english'][matching_topic].append(
            json.dumps(influencer_metadata))
    else:
        warn(
            f'Unexpected language {language} received. Expected chinese or english')
    deteceted_influencers[author_id] = 1


twitterFilterRulesManager = TwitterFilterRulesManager(
    bearer_token, monitored_topics)
streamer = TwitterFilteredStreamer(
    bearer_token, twitterFilterRulesManager, callback)
streamer.start_stream()
