import json
import os
import time
from typing import List

import requests
from requests.structures import CaseInsensitiveDict


class TwitterFilterRulesManager:
    rules_url = 'https://api.twitter.com/2/tweets/search/stream/rules'

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self.rules_file_path = os.path.join(os.path.dirname(
            __file__),  'rules', 'twitter_filter_rules.json')

    def should_update_rules(self, active_rules: List[dict], local_rules: List[dict]) -> bool:
        if active_rules is None or local_rules is None or len(local_rules) != len(active_rules):
            return True
        rules = set()
        for active_rule in active_rules:
            rules.add(active_rule.value)
        for local_rule in local_rules:
            if local_rule.value and local_rule.value in rules:
                continue
            return True
        return False

    def update_rules_if_necessary(self):
        active_rules = self.get_active_rules()
        local_rules = self.get_local_rules()
        if ('data' in active_rules):
            deletion_response = self.delete_all_active_rules(
                active_rules['data'])
            print('Deletion response.', deletion_response)
        setting_rules_response = self.set_rules(local_rules)
        print('SetRules response:', setting_rules_response)
        # rules_file_path = os.path.join(os.path.dirname(os.path.abspath(
        #     __file__)), f'rules/temp/{str(int(time.time()))}.json')
        # with open(rules_file_path, 'w') as f:
        #     json.dump(setting_rules_response['data'], f, indent=2)
        # new_active_rules = self.get_active_rules()
        # if ('data' in new_active_rules):
        #     print(
        #         f"rules updated. New active rules: {new_active_rules['data']}")

    def get_local_rules(self):
        if not os.path.exists(self.rules_file_path):
            return []
        with open(self.rules_file_path, 'r') as f:
            rules = json.load(f)
        return rules

    def get_active_rules(self):
        headers = {}
        headers['Authorization'] = f'Bearer {self._api_key}'
        response = requests.get(self.rules_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data

    def set_rules(self, rules: List[dict]):
        headers = {}
        headers['Content-Type'] = 'application/json'
        headers['Authorization'] = f'Bearer {self._api_key}'
        data = {
            'add': rules
        }
        res = requests.post(self.rules_url, headers=headers, json=data)
        res.raise_for_status()
        response_data = res.json()
        return response_data

    def delete_all_active_rules(self, rules: List[dict]):
        if not isinstance(rules, list):
            return None
        ids = [r['id'] for r in rules]
        headers = CaseInsensitiveDict()
        headers['Content-Type'] = 'application/json'
        headers['Authorization'] = f'Bearer {self._api_key}'
        data = {
            'delete': {
                'ids': ids
            }
        }
        res = requests.post(self.rules_url, headers=headers, json=data)
        res.raise_for_status()
        response_data = res.json()
        return response_data
