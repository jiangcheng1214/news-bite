import json
import os

from dotenv import load_dotenv
from utils.Logging import info
from typing import List
from utils.Constants import TWITTER_BEARER_TOKEN_DEV_EVAR_KEY, TWITTER_BEARER_TOKEN_EVAR_KEY
from utils.Utilities import TwitterTopic
import requests


class TwitterFilterRulesManager:
    rules_url = 'https://api.twitter.com/2/tweets/search/stream/rules'

    def __init__(self, bearer_token: str, topic: str) -> None:
        self.bearer_token = bearer_token
        self.topic = topic
        self.rules_file_path = os.path.join(os.path.dirname(
            __file__),  'rules', 'twitter_filter_rules.json')

    def sync_filter_rules(self):
        active_rules = self._get_active_rules()
        local_rules = self._get_local_rules(self.topic)
        if (active_rules):
            deletion_response = self._delete_active_rules(
                active_rules)
            info(f'Deletion response. {deletion_response}')
        setting_rules_response = self._add_rules(local_rules)
        info(f'SetRules response: {setting_rules_response}')

    def get_all_active_rules(self):
        headers = {
            'Authorization': f'Bearer {self.bearer_token}',
            'Content-Type': 'application/json'
        }
        response = requests.get(self.rules_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if 'data' not in data:
            return []
        return data['data']

    def _get_local_rules(self, topic: str) -> List[dict]:
        if not os.path.exists(self.rules_file_path):
            return []
        monitoering_rules = []
        with open(self.rules_file_path, 'r') as f:
            rules = json.load(f)
            for rule in rules:
                if rule['tag'] == topic:
                    monitoering_rules.append(rule)
        return monitoering_rules

    def _get_active_rules(self):
        headers = {
            'Authorization': f'Bearer {self.bearer_token}',
            'Content-Type': 'application/json'
        }
        response = requests.get(self.rules_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if 'data' not in data:
            return []
        rules = [r for r in data['data'] if r['tag'] == self.topic]
        return rules

    def _add_rules(self, rules: List[dict]):
        headers = {
            'Authorization': f'Bearer {self.bearer_token}',
            'Content-Type': 'application/json'
        }
        data = {
            'add': rules
        }
        res = requests.post(self.rules_url, headers=headers, json=data)
        res.raise_for_status()
        response_data = res.json()
        return response_data

    def _delete_active_rules(self, rules: List[dict]):
        if not isinstance(rules, list):
            return None
        if not rules:
            return None
        ids = [r['id'] for r in rules]
        headers = {
            'Authorization': f'Bearer {self.bearer_token}',
            'Content-Type': 'application/json'
        }
        data = {
            'delete': {
                'ids': ids
            }
        }
        res = requests.post(self.rules_url, headers=headers, json=data)
        res.raise_for_status()
        response_data = res.json()
        return response_data


if __name__ == '__main__':
    load_dotenv()
    bearer_token = os.getenv(TWITTER_BEARER_TOKEN_EVAR_KEY)
    twitterFilterRulesManager = TwitterFilterRulesManager(
        bearer_token, 'influencers')
    # active_rules = twitterFilterRulesManager._get_active_rules()
    # info(active_rules)
    # all_active_rules = twitterFilterRulesManager.get_all_active_rules()
    # twitterFilterRulesManager._delete_active_rules(all_active_rules)
    info(twitterFilterRulesManager.get_all_active_rules())
