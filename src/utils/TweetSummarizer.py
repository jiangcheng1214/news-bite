import json
import os
from datetime import datetime, timedelta
from openAI.OpenaiGptApiManager import OpenaiGpt35ApiManager, OpenaiGpt4ApiManager
from utils.Utilities import get_date, RAW_TWEET_FILE_PREFIX, MIN_RAW_TWEET_LENGTH_FOR_EMBEDDING, SUM_TWEET_FILE_PREFIX, get_clean_tweet_text, DAILY_SUM_TWEET_FILE_NAME, DAILY_SUM_ENRICHED_TWEET_FILE_NAME
from utils.Logging import info
from utils.TweetSummaryEnricher import TweetSummaryEnricher


class TweetSummarizer:

    def __init__(self, master_folder, topic):
        self.master_folder = master_folder
        self.topic = topic
        self.running = False
        self.openaiApiManager = OpenaiGpt35ApiManager()
        # self.openaiApiManager = OpenaiGpt4ApiManager()

    def summarize_hourly_tweets_if_necessary(self, back_fill: bool = False):
        date = get_date(datetime.now()-timedelta(hours=1))
        file_paths = self._get_houly_raw_files_to_process_for_date(
            date, back_fill)
        info(f'summarize_hourly_tweets_if_necessary file_paths={file_paths}')
        if (len(file_paths) > 0):
            info(
                f'tweet processor started ({self.topic}). file_paths={file_paths} backfill={back_fill}')
            self._process_hourly_raw_files(file_paths)

    def summarize_daily_tweets(self, date):
        info(f"start generating daily {self.topic} tweet summary for {date}")
        summary_folder_path = os.path.join(
            self.master_folder, self.topic, date)
        if not os.path.exists(summary_folder_path):
            info(f"{summary_folder_path} doesn't exist, skip")
            return
        single_summary_text_list = []
        for hourly_summary_file_name in os.listdir(summary_folder_path):
            if hourly_summary_file_name.startswith(SUM_TWEET_FILE_PREFIX):
                lines = open(os.path.join(
                    summary_folder_path, hourly_summary_file_name), 'r').readlines()
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
        daily_summary_file_path = os.path.join(
            summary_folder_path, DAILY_SUM_TWEET_FILE_NAME)
        if os.path.exists(daily_summary_file_path):
            info(f"{daily_summary_file_path} already exists, skip")
            return
        info(f"start generating daily summary for {self.topic}")
        aggregated_summary_item_list = self.openaiApiManager.merge_summary_items(
            single_summary_text_list, self.topic)
        with open(daily_summary_file_path, 'a') as f:
            for summary_item in aggregated_summary_item_list:
                f.write(summary_item)
                f.write('\n')
        info(
            f"{date} {self.topic} daily summary has been writen to {daily_summary_file_path}")

    def enrich_daily_summary(self, date):
        info(f"start enriching daily {self.topic} tweet summary for {date}")
        summary_folder = os.path.join(
            self.master_folder, self.topic, date)
        text_to_tweet = {}
        summary_list = []

        daily_summary_file_path = os.path.join(
            summary_folder, DAILY_SUM_TWEET_FILE_NAME)
        if not os.path.exists(daily_summary_file_path):
            info(f"{daily_summary_file_path} doesn't exist, skip")
            return
        enriched_summary_file_path = os.path.join(
            summary_folder, f"{DAILY_SUM_ENRICHED_TWEET_FILE_NAME}")
        if os.path.exists(enriched_summary_file_path):
            info(f"{enriched_summary_file_path} already exists, skip")
            return
        for line in open(daily_summary_file_path).readlines():
            individual_summary = line.strip()
            if len(individual_summary) == 0:
                continue
            summary_list.append(individual_summary)

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
        enriched_summary_list = []
        for individual_summary in summary_list:
            info(f"enriching {individual_summary}")
            source_text = tagger.find_most_similar_url_uisng_openai_embedding(
                individual_summary)
            tweet_url = text_to_tweet[source_text]['tweet_url']
            unwound_url = text_to_tweet[source_text]['unwound_url']
            enriched_summary = {"summary": individual_summary,  "source_text": source_text,
                                "tweet_url": tweet_url, "unwound_url": unwound_url}
            enriched_summary_list.append(enriched_summary)
            info(
                f'{individual_summary}\n  {tweet_url}\n  {unwound_url}\n  {source_text}')
        with open(enriched_summary_file_path, 'a') as f:
            for enriched_summary in enriched_summary_list:
                f.write(json.dumps(enriched_summary))
                f.write('\n')
        info(
            f"{len(summary_list)} enriched summaries written to {enriched_summary_file_path}")

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
                clean_tweet_text = get_clean_tweet_text(text)
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
