import datetime
from instagram.InstagramAPIManager import (
    InstagramAPIManager,
    InstagramAPIManagerAccountType,
    get_next_proxy,
)
from newsAPI.NewsAPIManager import (
    GeneralNewsType,
    NewsAPIManager,
    GeneralNews,
    NewsAPIType,
)
from langChain.LangChainAPIManager import LangChainAPIManager
from threadsMeta.ThreadsAPIManager import (
    ThreadsAPIManager,
    ThreadsAPIManagerAccountType,
)
from newsAPI.NewsAPIItem import NewsAPIItem
from utils.Logging import info, error
from utils.Constants import INS_POST_INTERVAL_HOUR
import time

newsAPIManager = NewsAPIManager(NewsAPIType.NewsAPITypeFintech)
langChainAPIManager = LangChainAPIManager()
threadsAPIManager = ThreadsAPIManager(
    ThreadsAPIManagerAccountType.ThreadsAPIManagerAccountTypeFintech
)
instagramAPIManager = InstagramAPIManager(
    InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeFintech
)


def run():
    ticker_news_list = newsAPIManager.get_recent_tickers_news(
        INS_POST_INTERVAL_HOUR, no_video=True
    )[:10]
    ticker_news_post_candidate_list = []
    general_news_list = newsAPIManager.get_recent_general_news(
        INS_POST_INTERVAL_HOUR, no_video=True
    )[:10]
    general_news_post_candidate_list = []
    for n in ticker_news_list + general_news_list:
        candidate_dict = langChainAPIManager.generate_tweet_dict(
            title=n.news_title,
            abstract=n.news_text,
            topics=n.topics,
            source=n.source_name,
        )
        content = candidate_dict["tweet_content"]
        sentiment = n.sentiment
        is_event = n.event_id is not None
        candidate = NewsAPIItem(
            {
                "news_content": content,
                "news_url": n.news_url,
                "image_url": n.image_url,
                "hashtags": candidate_dict["hashtags"],
                "sentiment": sentiment,
                "is_event": is_event,
                "is_video": n.type == GeneralNewsType.Video.value,
            }
        )
        if n.tickers is not None and len(n.tickers) > 0:
            ticker_news_post_candidate_list.append(candidate)
        else:
            general_news_post_candidate_list.append(candidate)
    info(
        f"[Stock] Ticker news candidate Ticker News({len(ticker_news_post_candidate_list)}) General News({len(general_news_post_candidate_list)})"
    )

    general_news_candidates = instagramAPIManager.generate_publish_candidates(
        general_news_post_candidate_list
    )
    ticker_news_candidates = instagramAPIManager.generate_publish_candidates(
        ticker_news_post_candidate_list
    )

    # post instagram with retry
    for i in range(3):
        try:
            instagramAPIManager.publish_image_post(
                general_news_candidates, publish_limit=1
            )
            instagramAPIManager.publish_image_story(
                general_news_candidates, publish_limit=1
            )
            instagramAPIManager.publish_image_post(
                ticker_news_candidates, publish_limit=1
            )
            instagramAPIManager.publish_image_story(
                ticker_news_candidates, publish_limit=1
            )
            break
        except Exception as e:
            if "login_required" in str(e):
                error("Instagram login required during posting image")
                instagramAPIManager.login_user()
            if "Please wait a few minutes before you try again" in str(e):
                error("ip was possibly banned by instagram. Try login with proxy")
                proxy = get_next_proxy()
                instagramAPIManager.login_user(proxy=proxy)

    # comment related posts
    # comment_text_with_news_content = general_news_post_candidate_list[0].news_content
    # instagramAPIManager.comment_media_from_searched_users(
    #     "stock trading", comment_text_with_news_content
    # )
    # post threads
    threadsAPIManager.post_threads(general_news_post_candidate_list, post_limit=2)
    threadsAPIManager.post_threads(ticker_news_post_candidate_list, post_limit=4)


if __name__ == "__main__":
    while True:
        try:
            current_start_time = datetime.datetime.now()
            hour = current_start_time.hour
            next_hour_start_time = (
                current_start_time + datetime.timedelta(hours=1)
            ).replace(minute=0, second=0, microsecond=0)
            next_hour_start_ts = next_hour_start_time.timestamp()
            if hour % INS_POST_INTERVAL_HOUR == 0:
                try:
                    run()
                except Exception as e:
                    if "login_required" in str(e):
                        error("Instagram login required during run() function")
                        instagramAPIManager.login_user()
                    if "Please wait a few minutes before you try again" in str(e):
                        error("ip was possibly banned by instagram. login with proxy")
                        proxy = get_next_proxy()
                        instagramAPIManager.login_user(proxy=proxy)
                        # we don't retry run() function here
            current_ts = datetime.datetime.now().timestamp()
            sec_until_next_start = max(next_hour_start_ts - current_ts, 1)
            info(f"Seconds until the next hour starts: {sec_until_next_start}")
            time.sleep(sec_until_next_start)
        except Exception as e:
            error(f"Exception in posting for fintech: {e}")
            time.sleep(60)
