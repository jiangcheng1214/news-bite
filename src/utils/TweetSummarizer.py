import json
import os
from datetime import datetime, timedelta
from openAI.OpenaiGptApiManager import OpenaiGpt35ApiManager, OpenaiGpt4ApiManager
from utils.Utilities import get_date, RAW_TWEET_FILE_PREFIX, CLEAN_TWEET_FILE_PREFIX, SUM_TWEET_FILE_PREFIX, get_clean_tweet_text
from utils.Logging import info


class TweetSummarizer:

    def __init__(self, master_folder, topic):
        self.master_folder = master_folder
        self.topic = topic
        self.running = False
        self.openaiApiManager = OpenaiGpt35ApiManager()
        # self.openaiApiManager = OpenaiGpt4ApiManager()

    def summarize_hourly_tweets_if_necessary(self, back_fill: bool = False):
        date = get_date(datetime.now())
        file_paths = self._get_houly_raw_files_to_process_for_date(
            date, back_fill)
        info(f'summarize_hourly_tweets_if_necessary file_paths={file_paths}')
        if (len(file_paths) > 0):
            info(
                f'tweet processor started ({self.topic}). file_paths={file_paths} backfill={back_fill}')
            self._process_hourly_raw_files(file_paths)

    def _get_houly_raw_files_to_process_for_date(self, date, back_fill=False):
        hour_ago = datetime.now() - timedelta(hours=1)
        daily_data_folder = os.path.join(self.master_folder, self.topic, date)
        if not os.path.exists(daily_data_folder):
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
            info(f'start cleaning {file_path}')
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
            clean_file_path = os.path.join(
                dir_path, f"{CLEAN_TWEET_FILE_PREFIX}{file_index}")
            with open(clean_file_path, 'w') as f:
                for clean_tweet in clean_tweets:
                    f.write(clean_tweet)
                    f.write('\n')
            info(f'clean tweets for summary: {clean_file_path}')
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

            # num_lines = len(clean_tweets)
            # batch_size = 50
            # num_batches = num_lines // batch_size + \
            #     (num_lines % batch_size > 0)  # calculate number of batches

            # info(
            #     f'start summarizing. {num_lines} tweets will be processed with {num_batches} batches of {batch_size} tweets each')
            # for batch_num in range(num_batches):
            #     start_idx = batch_num * batch_size
            #     end_idx = min((batch_num + 1) * batch_size, num_lines)
            #     batch_clean_tweets = clean_tweets[start_idx:end_idx]
            #     process_result = self.openaiApiManager.summarize_tweets(
            #         batch_clean_tweets, self.topic)
            #     with open(summary_file_path, 'a') as f:
            #         f.write(json.dumps(process_result))
            #         f.write('\n')
            #     info(f'batch:{batch_num} summry write to {summary_file_path}')
