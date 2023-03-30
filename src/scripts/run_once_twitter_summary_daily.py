
import json
import os
from utils.Logging import info
from openAI.OpenaiGpt35ApiManager import OpenaiGpt35ApiManager

from utils.Utilities import SUM_TWEET_FILE_PREFIX, TwitterTopic, DAILY_SUM_TWEET_FILE_PREFIX

"""
This script is used to aggregate HOURLY tweet summary and generate DAILY tweet summary.
usage: python daily_summary.py
"""

# e.g '20230326'
SUMMRAY_DATE = '20230328'

assert (len(SUMMRAY_DATE) == 8, "SUMMRAY_DATE must be in format of 'YYYYMMDD'")

summary_folder_by_topic = {topic.value: (os.path.join(os.path.dirname(
    __file__),  '..', '..', 'data', 'tweets', topic.value, SUMMRAY_DATE))
    for topic in TwitterTopic}

openai_gpt35_api_manager = OpenaiGpt35ApiManager()

for topic in summary_folder_by_topic.keys():
    dir_path = summary_folder_by_topic[topic]
    summaries = []
    for file_name in os.listdir(dir_path):
        if file_name.startswith(SUM_TWEET_FILE_PREFIX):
            lines = open(os.path.join(dir_path, file_name), 'r').readlines()
            for line in lines:
                try:
                    summary_json = json.loads(line)
                    summaries.append(summary_json['text'])
                except json.decoder.JSONDecodeError:
                    info(f"json.decoder.JSONDecodeError: {line}")

    responses = openai_gpt35_api_manager.gpt3_5_combine_hourly_summary(
        summaries, topic)
    for i in range(len(responses)):
        daily_summary_file_path = os.path.join(
            dir_path, f'{DAILY_SUM_TWEET_FILE_PREFIX}{i}')
        with open(daily_summary_file_path, 'w') as f:
            f.write(json.dumps(responses[i]))
            f.write('\n')
            info(
                f"{SUMMRAY_DATE} daily summary has been writen to {daily_summary_file_path}")
