import os
import sys
from utils.Utilities import RAW_TWEET_FILE_PREFIX, get_yesterday_date, DAILY_SUM_ENRICHED_TWEET_FILE_NAME, get_clean_tweet_text, TwitterTopic, DAILY_SUM_TWEET_FILE_NAME, MIN_RAW_TWEET_LENGTH_FOR_EMBEDDING
from utils.TweetSummaryEnricher import TweetSummaryEnricher
import json
from utils.Logging import info, error

"""
This script is used to enrich DAILY tweet summary with more information including original tweet, tweet url, source url, etc.
usage: python enrich_twitter_summary.py
"""

explicit_date_from_user = sys.argv[1] if len(sys.argv) > 1 else None
if explicit_date_from_user:
    assert (len(explicit_date_from_user) == 8,
            "explicit_date_from_user must be in format of 'YYYYMMDD'")
    SUMMRAY_DATE = explicit_date_from_user
else:
    SUMMRAY_DATE = get_yesterday_date()

info(f"start enriching daily tweet summary for {SUMMRAY_DATE}")

summary_folder_by_topic = {topic.value: (os.path.join(os.path.dirname(
    __file__),  '..', '..', 'data', 'tweets', topic.value, SUMMRAY_DATE))
    for topic in TwitterTopic}

for topic in summary_folder_by_topic.keys():
    summary_folder = summary_folder_by_topic[topic]
    text_to_tweet = {}
    summary_list = []

    daily_summary_file_path = os.path.join(
        summary_folder, DAILY_SUM_TWEET_FILE_NAME)
    if not os.path.exists(daily_summary_file_path):
        info(f"{daily_summary_file_path} doesn't exist, skip")
        continue
    enriched_summary_file_path = os.path.join(
        summary_folder, f"{DAILY_SUM_ENRICHED_TWEET_FILE_NAME}")
    if os.path.exists(enriched_summary_file_path):
        info(f"{enriched_summary_file_path} already exists, skip")
        continue
    for line in open(daily_summary_file_path).readlines():
        daily_summary_data = json.loads(line)
        try:
            for individual_summary in daily_summary_data["text"].split('\n'):
                if len(individual_summary.strip()) == 0:
                    continue
                summary_list.append(individual_summary)
        except KeyError:
            error(f"KeyError {line}")
            continue

    for file_name in os.listdir(summary_folder):
        if not file_name.startswith(RAW_TWEET_FILE_PREFIX):
            continue
        for line in open(os.path.join(summary_folder, file_name)).readlines():
            json_data = json.loads(line)
            clean_text = get_clean_tweet_text(json_data["tweet"]['text'])
            if len(clean_text) < MIN_RAW_TWEET_LENGTH_FOR_EMBEDDING:
                info(f'{clean_text} is ignored')
                continue
            try:
                unwound_url = json_data['tweet']['entities']['urls'][0]['unwound_url']
            except KeyError:
                unwound_url = ""
            source_url = f"https://twitter.com/{json_data['authorMetadata']['username']}/status/{json_data['tweet']['id']}"
            text_to_tweet[clean_text] = {
                "unwound_url": unwound_url, 'tweet_url': source_url}

    info(f"start initializing TweetSummaryEnricher...")
    tagger = TweetSummaryEnricher(list(text_to_tweet.keys()))
    info(f"start enriching {len(summary_list)} summaries")
    for individual_summary in summary_list:
        info(f"enriching {individual_summary}")
        source_text = tagger.find_most_similar_url_uisng_openai_embedding(
            individual_summary)
        tweet_url = text_to_tweet[source_text]['tweet_url']
        unwound_url = text_to_tweet[source_text]['unwound_url']
        enriched_summary = {"summary": individual_summary,  "source_text": source_text,
                            "tweet_url": tweet_url, "unwound_url": unwound_url}
        info(f'{individual_summary}\n  {tweet_url}\n  {unwound_url}\n  {source_text}')
        with open(enriched_summary_file_path, 'a') as f:
            f.write(json.dumps(enriched_summary))
            f.write('\n')
    info(f"{len(summary_list)} enriched summaries weitten to {enriched_summary_file_path}")
