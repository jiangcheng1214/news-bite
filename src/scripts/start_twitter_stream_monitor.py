from datetime import datetime
import json
import os
import re
from dotenv import load_dotenv
from utils.Logging import info
from utils.BufferedFileWriter import BufferedFileWriter
from twitter.twitter_streamer import TwitterFilteredStreamer
from twitter.twitter_user_looker import TwitterUserLooker
from utils.Utilities import TwitterTopic, RAW_TWEET_FILE_PREFIX
from openAI.ai_summarizor import gpt3_5_tweets_summarize
load_dotenv()
key = os.getenv("TWITTER_KEY")

user_looker = TwitterUserLooker(key)
total_received = 0
complete_tweets_received_by_topic = {topic.value: [] for topic in TwitterTopic}
raw_tweets_file_writer_by_topic = {topic.value: BufferedFileWriter(os.path.join(os.path.dirname(
    __file__),  '..', '..', 'data', 'tweets', topic.value), RAW_TWEET_FILE_PREFIX)
    for topic in TwitterTopic}
tweet_count_by_topic = {topic.value: 0 for topic in TwitterTopic}


def callback(tweet, matching_topic):
    global complete_tweets_received_by_topic, tweet_count_by_topic, total_received
    author_metadata = user_looker.lookup_user_metadata(tweet['author_id'])
    complete_tweet_received = {'tweet': tweet,
                               'authorMetadata': author_metadata}
    complete_tweets_received_by_topic[matching_topic].append(
        complete_tweet_received)
    tweet_count_by_topic[matching_topic] += 1
    total_received += 1
    author_name = complete_tweet_received['authorMetadata']['name']
    followers_count = complete_tweet_received['authorMetadata']['public_metrics']['followers_count']
    stats_string = f'New tweet received from {author_name} with {followers_count} followers.'
    for t in TwitterTopic:
        stats_string += f' {t.value}:{tweet_count_by_topic[t.value]}'
    info(stats_string)
    raw_tweets_file_writer_by_topic[matching_topic].append(
        json.dumps(complete_tweet_received))

    # complete_tweets_received_for_current_topic = complete_tweets_received_by_topic[
    #     matching_topic]
    # if len(complete_tweets_received_for_current_topic) % TRUNCK_SIZE == 0:
    #     ts = int(datetime.now().timestamp())
    #     data_folder_path = os.path.join(os.path.dirname(
    #         __file__),  '..', '..', 'data', 'tweets', matching_topic)
    #     if not os.path.exists(data_folder_path):
    #         os.makedirs(data_folder_path)
    #     cleaned_tweet_file_path = os.path.join(
    #         data_folder_path, f'cleaned_{ts}.txt')
    #     cleaned_tweets = []
    #     for complete_record in complete_tweets_received_for_current_topic:
    #         text = complete_record['tweet']['text']
    #         link_free_text = re.sub(r'http\S+', '', text)
    #         author_name = complete_record['authorMetadata']['name']
    #         followers_count = complete_record['authorMetadata']['public_metrics']['followers_count']
    #         clean_tweet = f"({author_name}) ({followers_count}) {link_free_text}".replace(
    #             "\n", " ")
    #         cleaned_tweets.append(clean_tweet)
    #     with open(cleaned_tweet_file_path, 'a') as f:
    #         for cleaned_tweet in cleaned_tweets:
    #             f.write(cleaned_tweet)
    #             f.write('\n')
    #     info(f"clean tweets have been written to {cleaned_tweet_file_path}")
    #     summary_file_path = os.path.join(
    #         data_folder_path, f'summary_{ts}.txt')
    #     summarize_result = gpt3_5_tweets_summarize(
    #         cleaned_tweets, matching_topic)
    #     with open(summary_file_path, 'a') as f:
    #         json.dump(summarize_result, f)
    # info(
    #     f"summary_path: {cleaned_tweet_file_path}, tweet_count:{len(cleaned_tweets)}, total_tokens:{summarize_result['usage']['total_tokens']}")
    # complete_tweets_received_by_topic[matching_topic] = []


fetcher = TwitterFilteredStreamer(key, callback)
fetcher.start_stream()
