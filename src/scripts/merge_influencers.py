
import json
import os
import re

from twitter.TwitterAPIManager import TwitterAPIManager

porn_keywords = [
    'adult',  'xxx', 'breast', 'porn', 'nude', 'sex', 'nsfw', 'x-rated', 'fetish', 'onlyfans', 'onlyfanz', 'fuck', 'fxck', 'anal', 'fingered', 'pussy', 'dicks', 'dick', 'sugardad', 'sugardaddy', 'sugar daddy', '18+'
]


def is_porn_influencer(api_manager: TwitterAPIManager, influencer_data_json):
    """
    Check if the influencer is a porn influencer.
    """
    description = influencer_data_json['description'] if 'description' in influencer_data_json else ""
    matched = 0
    for porn_keyword in porn_keywords:
        if description.find(porn_keyword) >= 0:
            matched += 1
        if matched >= 1:
            return True
    recent_posted_tweets = api_manager.get_timeline_contents(
        influencer_data_json['id'])
    total_post = len(recent_posted_tweets)
    total_matched = 0
    for tweet in recent_posted_tweets:
        for porn_keyword in porn_keywords:
            if tweet.find(porn_keyword) >= 0:
                total_matched += 1
                continue
    if total_matched / total_post >= 0.2:
        return True


def group_influencers(source_dir_paths, output_csv_dir):
    """
    Merge all the files in source_dir_path that start with file_prefix into a single csv file.
    """
    file_prefix = 'english_'
    if not os.path.exists(output_csv_dir):
        os.makedirs(output_csv_dir)
    influencers_output_csv_path = os.path.join(
        output_csv_dir, 'influencers.csv')
    porn_influencers_output_csv_path = os.path.join(
        output_csv_dir, 'porn_influencers.csv')
    influencers_csv_file = open(influencers_output_csv_path, 'w')
    influencers_csv_file.write(
        'id,username,location,verified,followers_count,tweet_count,created_at,user_url,description\n')
    porn_influencers_csv_file = open(porn_influencers_output_csv_path, 'w')
    porn_influencers_csv_file.write(
        'id,username,location,verified,followers_count,tweet_count,created_at,user_url,description\n')
    api_manager = TwitterAPIManager()
    counter = 0
    for source_dir_path in source_dir_paths:
        for file_name in os.listdir(source_dir_path):
            if file_name.startswith(file_prefix):
                for line in open(os.path.join(source_dir_path, file_name)):
                    influencer_data_json = json.loads(line)
                    id = influencer_data_json['id'] if 'id' in influencer_data_json else ""
                    username = influencer_data_json['username'] if 'username' in influencer_data_json else ""
                    description = influencer_data_json['description'] if 'description' in influencer_data_json else ""
                    description = re.sub(r"[\t\r\n,]", " ", description)
                    location = influencer_data_json['location'] if 'location' in influencer_data_json else ""
                    location = re.sub(r"[\t\r\n,]", " ", location)
                    verified = influencer_data_json['verified'] if 'verified' in influencer_data_json else False
                    followers_count = influencer_data_json['public_metrics'][
                        'followers_count'] if 'public_metrics' in influencer_data_json and 'followers_count' in influencer_data_json['public_metrics'] else 0
                    tweet_count = influencer_data_json['public_metrics'][
                        'tweet_count'] if 'public_metrics' in influencer_data_json and 'tweet_count' in influencer_data_json['public_metrics'] else 0
                    created_at = influencer_data_json['created_at'] if 'created_at' in influencer_data_json else ""
                    user_url = influencer_data_json['user_url'] if 'user_url' in influencer_data_json else ""
                    if id == "" or username == "":
                        continue
                    if is_porn_influencer(api_manager, influencer_data_json):
                        porn_influencers_csv_file.write(
                            f'{id},{username},{location},{verified},{followers_count},{tweet_count},{created_at},{user_url},{description}\n')
                        counter += 1
                    else:
                        influencers_csv_file.write(
                            f'{id},{username},{location},{verified},{followers_count},{tweet_count},{created_at},{user_url},{description}\n')
                        counter += 1
                    if counter % 10 == 0:
                        print(f'Processed {counter} influencers.')
    influencers_csv_file.close()
    porn_influencers_csv_file.close()


if __name__ == '__main__':
    folders = ['influencers', 'possible_porn_influencers']
    group_influencers([os.path.join(os.path.dirname(
        __file__), '..', '..', 'data', folder) for folder in folders], os.path.join(os.path.dirname(
            __file__), '..', '..', 'data', 'influencers'))
