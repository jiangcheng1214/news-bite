import json
import os
import re
from datetime import datetime, timedelta
from openAI.ai_summarizor import gpt3_5_tweets_summarize
from utils.Utilities import get_date, RAW_TWEET_FILE_PREFIX, CLEAN_TWEET_FILE_PREFIX, SUM_TWEET_FILE_PREFIX
from utils.Logging import info


class TweetDataProcessor:

    def __init__(self, master_folder, topic):
        self.master_folder = master_folder
        self.topic = topic
        self.running = False

    def summarize_tweets_if_necessary(self, back_fill: bool = False):
        date = get_date(datetime.now())
        file_paths = self._get_files_to_process_for_date(date, back_fill)
        if (len(file_paths) > 0):
            info(
                f'tweet processor started ({self.topic}). backfill={back_fill}')
            self._process_files(file_paths)

    def _get_files_to_process_for_date(self, date, back_fill=False):
        hour_ago = datetime.now() - timedelta(hours=1)
        daily_data_folder = os.path.join(self.master_folder, self.topic, date)
        files_to_process = []
        for file_name in os.listdir(daily_data_folder):
            if file_name.startswith(RAW_TWEET_FILE_PREFIX):
                hour_tag = file_name.split(RAW_TWEET_FILE_PREFIX)[-1]
                if int(hour_tag) == hour_ago.hour:
                    files_to_process.append(
                        os.path.join(daily_data_folder, file_name))
                if int(hour_tag) < hour_ago.hour and back_fill:
                    files_to_process.append(
                        os.path.join(daily_data_folder, file_name))
        return files_to_process

    def _process_files(self, file_paths):
        for file_path in file_paths:
            info(f'start cleaning {file_path}')
            raw_tweets = open(file_path, 'r').readlines()
            dir_path = os.path.dirname(file_path)
            clean_tweets = []
            for raw in raw_tweets:
                raw_json = json.loads(raw)
                text = raw_json['tweet']['text']
                link_free_text = re.sub(r'http\S+', '', text)
                author_name = raw_json['authorMetadata']['name']
                followers_count = raw_json['authorMetadata']['public_metrics']['followers_count']
                clean_tweets.append(f"({author_name}) ({followers_count}) {link_free_text}".replace(
                    "\n", " "))
            file_index = file_path.split(RAW_TWEET_FILE_PREFIX)[-1]
            clean_file_path = os.path.join(
                dir_path, f"{CLEAN_TWEET_FILE_PREFIX}{file_index}")
            with open(clean_file_path, 'a') as f:
                for clean_tweet in clean_tweets:
                    f.write(clean_tweet)
                    f.write('\n')
            info(f'clean tweets for summary: {clean_file_path}')
            summary_file_path = os.path.join(
                dir_path, f"{SUM_TWEET_FILE_PREFIX}{file_index}")
            if os.path.exists(summary_file_path):
                info(f"{summary_file_path} exists. Return.")
                return

            num_lines = len(clean_tweets)
            batch_size = 50
            num_batches = num_lines // batch_size + \
                (num_lines % batch_size > 0)  # calculate number of batches

            info(
                f'start summarizing. {num_lines} tweets will be processed with {num_batches} batches of {batch_size} tweets each')
            for batch_num in range(num_batches):
                start_idx = batch_num * batch_size
                end_idx = min((batch_num + 1) * batch_size, num_lines)
                batch_tweets = clean_tweets[start_idx:end_idx]
                process_result = gpt3_5_tweets_summarize(
                    batch_tweets, self.topic)
                with open(summary_file_path, 'a') as f:
                    f.write(json.dumps(process_result))
                    f.write('\n')
                info(f'batch:{batch_num} summry write to {summary_file_path}')
            info(f'summarizing finished')
