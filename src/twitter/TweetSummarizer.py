import json
import os
from datetime import datetime, timedelta
from openAI.OpenaiGptApiManager import OpenaiGptApiManager
from utils.Utilities import get_date, RAW_TWEET_FILE_PREFIX, MIN_RAW_TWEET_LENGTH_FOR_EMBEDDING, SUM_TWEET_FILE_PREFIX, get_clean_text, OpenaiModelVersion, TwitterTopic, TwitterTopicMatchScoreSeed, clean_summary
from utils.Logging import info, error
from twitter.TweetSummaryEnricher import TweetSummaryEnricher
import numpy as np


class TweetSummarizer:

    def __init__(self, master_folder, topic: TwitterTopic):
        self.master_folder = master_folder
        self.topic = topic
        if topic == TwitterTopic.FINANCE.value:
            self.topic_match_score_seed = TwitterTopicMatchScoreSeed.FINANCE.value
        elif topic == TwitterTopic.TECHNOLOGY.value:
            self.topic_match_score_seed = TwitterTopicMatchScoreSeed.TECHNOLOGY.value
        elif topic == TwitterTopic.CRYPTO_CURRENCY.value:
            self.topic_match_score_seed = TwitterTopicMatchScoreSeed.CRYPTO_CURRENCY.value
        else:
            assert False, f"unsupported topic {topic}"
        self.running = False
        self.openaiApiManager = OpenaiGptApiManager(
            OpenaiModelVersion.GPT3_5.value)

    def summarize_hourly_tweets_if_necessary(self, back_fill: bool = False):
        date = get_date(datetime.now()-timedelta(hours=1))
        file_paths = self._get_houly_raw_files_to_process_for_date(
            date, back_fill)
        info(f'summarize_hourly_tweets_if_necessary file_paths={file_paths}')
        if (len(file_paths) > 0):
            info(
                f'tweet processor started ({self.topic}). file_paths={file_paths} backfill={back_fill}')
            self._process_hourly_raw_files(file_paths)

    def summarize_intra_day_tweets(self, hourly_summary_file_paths, output_file_path):
        info(
            f"start generating intra day {self.topic} tweet summary from {hourly_summary_file_paths}")
        if os.path.exists(output_file_path):
            info(f"{output_file_path} already exists, skip")
            return
        single_summary_text_list = []
        for hourly_summary_file_path in hourly_summary_file_paths:
            if not os.path.exists(hourly_summary_file_path):
                info(f"{hourly_summary_file_path} doesn't exist, skip")
                continue
            lines = open(hourly_summary_file_path, 'r').readlines()
            for line in lines:
                if not line:
                    continue
                try:
                    summary_json = json.loads(line)
                    if not summary_json:
                        continue
                    summary_text = summary_json['text'].strip()
                    for summary in summary_text.split('\n'):
                        single_summary_text_list.append(summary)
                except json.decoder.JSONDecodeError:
                    info(f"json.decoder.JSONDecodeError: {line}")
                except TypeError:
                    info(f"TypeError: {line}")

        info(f"start generating daily summary for {self.topic}")
        aggregated_summary_item_list = self.openaiApiManager.merge_summary_items(
            single_summary_text_list, self.topic)
        if not os.path.exists(os.path.dirname(output_file_path)):
            os.makedirs(os.path.dirname(output_file_path))
        with open(output_file_path, 'a') as f:
            for summary_item in aggregated_summary_item_list:
                clean_summary_item = clean_summary(summary_item)
                f.write(clean_summary_item)
                f.write('\n')
        info(
            f"{self.topic} intra day summary has been writen to {output_file_path}")

    def enrich_tweet_summary(self, raw_tweet_file_paths, summary_file_path, output_file_path):
        info(
            f"start enriching intraday day {self.topic} tweet summary from {raw_tweet_file_paths} for {summary_file_path}")
        text_to_tweet = {}
        summary_list = []

        if not os.path.exists(summary_file_path):
            info(f"{summary_file_path} doesn't exist, skip")
            return
        if os.path.exists(output_file_path):
            info(f"{output_file_path} already exists, skip")
            return
        for line in open(summary_file_path).readlines():
            individual_summary = line.strip()
            if len(individual_summary) == 0:
                continue
            summary_list.append(individual_summary)

        for raw_tweet_file_path in raw_tweet_file_paths:
            if not os.path.exists(raw_tweet_file_path):
                info(f"{raw_tweet_file_path} doesn't exist, skip")
                continue
            for line in open(raw_tweet_file_path).readlines():
                json_data = json.loads(line)
                clean_text = get_clean_text(json_data["tweet"]['text'])
                if len(clean_text) < MIN_RAW_TWEET_LENGTH_FOR_EMBEDDING:
                    info(f'{clean_text} is ignored')
                    continue
                external_urls = []
                video_urls = []
                image_urls = []
                try:
                    urls = json_data['tweet']['entities']['urls']
                except KeyError:
                    urls = []
                for url in urls:
                    try:
                        if 'unwound_url' in url:
                            external_urls.append(url['unwound_url'])
                        elif 'media_key' in url:
                            expanded_url = url['expanded_url']
                            if '/video/' in expanded_url:
                                video_urls.append(expanded_url)
                            elif '/photo/' in expanded_url:
                                image_urls.append(expanded_url)
                    except KeyError:
                        pass
                try:
                    hash_tags = [t['tag']
                                 for t in json_data['tweet']['entities']['hashtags']]
                except KeyError:
                    hash_tags = []
                try:
                    author_follower_count = json_data['authorMetadata']['public_metrics']['followers_count']
                except KeyError:
                    author_follower_count = 0
                try:
                    attachments = json_data['tweet']['attachments']
                except KeyError:
                    attachments = {}
                try:
                    source_url = f"https://twitter.com/{json_data['authorMetadata']['username']}/status/{json_data['tweet']['id']}"
                    text_to_tweet[clean_text] = {
                        "external_urls": external_urls,
                        "video_urls": video_urls,
                        "image_urls": image_urls,
                        'tweet_url': source_url,
                        'author_follower_count': author_follower_count,
                        'hash_tags': hash_tags,
                        'created_at': json_data['tweet']['created_at'],
                        'attachments': attachments
                    }
                except KeyError:
                    error(f"KeyError: {line}")
                    continue
                except TypeError:
                    error(f"TypeError: {line}")
                    continue
                except Exception as e:
                    error(f"Error occurred: {e}. {line}")
                    continue

        info(f"start initializing TweetSummaryEnricher...")
        tagger = TweetSummaryEnricher(list(text_to_tweet.keys()))
        info(f"start enriching {len(summary_list)} summaries")
        enriched_summary_list = []
        for individual_summary in summary_list:
            info(f"enriching {individual_summary}")
            source_text, match_score = tagger.find_best_match_and_score(
                individual_summary)
            tweet_url = text_to_tweet[source_text]['tweet_url']
            topic_relavance_score = tagger.get_similarity(
                self.topic_match_score_seed, individual_summary)
            enriched_summary = {
                "summary": individual_summary,
                "match_score": match_score,
                "source_text": source_text,
                "topic_relavance_score": topic_relavance_score,
                "tweet_url": tweet_url,
                "external_urls": text_to_tweet[source_text]['external_urls'],
                "video_urls": text_to_tweet[source_text]['video_urls'],
                "image_urls": text_to_tweet[source_text]['image_urls'],
                "author_follower_count": text_to_tweet[source_text]['author_follower_count'],
                "hash_tags": text_to_tweet[source_text]['hash_tags'],
                "created_at": text_to_tweet[source_text]['created_at'],
            }
            enriched_summary_list.append(enriched_summary)
            info(
                f'{individual_summary}\n  {tweet_url}\n  {source_text}')
        enriched_summary_list = sorted(
            enriched_summary_list, key=lambda x: (-len(x['video_urls']), -len(x['video_urls']), -x['topic_relavance_score']))
        with open(output_file_path, 'a') as f:
            for enriched_summary in enriched_summary_list:
                f.write(json.dumps(enriched_summary))
                f.write('\n')
        info(
            f"{len(summary_list)} enriched summaries written to {output_file_path}")

    def _get_houly_raw_files_to_process_for_date(self, date, back_fill=False):
        hour_ago = datetime.now() - timedelta(hours=1)
        daily_data_folder = os.path.join(self.master_folder, self.topic, date)
        if not os.path.exists(daily_data_folder):
            info(f"{daily_data_folder} doesn't exist, skip")
            return []
        files_to_process = []
        for file_name in os.listdir(daily_data_folder):
            if file_name.startswith(RAW_TWEET_FILE_PREFIX):
                hour_tag = file_name.split(RAW_TWEET_FILE_PREFIX)[-1]
                if int(hour_tag) == hour_ago.hour or back_fill:
                    files_to_process.append(
                        os.path.join(daily_data_folder, file_name))
        return sorted(files_to_process)

    def _process_hourly_raw_files(self, file_paths):
        for file_path in file_paths:
            info(f'start processing hourly raw data: {file_path}')
            raw_tweets = open(file_path, 'r').readlines()
            dir_path = os.path.dirname(file_path)
            clean_tweets = []
            for raw in raw_tweets:
                raw_json = json.loads(raw)
                author_name = raw_json['authorMetadata']['name']
                followers_count = raw_json['authorMetadata']['public_metrics']['followers_count']
                text = raw_json['tweet']['text']
                clean_tweet_text = get_clean_text(text)
                clean_tweets.append(
                    f"({author_name}) ({followers_count}) {clean_tweet_text}")
            file_index = file_path.split(RAW_TWEET_FILE_PREFIX)[-1]
            summary_file_path = os.path.join(
                dir_path, f"{SUM_TWEET_FILE_PREFIX}{file_index}")
            if os.path.exists(summary_file_path):
                info(f"{summary_file_path} exists. Return.")
                continue
            summarize_responses = self.openaiApiManager.summarize_tweets(
                clean_tweets, self.topic)
            if len(summarize_responses) == 0:
                info(f"summarize_responses is empty. Return.")
            else:
                with open(summary_file_path, 'w') as f:
                    for summarize_response in summarize_responses:
                        f.write(json.dumps(summarize_response))
                        f.write('\n')
                info(f'summarizing finished. {summary_file_path} created.')
