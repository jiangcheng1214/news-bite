import requests
import json
import logging

class RapidBBFinanceAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.host = "bloomberg-market-and-financial-news.p.rapidapi.com"
        self.base_url = "https://bloomberg-market-and-financial-news.p.rapidapi.com"
        self.logger = logging.getLogger(__name__)

    def _request(self, method, url, headers=None, params=None):
        if headers is None:
            headers = {}
        headers["X-RapidAPI-Key"] = self.api_key
        headers["X-RapidAPI-Host"] = self.host
        response = requests.request(method, url, headers=headers, params=params)
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            return response.status_code

        self.logger.debug(f"Response from {url}: {response.text}")

    def get_news_list(self, id):
        url = f"{self.base_url}/news/list"
        querystring = {"id": id}
        return self._request("GET", url, params=querystring)

    def get_story_detail(self, internal_id):
        url = f"{self.base_url}/stories/detail"
        querystring = {"internalID": internal_id}
        return self._request("GET", url, params=querystring)

