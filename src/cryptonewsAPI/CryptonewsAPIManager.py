from dateutil import parser
import requests
from utils.Logging import info, warn, error
from utils.Logging import info, warn
from utils.Utilities import get_today_date, get_yesterday_date
from dotenv import load_dotenv
import os
import json
from typing import List
from urllib.parse import urlencode, urljoin, unquote

load_dotenv()


class CryptoNews:
    def __init__(self, initial_dict: dict):
        self.news_url = initial_dict.get("news_url")
        if self.news_url.endswith("?SNAPI"):
            self.news_url = self.news_url[:-6]
        self.image_url = initial_dict.get("image_url")
        if self.image_url.endswith("?SNAPI"):
            self.image_url = self.image_url[:-6]
        self.news_title = initial_dict.get("title")
        self.news_text = initial_dict.get("text")
        self.topics = initial_dict.get("topics")
        self.sentiment = initial_dict.get("sentiment")
        self.source_name = initial_dict.get("source_name")
        self.type = initial_dict.get("type")
        self.tickers = initial_dict.get("tickers")
        self.date = initial_dict.get("date")
        self.rank_score = initial_dict.get("rank_score")
        self.event_id = initial_dict.get("eventid")
        self.timestamp = int(parser.parse(self.date).timestamp())

    def __repr__(self):
        return {
            "news_url": self.news_url,
            "image_url": self.image_url,
            "news_title": self.news_title,
            "news_text": self.news_text,
            "topics": self.topics,
            "sentiment": self.sentiment,
            "source_name": self.source_name,
            "type": self.type,
            "tickers": self.tickers,
            "sentiment": self.sentiment,
            "date": self.date,
            "rank_score": self.rank_score,
            "event_id": self.event_id,
            "timestamp": self.timestamp
        }

    def __str__(self):
        return f"<CryptoNews> {self.news_text} ({self.date})"


class CryptoEvent:
    def __init__(self, initial_dict: dict):
        self.event_name = initial_dict.get("event_name")
        self.event_text = initial_dict.get("event_text")
        self.event_id = initial_dict.get("event_id")
        self.news_items = initial_dict.get("news_items")
        self.tickers = initial_dict.get("tickers")
        self.date = initial_dict.get("date")
        self.timestamp = int(parser.parse(self.date).timestamp())

    def __repr__(self):
        return {
            "event_name": self.event_name,
            "event_text": self.event_text,
            "event_id": self.event_id,
            "news_items": self.news_items,
            "tickers": self.tickers,
            "date": self.date,
            "timestamp": self.timestamp
        }

    def __str__(self):
        return f"<CryptoEvent> {self.event_name} ({self.date})"


class CryptonewsAPIManager():
    def __init__(self):
        self.base_url = "https://cryptonews-api.com/api/v1"
        self.api_key = os.getenv("CRYPTONEWS_API_KEY")

    def get_events(self, date=None) -> List[CryptoEvent]:
        if date is None:
            # Default to yesterday and today
            yesterday_date = get_yesterday_date("%m%d%Y")
            today_date = get_today_date("%m%d%Y")
            date = f"{yesterday_date}-{today_date}"
        url = f"{self.base_url}/events"
        params = {
            "date": date,
            "token": self.api_key,
            "metadata": 1,
            "items": 100}
        query_string = urlencode(params)
        composed_url = urljoin(url, '?' + query_string)
        response = requests.request("GET", composed_url)
        info(f"CryptoEvent: Requesting get_events: {composed_url}")
        response_json = json.loads(response.text)
        total_count = response_json['total_pages']
        if total_count > 50:
            warn(
                f"CryptoEvent: total_count is {total_count}. Only 50 events returned due to page limit.")
        event_json_list = response_json['data']
        event_list = [CryptoEvent(event_json)
                      for event_json in event_json_list]
        return event_list

    def _get_headline_news_ids(self) -> List[str]:
        # Default to yesterday and today
        yesterday_date = get_yesterday_date("%m%d%Y")
        today_date = get_today_date("%m%d%Y")
        date = f"{yesterday_date}-{today_date}"
        url = f"{self.base_url}/trending-headlines"
        params = {
            "date": date,
            "token": self.api_key,
            "metadata": 1,
            "items": 50}
        query_string = urlencode(params)
        composed_url = urljoin(url, '?' + query_string)
        response = requests.request("GET", composed_url)
        info(f"CryptoEvent: Requesting get_headline_news_ids: {composed_url}")
        response_json = json.loads(response.text)
        news_json_list = response_json['data']
        news_ids = [str(news_json['news_id']) for news_json in news_json_list]
        return news_ids

    def get_headline_news(self) -> CryptoNews:
        news_ids = self._get_headline_news_ids()
        url = f"{self.base_url}/category"
        params = {
            "news_id": ",".join(news_ids),
            "token": self.api_key,
            "metadata": 1,
            "items": 50,
            "section": "general",
            "extra-fields": "id,eventid,rankscore"}
        query_string = urlencode(params)
        composed_url = urljoin(url, '?' + query_string)
        unquoted_url = unquote(composed_url)
        response = requests.request("GET", unquoted_url)
        info(f"CryptoEvent: Requesting get_headline_news: {unquoted_url}")
        response_json = json.loads(response.text)
        news_json_list = response_json['data']
        news_list = []
        for news_json in news_json_list:
            try:
                news_list.append(CryptoNews(news_json))
            except Exception as e:
                error(f"Error occurred: {e}. {news_json}")
                continue
        return news_list

    def get_all_ticker_news(self) -> CryptoNews:
        url = f"{self.base_url}/category"
        params = {
            "section": "alltickers",
            "token": self.api_key,
            "metadata": 1,
            "items": 50,
            "extra-fields": "id,eventid,rankscore"
        }
        query_string = urlencode(params)
        composed_url = urljoin(url, '?' + query_string)
        unquoted_url = unquote(composed_url)
        response = requests.request("GET", unquoted_url)
        info(f"CryptoEvent: Requesting get_all_ticker_news: {unquoted_url}")
        response_json = json.loads(response.text)
        news_json_list = response_json['data']
        news_list = []
        for news_json in news_json_list:
            try:
                news_list.append(CryptoNews(news_json))
            except Exception as e:
                error(f"Error occurred: {e}. {news_json}")
                continue
        return news_list

    def get_general_news(self):
        url = f"{self.base_url}/category"
        params = {
            "section": "general",
            "token": self.api_key,
            "metadata": 1,
            "items": 50,
            "extra-fields": "id,eventid,rankscore"
        }
        query_string = urlencode(params)
        composed_url = urljoin(url, '?' + query_string)
        unquoted_url = unquote(composed_url)
        response = requests.request("GET", unquoted_url)
        info(f"CryptoEvent: Requesting get_general_news: {unquoted_url}")
        response_json = json.loads(response.text)
        news_json_list = response_json['data']
        news_list = []
        for news_json in news_json_list:
            try:
                news_list.append(CryptoNews(news_json))
            except Exception as e:
                error(f"Error occurred: {e}. {news_json}")
                continue
        info(f"CryptoEvent: get_general_news: {len(news_list)} news returned.")
        return news_list

if __name__ == "__main__":
    cryptonews_api_manager = CryptonewsAPIManager()
    events = cryptonews_api_manager.get_events()
    for e in events:
        info(e.__repr__())
    news = get_headline_news = cryptonews_api_manager.get_headline_news(
        limit=10)
    for n in news:
        info(n.__repr__())
