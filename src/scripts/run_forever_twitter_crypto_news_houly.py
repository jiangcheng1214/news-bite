import datetime
from cryptonewsAPI.CryptonewsAPIManager import CryptonewsAPIManager, CryptoNews
from langChain.LangChainAPIManager import LangChainAPIManager
from twitter.TwitterAPIManager import TwitterAPIManager, TwitterAPIManagerAccountType, TwitterPostCandidate
from utils.Logging import info, error
import time
from typing import List

tweet_post_hour_interval = 1
# delay 3 minutes to post so that we can be ranked higher in search results sorted by time
run_time_start_delay_in_second = 180

cryptonewsAPIManager = CryptonewsAPIManager()
langChainAPIManager = LangChainAPIManager()
twitterAPIManager = TwitterAPIManager(
    TwitterAPIManagerAccountType.TwitterAPIManagerAccountTypeCrypto)


def get_recent_all_ticker_news() -> List[CryptoNews]:
    news_list = cryptonewsAPIManager.get_all_ticker_news()
    recent_news_list = []
    for news in news_list:
        if news.timestamp < int(time.time()) - 3600 * tweet_post_hour_interval:
            continue
        recent_news_list.append(news)
    recent_news_list.sort(key=lambda x: x.rank_score, reverse=True)
    return recent_news_list


def get_recent_general_news() -> List[CryptoNews]:
    news_list = cryptonewsAPIManager.get_general_news()
    recent_news_list = []
    for news in news_list:
        try:
            if news.timestamp < int(time.time()) - 3600 * tweet_post_hour_interval:
                continue
            recent_news_list.append(news)
        except Exception as e:
            error(f"Exception in getting general news: {e}\n{news}")
            continue
    recent_news_list.sort(key=lambda x: x.rank_score, reverse=True)
    info(f"Recent news count: {len(recent_news_list)}")
    return recent_news_list


if __name__ == "__main__":
    while True:
        try:
            current_start_time = datetime.datetime.now()
            next_hour_start_time = (current_start_time + datetime.timedelta(hours=1)
                                    ).replace(minute=0, second=0, microsecond=0)
            news_list = get_recent_general_news()
            post_candidate_list = []
            for n in news_list:
                tweet_dict = langChainAPIManager.generate_tweet_dict(
                    title=n.news_title, abstract=n.news_text, topics=n.topics, source=n.source_name)
                content = tweet_dict['tweet_content']
                hashtags = []
                if type(tweet_dict['hashtags']) == list:
                    hashtags = tweet_dict['hashtags']
                elif type(tweet_dict['hashtags']) == str:
                    hashtags = tweet_dict['hashtags'].split(',')
                clean_hashtags = []
                for h in hashtags:
                    tag = h.strip().replace('-', '').replace('.', '')
                    if not tag.startswith('#'):
                        clean_hashtags.append(f"#{tag}")
                    else:
                        clean_hashtags.append(tag)
                sentiment = n.sentiment
                is_event = n.event_id is not None
                candidate = TwitterPostCandidate({
                    'news_content': content,
                    "news_url": n.news_url,
                    "media_url": n.image_url,
                    "hashtags": clean_hashtags,
                    "sentiment": sentiment,
                    "is_event": is_event
                })
                post_candidate_list.append(candidate)
            info(f"Post candidate count: {len(post_candidate_list)}")
            twitterAPIManager.post_tweets(post_candidate_list, post_limit=5)
            sec_until_next_start = (next_hour_start_time -
                                    datetime.datetime.now()).seconds + run_time_start_delay_in_second
            info(f"Seconds until the next hour starts: {sec_until_next_start}")
            time.sleep(sec_until_next_start+5)
        except Exception as e:
            error(f"Exception in running twitter summary generation: {e}")
            time.sleep(60)
