import datetime
import os
from instagram.InstagramAPIManager import (
    InstagramAPIManager,
    InstagramAPIManagerAccountType,
)
from newsAPI.NewsAPIManager import (
    GeneralNewsType,
    NewsAPIManager,
    GeneralNews,
    NewsAPIType,
)
from langChain.LangChainAPIManager import LangChainAPIManager
from posterGeneration.PosterGenerator import PosterGenerator
from threadsMeta.ThreadsAPIManager import (
    ThreadsAPIManager,
    ThreadsAPIManagerAccountType,
)
from newsAPI.NewsAPIItem import NewsAPIItem
from utils.Logging import info, error
import time
from typing import List

post_hour_interval = 3

cryptoNewsAPIManager = NewsAPIManager(NewsAPIType.NewsAPITypeCrypto)
langChainAPIManager = LangChainAPIManager()
posterGenerator = PosterGenerator()
instagramAPIManager = InstagramAPIManager(
    InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeOther,
    username="58pjoy1f",
    password="HgMHufzr",
)


def get_recent_general_news(no_video=False) -> List[GeneralNews]:
    news_list = cryptoNewsAPIManager.get_general_news()
    recent_news_list = []
    for news in news_list:
        try:
            if news.timestamp < int(time.time()) - 3600 * post_hour_interval:
                continue
            recent_news_list.append(news)
        except Exception as e:
            error(f"Exception in getting general news: {e}\n{news}")
            continue
    if no_video:
        recent_news_list = [
            x for x in recent_news_list if x.type != GeneralNewsType.Video.value
        ]
    recent_news_list.sort(key=lambda x: x.rank_score, reverse=True)
    recent_news_list.sort(key=lambda x: x.type, reverse=True)
    info(f"Recent news count: {len(recent_news_list)}")
    return recent_news_list


def run():
    news_list = get_recent_general_news(no_video=True)[:10]
    news_items = []
    for n in news_list:
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
                "rank_score": n.rank_score,
                "hashtags": candidate_dict["hashtags"],
                "sentiment": sentiment,
                "is_event": is_event,
                "is_video": n.type == GeneralNewsType.Video.value,
            }
        )
        news_items.append(candidate)
    info(f"Post candidate count: {len(news_items)}")
    try:
        publish_candidates = instagramAPIManager.generate_publish_candidates(news_items)
        instagramAPIManager.publish_image_post(publish_candidates, publish_limit=2)
        instagramAPIManager.publish_image_story(publish_candidates, publish_limit=2)
    except Exception as e:
        if "login_required" in str(e):
            error("Instagram login required during posting image")
            instagramAPIManager.login_user()
        else:
            error("Error posting image: " + str(e))
    try:
        comment_text_with_news_content = news_items[0].news_content
        instagramAPIManager.comment_media_from_searched_users(
            "crypto currency", comment_text_with_news_content
        )
    except Exception as e:
        if "login_required" in str(e):
            error("Instagram login required during liking and commenting")
            instagramAPIManager.login_user()


def test_dm():
    instagramAPIManager.dm_influencers("jaycee.1214", total_users_to_reach=1)


if __name__ == "__main__":
    test_dm()
