import os
from utils.BufferedRedisWriter import BufferedRedisWriter
from utils.Utilities import RAW_TWEET_FILE_PREFIX

project_root = os.environ.get('NEWS_BITE')

# Define data path
data_path = os.path.join(project_root, 'data')
topic_value = "financial"
date = '20230513'
tweet_data_path = os.path.join(data_path, 'tweets', topic_value, date)

master_key = "tweets" + ":" + topic_value 
raw_buffered_writer = BufferedRedisWriter(master_key,'raw')

for filename in os.listdir(tweet_data_path):
    prefix , hour = filename.split('_')
    raw_buffered_writer.sub_key_prefix = prefix
    raw_buffered_writer.filename_date = date
    raw_buffered_writer.filename_hour = hour
    tweet_filename = os.path.join(tweet_data_path, filename)
    try:
        with open(tweet_filename, 'r') as file:
            for line in file:
                if prefix == 'raw':
                    raw_buffered_writer.append(line)
    except Exception as e:
        print(f"Error reading file {tweet_filename}: {e}")
