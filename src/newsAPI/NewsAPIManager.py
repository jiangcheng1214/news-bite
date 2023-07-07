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
from enum import Enum

load_dotenv()

STOCK_TICKERS_TO_WATCH = "AAPL,ADBE,AGG,AI,AMD,AMZN,ARKQ,ASML,ATVI,BABA,BIDU,BOTZ,BRK,CIBR,CRM,DIA,FTEC,GOOG,GOOGL,IBM,INTC,IRBO,IYW,MSFT,MU,NVDA,ORCL,PLTR,QQQ,QTUM,ROBO,SAP,SHOP,SPY,TSLA,TSM,UBER,VGT,XLK"


class NewsAPIType(Enum):
    NewsAPITypeCrypto = "crypto"
    NewsAPITypeFintech = "fintech"

class GeneralNewsType(Enum):
    Article = "Article"
    Video = "Video"

class GeneralNews:
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


class NewsAPIManager():
    def __init__(self, news_api_type: NewsAPIType):
        self.news_api_type = news_api_type
        if news_api_type == NewsAPIType.NewsAPITypeCrypto:
            self.base_url = "https://cryptonews-api.com/api/v1"
            self.api_key = os.getenv("CRYPTONEWS_API_KEY")
        elif news_api_type == NewsAPIType.NewsAPITypeFintech:
            self.base_url = "https://stocknewsapi.com/api/v1"
            self.api_key = os.getenv("STOCKNEWS_API_KEY")

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
        info(
            f"NewsAPIManager({self.news_api_type}): Requesting get_general_news: {unquoted_url}")
        response_json = json.loads(response.text)
        news_json_list = response_json['data']
        news_list = []
        for news_json in news_json_list:
            try:
                news_list.append(GeneralNews(news_json))
            except Exception as e:
                error(f"Error occurred: {e}. {news_json}")
                continue
        info(
            f"NewsAPIManager({self.news_api_type}): get_general_news: {len(news_list)} news returned.")
        return news_list

    # Stock api only
    def get_tickers_news(self):
        assert self.news_api_type == NewsAPIType.NewsAPITypeFintech
        params = {
            "tickers": STOCK_TICKERS_TO_WATCH,
            "token": self.api_key,
            "items": 50,
            "extra-fields": "id,eventid,rankscore"
        }
        query_string = urlencode(params)
        composed_url = urljoin(self.base_url, '?' + query_string)
        unquoted_url = unquote(composed_url)
        response = requests.request("GET", unquoted_url)
        info(
            f"NewsAPIManager({self.news_api_type}): Requesting get_tickers_news: {unquoted_url}")
        response_json = json.loads(response.text)
        news_json_list = response_json['data']
        news_list = []
        for news_json in news_json_list:
            try:
                news_list.append(GeneralNews(news_json))
            except Exception as e:
                error(f"Error occurred: {e}. {news_json}")
                continue
        info(
            f"NewsAPIManager({self.news_api_type}): get_tickers_news: {len(news_list)} news returned.")
        return news_list

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
        info(
            f"NewsAPIManager({self.news_api_type}): Requesting get_headline_news_ids: {composed_url}")
        response_json = json.loads(response.text)
        news_json_list = response_json['data']
        news_ids = [str(news_json['news_id']) for news_json in news_json_list]
        return news_ids

    # premium access only
    def get_headline_news(self) -> GeneralNews:
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
        info(
            f"NewsAPIManager({self.news_api_type}): Requesting get_headline_news: {unquoted_url}")
        response_json = json.loads(response.text)
        news_json_list = response_json['data']
        news_list = []
        for news_json in news_json_list:
            try:
                news_list.append(GeneralNews(news_json))
            except Exception as e:
                error(f"Error occurred: {e}. {news_json}")
                continue
        return news_list

    # premium access only
    def get_all_ticker_news(self) -> GeneralNews:
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
        info(
            f"NewsAPIManager({self.news_api_type}): Requesting get_all_ticker_news: {unquoted_url}")
        response_json = json.loads(response.text)
        news_json_list = response_json['data']
        news_list = []
        for news_json in news_json_list:
            try:
                news_list.append(GeneralNews(news_json))
            except Exception as e:
                error(f"Error occurred: {e}. {news_json}")
                continue
        return news_list


if __name__ == "__main__":
    # crypto_news_api_manager = NewsAPIManager(NewsAPIType.NewsAPITypeCrypto)
    pass
