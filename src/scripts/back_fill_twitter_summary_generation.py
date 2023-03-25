import os
from utils.Utilities import TwitterTopic
from utils.TimedTweetDataProcessor import TweetDataProcessor
from utils.Logging import info

tweet_processor_by_topic = {topic.value: TweetDataProcessor(os.path.join(os.path.dirname(
    __file__),  '..', '..', 'data', 'tweets'), topic.value)
    for topic in TwitterTopic}

for tweet_processor in tweet_processor_by_topic.values():
    tweet_processor.summarize_tweets_if_necessary(True)
print(f"Back fill tweet summary finished")
