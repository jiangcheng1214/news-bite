import os
from utils.Utilities import RAW_TWEET_FILE_PREFIX, DAILY_SUM_TWEET_FILE_PREFIX, DAILY_SUM_ENRICHED_TWEET_FILE_NAME, get_clean_tweet_text, TwitterTopic
from utils.TweetSummaryEnricher import TweetSummaryEnricher
import json
from utils.Logging import info

"""
This script is used to enrich DAILY tweet summary with more information including original tweet, tweet url, source url, etc.
usage: python enrich_twitter_summary.py
"""

# e.g '20230326'
SUMMRAY_DATE = ''

assert (len(SUMMRAY_DATE) == 8, "SUMMRAY_DATE must be in format of 'YYYYMMDD'")

summary_folder_by_topic = {topic.value: (os.path.join(os.path.dirname(
    __file__),  '..', '..', 'data', 'tweets', topic.value, SUMMRAY_DATE))
    for topic in TwitterTopic}

for topic in summary_folder_by_topic.keys():
    summary_folder = summary_folder_by_topic[topic]
    text_to_tweet = {}
    summary_list = []
    for file_name in os.listdir(summary_folder):
        if file_name.startswith(RAW_TWEET_FILE_PREFIX):
            for line in open(os.path.join(summary_folder, file_name)).readlines():
                json_data = json.loads(line)
                clean_text = get_clean_tweet_text(json_data["tweet"]['text'])
                if len(clean_text) < 30:
                    info(f'{clean_text} is ignored')
                    continue
                try:
                    unwound_url = json_data['tweet']['entities']['urls'][0]['unwound_url']
                except KeyError:
                    unwound_url = ""
                source_url = f"https://twitter.com/{json_data['authorMetadata']['username']}/status/{json_data['tweet']['id']}"
                text_to_tweet[clean_text] = {
                    "unwound_url": unwound_url, 'tweet_url': source_url}
        elif file_name.startswith(DAILY_SUM_TWEET_FILE_PREFIX):
            for line in open(os.path.join(summary_folder, file_name)).readlines():
                json_data = json.loads(line)
                for summary in json_data["choices"][0]["message"]["content"].split('\n'):
                    summary_list.append(summary)

    tagger = TweetSummaryEnricher(list(text_to_tweet.keys()))

    info(f"start enriching {len(summary_list)} summaries")
    enriched_summary_list = []
    for summary in summary_list:
        info(f"enriching {summary}")
        source_text = tagger.find_most_similar_url_uisng_openai_embedding(
            summary)
        tweet_url = text_to_tweet[source_text]['tweet_url']
        unwound_url = text_to_tweet[source_text]['unwound_url']
        enriched_summary_list.append(
            {"summary": summary,  "source_text": source_text, "tweet_url": tweet_url, "unwound_url": unwound_url})
        info(f'{summary}\n  {tweet_url}\n  {unwound_url}\n  {source_text}')

    enriched_summary_file_path = os.path.join(
        summary_folder, f"{DAILY_SUM_ENRICHED_TWEET_FILE_NAME}")
    with open(enriched_summary_file_path, 'w') as f:
        for enriched_summary in enriched_summary_list:
            f.write(json.dumps(enriched_summary))
            f.write('\n')
    info(f"{len(enriched_summary_list)} enriched summaries weitten to {enriched_summary_file_path}")
