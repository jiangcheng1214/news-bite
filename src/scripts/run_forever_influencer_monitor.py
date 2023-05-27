import json
import os
from dotenv import load_dotenv
from twitter.TwitterFilterRulesManager import TwitterFilterRulesManager
from utils.Constants import TWITTER_BEARER_TOKEN_DEV_EVAR_KEY, INFLUENCER_FILE_PREFIX
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
for influencer_data_file in os.listdir(os.path.join(os.path.dirname(__file__), '..', '..', 'data', TwitterTopic.INFLUENCERS.value)):
    for line in open(os.path.join(os.path.dirname(__file__), '..', '..', 'data', TwitterTopic.INFLUENCERS.value, influencer_data_file)):
        influencer_data_json = json.loads(line)
        deteceted_influencers[influencer_data_json['id']] = 1
info(f'Loaded {len(deteceted_influencers)} influencers from file')
total_received = 0
monitored_topic = TwitterTopic.INFLUENCERS.value
raw_tweets_file_writer_by_lang = {
    'chinese': BufferedFileWriter(os.path.join(os.path.dirname(
        __file__),  '..', '..', 'data', monitored_topic), 'chinese_', daily_only=True),
    'english': BufferedFileWriter(os.path.join(os.path.dirname(
        __file__),  '..', '..', 'data', monitored_topic), 'english_', daily_only=True)
}

# @rabbitmq_decorator('twitter_raw_data')


def callback(tweet, matching_topic):
    if matching_topic != monitored_topic:
        warn(
            f'Unexpected topic {matching_topic} received. Expected {monitored_topic}')
        return
    global total_received, deteceted_influencers
    author_id = tweet['author_id']
    
    if author_id in deteceted_influencers:
        text = tweet['text']
        info(f'Influencer {author_id} already detected. tweet:{text} Skipping')
        deteceted_influencers[author_id] += 1
        most_active_influencers_and_count = [f"{i[0]} {i[1]}" for i in sorted(
            deteceted_influencers.items(), key=lambda x: x[1], reverse=True)[:5]]
        info(f'Most active influencers: {most_active_influencers_and_count}')
        return
    influencer_metadata = user_looker.lookup_user_metadata(author_id)

    total_received += 1
    author_name = influencer_metadata['name']
    language = tweet['lang']
    followers_count = influencer_metadata['public_metrics']['followers_count']
    stats_string = f'Influencer detected: {author_name} with {followers_count} followers. Total received: {total_received}'
    info(stats_string)
    if language == 'zh-CN' or language == 'zh-TW':
        raw_tweets_file_writer_by_lang['chinese'].append(
            json.dumps(influencer_metadata))
    elif language == 'en':
        raw_tweets_file_writer_by_lang['english'].append(
            json.dumps(influencer_metadata))
    else:
        warn(
            f'Unexpected language {language} received. Expected chinese or english')
    deteceted_influencers[author_id] = 1


twitterFilterRulesManager = TwitterFilterRulesManager(
    bearer_token, monitored_topic)
streamer = TwitterFilteredStreamer(
    bearer_token, twitterFilterRulesManager, callback)
streamer.start_stream()
