import json
import time
from utils.Logging import info
from typing import Dict
from urllib.parse import urlencode
import requests
from twitter.TwitterFilterRulesManager import TwitterFilterRulesManager


class TweetStreamData:
    def __init__(self, data: Dict):
        self.author_id = data['author_id']
        self.created_at = data['created_at']
        self.edit_history_tweet_ids = data['edit_history_tweet_ids']
        self.entities = data['entities']
        self.id = data['id']
        self.lang = data['lang']
        self.text = data['text']


class TwitterFilteredStreamer:
    stream_url: str
    rules_url: str
    stream: requests.Response
    rules_manager: TwitterFilterRulesManager
    api_key: str
    data_callback: callable
    running: bool

    def __init__(self, api_key: str, data_callback: callable):
        self.api_key = api_key
        self.rules_url = 'https://api.twitter.com/2/tweets/search/stream/rules'
        # https://developer.twitter.com/en/docs/twitter-api/data-dictionary/object-model/tweet
        response_params = urlencode({
            'tweet.fields': 'id,author_id,text,created_at,entities,lang',
            'user.fields': 'id,username',
        })
        self.stream_url = f'https://api.twitter.com/2/tweets/search/stream?{response_params}'

        self.rules_manager = TwitterFilterRulesManager(api_key)
        self.data_callback = data_callback
        self.running = False

    def start_stream(self):
        if self.running:
            exit(1)
        self.running = True
        self.rules_manager.update_rules_if_necessary()
        self.tweet_received_since_start = 0
        headers = {
            'User-Agent': 'v2FilterStreamPy',
            'Authorization': f'Bearer {self.api_key}',
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
                            for matching_rule_tag in set([r['tag'] for r in data['matching_rules']]):
                                self.data_callback(
                                    data['data'], matching_rule_tag)
                        except json.JSONDecodeError as e:
                            info(
                                f"Failed to load json due to json.JSONDecodeError. {line}")
                        except KeyError:
                            info(
                                f"Failed to load json due to KeyError. {line}")
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
        info('Max attempt hit')
