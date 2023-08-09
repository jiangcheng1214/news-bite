import datetime
from newsAPI.NewsAPIManager import GeneralNewsType, NewsAPIManager, GeneralNews, NewsAPIType
from langChain.LangChainAPIManager import LangChainAPIManager
from twitter.TwitterAPIManager import TwitterAPIManager, TwitterAPIManagerAccountType
from newsAPI.NewsAPIItem import NewsAPIItem
from utils.Logging import info, error
import time
from typing import List

tweet_post_hour_interval = 3
# delay 2 minutes to post so that we can be ranked higher in search results sorted by time
run_time_start_delay_in_second = 120

fintechNewsAPIManager = NewsAPIManager(NewsAPIType.NewsAPITypeFintech)
langChainAPIManager = LangChainAPIManager()
twitterAPIManager = TwitterAPIManager(
    TwitterAPIManagerAccountType.TwitterAPIManagerAccountTypeFintech)


def get_recent_general_news(no_video=False) -> List[GeneralNews]:
    news_list = fintechNewsAPIManager.get_general_news()
    recent_news_list = []
    for news in news_list:
        try:
            if news.timestamp < int(time.time()) - 3600 * tweet_post_hour_interval:
                continue
            recent_news_list.append(news)
        except Exception as e:
            error(f"Exception in getting general news: {e}\n{news}")
            continue
    if no_video:
        recent_news_list = [
            x for x in recent_news_list if x.type != GeneralNewsType.Video.value]
    recent_news_list.sort(key=lambda x: x.rank_score, reverse=True)
    recent_news_list.sort(key=lambda x: x.type, reverse=True)
    info(f"Recent general news count: {len(recent_news_list)}")
    return recent_news_list


def get_recent_tickers_news(no_video=False) -> List[GeneralNews]:
    news_list = fintechNewsAPIManager.get_tickers_news()
    recent_news_list = []
    for news in news_list:
        try:
            if news.timestamp < int(time.time()) - 3600 * tweet_post_hour_interval:
                continue
            recent_news_list.append(news)
        except Exception as e:
            error(f"Exception in getting ticker news: {e}\n{news}")
            continue
    if no_video:
        recent_news_list = [
            x for x in recent_news_list if x.type != GeneralNewsType.Video.value]
    recent_news_list.sort(key=lambda x: x.rank_score, reverse=True)
    recent_news_list.sort(key=lambda x: x.type, reverse=True)
    info(f"Recent ticker news count: {len(recent_news_list)}")
    return recent_news_list


def run():
    no_video = True
    ticker_news_list = get_recent_tickers_news(no_video)[:10]
    ticker_news_post_candidate_list = []
    general_news_list = get_recent_general_news(no_video)[:10]
    general_news_post_candidate_list = []
    for n in ticker_news_list + general_news_list:
        tweet_dict = langChainAPIManager.generate_tweet_dict(
            title=n.news_title, abstract=n.news_text, topics=n.topics, source=n.source_name)
        content = tweet_dict['tweet_content']
        sentiment = n.sentiment
        is_event = n.event_id is not None
        candidate = NewsAPIItem({
            'news_content': content,
            "news_url": n.news_url,
            "media_url": n.image_url,
            "hashtags": tweet_dict['hashtags'],
            "sentiment": sentiment,
            "is_event": is_event,
            "is_video": n.type == GeneralNewsType.Video.value,
        })
        if n.tickers is not None and len(n.tickers) > 0:
            ticker_news_post_candidate_list.append(candidate)
        else:
            general_news_post_candidate_list.append(candidate)
    info(
        f"[Stock] Ticker news candidate Ticker News({len(ticker_news_post_candidate_list)}) General News({len(general_news_post_candidate_list)})")
    twitterAPIManager.post_tweets(
        general_news_post_candidate_list, post_limit=2)
    twitterAPIManager.post_tweets(
        ticker_news_post_candidate_list, post_limit=4)


if __name__ == "__main__":
    should_first_run = True
    while True:
        try:
            current_start_time = datetime.datetime.now()
            hour = current_start_time.hour
            next_hour_start_time = (current_start_time + datetime.timedelta(hours=1)
                                    ).replace(minute=0, second=0, microsecond=0)
            if hour % tweet_post_hour_interval == 0 or should_first_run:
                run()
                should_first_run = False
            sec_until_next_start = (next_hour_start_time -
                                    datetime.datetime.now()).seconds + run_time_start_delay_in_second
            info(f"Seconds until the next hour starts: {sec_until_next_start}")
            time.sleep(sec_until_next_start+5)
        except Exception as e:
            error(f"Exception in running twitter summary generation: {e}")
            time.sleep(60)
