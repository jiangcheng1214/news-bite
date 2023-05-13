
import sys
import json
import os
from utils.Logging import info, error
from openAI.OpenaiGptApiManager import OpenaiGpt35ApiManager, OpenaiGpt4ApiManager

from utils.Utilities import SUM_TWEET_FILE_PREFIX, TwitterTopic, DAILY_SUM_TWEET_FILE_NAME, get_yesterday_date

"""
This script is used to aggregate HOURLY tweet summary and generate DAILY tweet summary.
usage: python daily_summary.py
"""

explicit_date_from_user = sys.argv[1] if len(sys.argv) > 1 else None
if explicit_date_from_user:
    if len(explicit_date_from_user) != 8:
        error(f"explicit_date_from_user must be in format of 'YYYYMMDD'")
        sys.exit(1)
    SUMMRAY_DATE = explicit_date_from_user
else:
    SUMMRAY_DATE = get_yesterday_date()

info(f"start generating daily tweet summary for {SUMMRAY_DATE}")

summary_folder_by_topic = {topic.value: (os.path.join(os.path.dirname(
    __file__),  '..', '..', 'data', 'tweets', topic.value, SUMMRAY_DATE))
    for topic in TwitterTopic}

openai_api_manager = OpenaiGpt35ApiManager()

for topic in summary_folder_by_topic.keys():
    dir_path = summary_folder_by_topic[topic]
    if not os.path.exists(dir_path):
        info(f"{dir_path} doesn't exist, skip")
        continue
    hourly_summary_text_list = []
    for hourly_summary_file_name in os.listdir(dir_path):
        if hourly_summary_file_name.startswith(SUM_TWEET_FILE_PREFIX):
            lines = open(os.path.join(
                dir_path, hourly_summary_file_name), 'r').readlines()
            for line in lines:
                if not line:
                    continue
                try:
                    summary_json = json.loads(line)
                    if not summary_json:
                        continue
                    hourly_summary_text_list.append(summary_json['text'])
                except json.decoder.JSONDecodeError:
                    info(f"json.decoder.JSONDecodeError: {line}")
                except TypeError:
                    info(f"TypeError: {line}")
    daily_summary_file_path = os.path.join(dir_path, DAILY_SUM_TWEET_FILE_NAME)
    if os.path.exists(daily_summary_file_path):
        info(f"{daily_summary_file_path} already exists, skip")
        continue
    info(f"start generating daily summary for {topic}")
    i = 1
    for summary_response in openai_api_manager.hourly_tweet_summary_generator(
            hourly_summary_text_list, topic):
        with open(daily_summary_file_path, 'a') as f:
            f.write(json.dumps(summary_response))
            f.write('\n')
        info(f"{SUMMRAY_DATE} {topic} daily summary has been writen to {daily_summary_file_path}. batch: {i}")
        i += 1
