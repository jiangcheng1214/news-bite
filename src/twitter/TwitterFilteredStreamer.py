import json
import time
from utils.Logging import info, warn
from urllib.parse import urlencode
import requests
from twitter.TwitterFilterRulesManager import TwitterFilterRulesManager


class TwitterFilteredStreamer:
    stream_url: str
    stream: requests.Response
    rules_manager: TwitterFilterRulesManager
    bearer_token: str
    data_callback: callable

    def __init__(self, bearer_token: str, twitterFilterRulesManager: TwitterFilterRulesManager, data_callback: callable):
        self.bearer_token = bearer_token
        # https://developer.twitter.com/en/docs/twitter-api/data-dictionary/object-model/tweet
        response_params = urlencode({
            'tweet.fields': 'id,author_id,text,created_at,entities,lang,attachments',
            'user.fields': 'id,username',
        })
        self.stream_url = f'https://api.twitter.com/2/tweets/search/stream?{response_params}'
        self.rules_manager = twitterFilterRulesManager
        self.data_callback = data_callback

    def start_stream(self):
        self.rules_manager.sync_filter_rules()
        self.tweet_received_since_start = 0
        headers = {
            'User-Agent': 'v2FilterStreamPy',
            'Authorization': f'Bearer {self.bearer_token}',
        }
        attempts = 0
        max_attempts = 5
        retry_delay = 5  # seconds
        while attempts < max_attempts:
            response = requests.get(
                self.stream_url, headers=headers, stream=True, timeout=300)
            if response.status_code == 429:
                info(
                    f"Too Many Requests. {response.status_code} {response.reason}.")
                attempts += 1
                # sleep 15 mins due to 429 Too Many Requests.
                time.sleep(15*60)
            elif response.status_code != 200:
                info(
                    f"Failed to connect to stream: {response.status_code} {response.reason}.")
                attempts += 1
                time.sleep(retry_delay)
            else:
                attempts = 0
                try:
                    for line in response.iter_lines():
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            matching_rules = data['matching_rules']
                            matching_tags = [r['tag'] for r in matching_rules]
                            matching_tags_set = set(matching_tags)
                            tweet_data = data['data']
                        except json.JSONDecodeError as e:
                            info(
                                f"Failed to load json due to json.JSONDecodeError. {line}")
                            continue
                        except KeyError as e:
                            info(
                                f"Failed to load json due to KeyError. {line}")
                            continue
                        try:
                            for matching_rule_tag in matching_tags_set:
                                self.data_callback(
                                    tweet_data, matching_rule_tag)
                        except Exception as e:
                            warn(
                                f'Failed to process tweet data due to {e}. Line: {line}')
                except (requests.exceptions.ConnectionError):
                    info(
                        f'Retrying in {retry_delay} seconds due to ConnectionError')
                    attempts += 1
                    time.sleep(retry_delay)
                except (TimeoutError):
                    attempts += 1
                    info(
                        f'Retrying in {retry_delay} seconds due to TimeoutError')
                    time.sleep(retry_delay)
                except (requests.exceptions.ChunkedEncodingError):
                    attempts += 1
                    info(
                        f'Retrying in {retry_delay} seconds due to ChunkedEncodingError')
                    time.sleep(retry_delay)
        info('Max attempt hit')
