import json
import random
import time
from instagram.InstagramPostCandidate import InstagramPostCandidate
from newsAPI.NewsAPIItem import NewsAPIItem
from utils.Constants import (
    DM_IG_ACCOUNT_INDEX,
    DM_IG_ACCOUNTS,
    PAST_DM_USER_IDS_REDIS_KEY_CRYPTO,
    TODO_DM_USER_IDS_REDIS_KEY_CRYPTO,
    VISITED_INFLUENCER_ID_DICT_REDIS_KEY_CRYPTO,
)
from utils.RedisClient import RedisClient
from instagrapi.types import StoryLink
from utils.Logging import error, info, warn
from instagrapi import Client
from instagrapi.exceptions import LoginRequired
from enum import Enum
from typing import Dict, List
import os
from dotenv import load_dotenv
from posterGeneration.PosterGenerator import PosterGenerator
from utils.TextEmbeddingCache import TextEmbeddingCache

load_dotenv()


class InstagramAPIManagerAccountType(Enum):
    InstagramAPIManagerAccountTypeCrypto = 0
    InstagramAPIManagerAccountTypeFintech = 1
    InstagramAPIManagerAccountTypeOther = 2


def get_past_dm_user_ids(accountType: InstagramAPIManagerAccountType) -> set[str]:
    assert (
        accountType
        == InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto
    )
    past_dm_user_ids_str = RedisClient.shared().get(PAST_DM_USER_IDS_REDIS_KEY_CRYPTO)
    if past_dm_user_ids_str:
        past_dm_user_ids = set(json.loads(past_dm_user_ids_str))
    else:
        past_dm_user_ids = set()
    return past_dm_user_ids


def record_dm_user_ids(
    accountType: InstagramAPIManagerAccountType, user_ids: List[str]
):
    assert (
        accountType
        == InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto
    )
    past_dm_user_ids = get_past_dm_user_ids(accountType)
    past_dm_user_ids.update(user_ids)
    past_dm_user_ids = list(past_dm_user_ids)
    RedisClient.shared().set(
        PAST_DM_USER_IDS_REDIS_KEY_CRYPTO,
        json.dumps(past_dm_user_ids),
        ex=60 * 60 * 24 * 7,
    )


def get_visited_influencer_id_dict(
    accountType: InstagramAPIManagerAccountType,
) -> dict[str:int]:
    assert (
        accountType
        == InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto
    )
    visited_influencer_id_dict_str = RedisClient.shared().get(
        VISITED_INFLUENCER_ID_DICT_REDIS_KEY_CRYPTO
    )
    if visited_influencer_id_dict_str:
        visited_influencer_id_dict = json.loads(visited_influencer_id_dict_str)
    else:
        visited_influencer_id_dict = {}
    result = {}
    for k, v in visited_influencer_id_dict.items():
        if type(v) != int:
            continue
        current_time = int(time.time())
        if current_time - v < 60 * 60 * 24 * 30:
            result[k] = v
    return visited_influencer_id_dict


def add_visited_influencer_id(
    accountType: InstagramAPIManagerAccountType, influencer_id: str
):
    assert (
        accountType
        == InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto
    )
    visited_influencer_id_dict = get_visited_influencer_id_dict(accountType)
    visited_influencer_id_dict[influencer_id] = int(time.time())
    RedisClient.shared().set(
        VISITED_INFLUENCER_ID_DICT_REDIS_KEY_CRYPTO,
        json.dumps(visited_influencer_id_dict),
        ex=60 * 60 * 24 * 30,
    )


def clear_visited_influencer_ids(
    accountType: InstagramAPIManagerAccountType,
):
    assert (
        accountType
        == InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto
    )
    RedisClient.shared().delete(
        VISITED_INFLUENCER_ID_DICT_REDIS_KEY_CRYPTO,
    )


def get_existing_todo_dm_user_ids(
    accountType: InstagramAPIManagerAccountType,
) -> set[str]:
    assert (
        accountType
        == InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto
    )
    todo_dm_user_ids_str = RedisClient.shared().get(TODO_DM_USER_IDS_REDIS_KEY_CRYPTO)
    if todo_dm_user_ids_str:
        todo_dm_user_ids = set(json.loads(todo_dm_user_ids_str))
    else:
        todo_dm_user_ids = set()
    return todo_dm_user_ids


def set_todo_dm_user_ids(
    accountType: InstagramAPIManagerAccountType, user_ids: set[str]
):
    assert (
        accountType
        == InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto
    )
    RedisClient.shared().set(
        TODO_DM_USER_IDS_REDIS_KEY_CRYPTO,
        json.dumps(list(user_ids)),
        ex=60 * 60 * 24 * 7,
    )


def get_next_dm_ig_account():
    dm_ig_account_index = int(RedisClient.shared().get(DM_IG_ACCOUNT_INDEX) or 0)
    dm_ig_accounts_str = RedisClient.shared().get(DM_IG_ACCOUNTS)
    if dm_ig_accounts_str:
        dm_ig_accounts = json.loads(dm_ig_accounts_str)
    else:
        return ["", ""]
    dm_ig_account_index %= len(dm_ig_accounts)
    dm_ig_account = dm_ig_accounts[dm_ig_account_index]
    dm_ig_account_index += 1
    RedisClient.shared().set(DM_IG_ACCOUNT_INDEX, dm_ig_account_index)
    return dm_ig_account


def get_next_proxy():
    proxy_list_str = RedisClient.shared().get("proxy_ips")
    proxy = None
    if proxy_list_str:
        proxy_index = int(RedisClient.shared().get("proxy_index"))
        proxy_list = json.loads(proxy_list_str)
        proxy = proxy_list[proxy_index]
        proxy_index += 1
        proxy_index %= len(proxy_list)
        RedisClient.shared().set("proxy_index", proxy_index)
        proxy = proxy
    return proxy


class InstagramAPIManager:
    def __init__(
        self,
        accountType: InstagramAPIManagerAccountType,
        username=None,
        password=None,
        force_login=False,
        proxy=None,
    ):
        self.accountType = accountType
        self.posterGenerator = PosterGenerator()
        self.client = Client()
        self.client.delay_range = [0.5, 1.5]
        if (
            accountType
            == InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto
        ):
            self.username = os.environ.get("THREADS_CRYPTO_USER_NAME")
            self.password = os.environ.get("THREADS_CRYPTO_PASSWORD")
            self.session_path = os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "cache",
                f"instagram_session_crypto.json",
            )
            self.hashtag_appending = "#crypto #cryptocurrency #btc #bitcoin #passiveincome #eth #marketsentiment #cryptonews"
            self.comment_text_suffix = (
                "🙌 Latest crypto updates and sentimental news. #MissNoMore 🙌"
            )
        elif (
            accountType
            == InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeFintech
        ):
            self.username = os.environ.get("THREADS_FINTECH_USER_NAME")
            self.password = os.environ.get("THREADS_FINTECH_PASSWORD")
            self.session_path = os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "cache",
                f"instagram_session_fintech.json",
            )
            self.hashtag_appending = "#financialnews #technews #quant #marketsentiment #passiveincome #stockmarket #marketindicator #fintech"
            self.comment_text_suffix = (
                "🙌 Latest financial / tech updates and sentimental news. #MissNoMore 🙌"
            )
        else:
            assert (
                accountType
                == InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeOther
            )
            self.username = username
            self.password = password
            self.session_path = os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "cache",
                f"instagram_session_{self.username}.json",
            )
            self.hashtag_appending = ""
            self.comment_text_suffix = ""
            if not proxy:
                proxy = get_next_proxy()
        login_success = self.login_user(force_login=force_login, proxy=proxy)
        if not login_success and not proxy:
            error("Login failed, try again with proxy")
            proxy = get_next_proxy()
            self.login_user(force_login=force_login, proxy=proxy)

    def login_user(self, force_login=False, proxy=None):
        info(
            f"Logging in user: {self.username}. force_login: {force_login}. proxy: {proxy}"
        )
        username, password = self.username, self.password
        session = None
        if not force_login:
            if os.path.exists(self.session_path):
                session = self.client.load_settings(self.session_path)
        login_via_session = False
        login_via_pw = False
        if session:
            try:
                self.client.set_settings(session)
                self.client.login(username, password)
                # check if session is valid
                try:
                    self.client.get_timeline_feed()
                except LoginRequired:
                    warn("Session is invalid, need to login via username and password")
                    old_session = self.client.get_settings()
                    # use the same device uuids across logins
                    self.client.set_settings({})
                    self.client.set_uuids(old_session["uuids"])
                    self.client.login(username, password)
                login_via_session = True
            except Exception as e:
                error("Couldn't login user using session information: %s" % e)

        if not login_via_session:
            try:
                if proxy:
                    self.client.set_proxy(proxy)
                info(
                    f"Attempting to login via username and password. username: {username}"
                )
                if self.client.login(username, password):
                    login_via_pw = True
                    self.client.dump_settings(self.session_path)
            except Exception as e:
                info("Couldn't login user using username and password: %s" % e)

        if not login_via_pw and not login_via_session:
            error("Couldn't login user with either password or session")
            return False
        else:
            return True

    def generate_poster(self, text, image_url, sentiment):
        timestamp = int(time.time())
        prefix = (
            "crypto"
            if self.accountType
            == InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto
            else "fintech"
        )
        post_image_output_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", f"{prefix}_{timestamp}.jpg"
        )
        story_image_output_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "data",
            f"{prefix}_{timestamp}_story.jpg",
        )
        try:
            info(
                f"Generating poster for instagram post: {text} - {post_image_output_path}"
            )
            self.posterGenerator.generate_instagram_poster(
                text,
                image_url,
                sentiment,
                post_image_output_path,
                story_image_output_path,
            )
            if os.path.exists(post_image_output_path):
                if os.path.exists(story_image_output_path):
                    return post_image_output_path, story_image_output_path
                else:
                    return post_image_output_path, None
            else:
                return None, None
        except Exception as e:
            error(f"Exception in generating poster: {e}")
            return None, None

    def generate_publish_candidates(
        self, news_items: List[NewsAPIItem]
    ) -> List[InstagramPostCandidate]:
        post_candidates = []
        for newsItem in news_items:
            content = newsItem.news_content
            image_url = newsItem.image_url
            hashtags = newsItem.hashtags
            if type(hashtags) == list:
                hashtag_list = hashtags
            elif type(hashtags) == str:
                hashtag_list = hashtags.split(",")
                clean_hashtags = []
                for h in hashtag_list:
                    tag = (
                        h.strip()
                        .replace("-", "")
                        .replace(".", "")
                        .replace("@", "")
                        .replace("/", "")
                    )
                    if not tag.startswith("#"):
                        clean_hashtags.append(f"#{tag}")
                    else:
                        clean_hashtags.append(tag)
                hashtag_list = clean_hashtags
            hashtag_string = " ".join(hashtag_list).strip()
            if content.endswith(hashtag_string):
                content = content[: -len(hashtag_string)].strip()
            hashtag_string = f"{hashtag_string} {self.hashtag_appending}"
            content_with_hashtags = f"{content}\n{hashtag_string}"
            (
                most_similar_post,
                most_similar_post_similarity_score,
            ) = self.get_most_similar_posted_ins_and_similarity_score(content)
            if most_similar_post_similarity_score > 0.9:
                info(
                    f"Skip posting: {content}. Most similar post similarity score: {most_similar_post_similarity_score} - {most_similar_post}"
                )
                continue
            post_image_path, story_image_path = self.generate_poster(
                content, image_url, newsItem.sentiment
            )

            postCandidate = InstagramPostCandidate(
                {
                    "content": content,
                    "hashtags_str": hashtag_string,
                    "content_with_hashtags": content_with_hashtags,
                    "post_image_path": post_image_path,
                    "story_image_path": story_image_path,
                    "rank_score": newsItem.rank_score,
                    "sentiment": newsItem.sentiment,
                    "news_url": newsItem.news_url,
                }
            )
            post_candidates.append(postCandidate)
        return post_candidates

    def publish_image_post(
        self, publish_candidates: List[InstagramPostCandidate], publish_limit=1
    ):
        publish_count = 0
        for candidate in publish_candidates:
            if candidate.post_image_path is None:
                continue
            most_recent_post_ins_ids_before_post = self.get_most_recent_posted_ins_ids()
            try:
                enriched_content = f"{candidate.content}\n{candidate.hashtags_str}"
                publish_result = self.client.photo_upload(
                    candidate.post_image_path, enriched_content
                )
                info(
                    f"published instagram image: {candidate.post_image_path}. publish_result: {publish_result}"
                )
            except Exception as e:
                error(f"Exception in posting instagram image: {e}")
            most_recent_post_ins_ids = self.get_most_recent_posted_ins_ids()
            if (
                len(most_recent_post_ins_ids) == 0
                or len(most_recent_post_ins_ids_before_post) == 0
            ):
                error(
                    f"ERROR when fetching most recent posts: most_recent_post_ins_ids: {most_recent_post_ins_ids}, most_recent_posted_ins_id_before_post: {most_recent_post_ins_ids_before_post}"
                )
                continue
            most_recent_post_ins_id = most_recent_post_ins_ids[0]
            most_recent_post_ins_id_before_post = most_recent_post_ins_ids_before_post[
                0
            ]
            info(
                f"most_recent_post_ins_id: {most_recent_post_ins_id}, most_recent_post_ins_id_before_post: {most_recent_post_ins_id_before_post}"
            )
            if most_recent_post_ins_id != most_recent_post_ins_id_before_post:
                publish_count += 1
                try:
                    info(
                        f"New post id: {most_recent_post_ins_id}, news_url: {candidate.news_url}"
                    )
                    link_conmment_content = f"News Source:\n{candidate.news_url}"
                    comment_result = self.client.media_comment(
                        most_recent_post_ins_id, link_conmment_content
                    )
                    info(
                        f"Commented link: {candidate.news_url} comment_result: {comment_result}"
                    )
                except Exception as e:
                    error(f"Exception in commenting link: {e}")

            if publish_count >= publish_limit:
                break
            time.sleep(
                random.randint(20, 30)
            )  # sleep for 20-30 seconds between each post to avoid instagram ban

    def publish_image_story(
        self, publish_candidates: List[InstagramPostCandidate], publish_limit=1
    ):
        my_stories = self.client.user_stories(self.client.user_id)
        if len(my_stories) >= 4:
            info("Skip publishing image story since there are already 2 stories")
            return
        published_story_count = 0
        for candidate in publish_candidates:
            if candidate.story_image_path is None:
                continue
            posted_with_link = False
            try:
                links = [StoryLink(webUri=candidate.news_url)]
                self.client.photo_upload_to_story(
                    candidate.story_image_path, links=links
                )
                published_story_count += 1
                posted_with_link = True
            except Exception as e:
                if (
                    "feedback_required: We restrict certain activity to protect our community"
                    in str(e)
                ):
                    info(f"Published instagram story: {candidate.story_image_path}")
                    published_story_count += 1
                error(f"Exception in publishing instagram story: {e}")
            if not posted_with_link:
                try:
                    error(
                        f"Posting instagram story without link failed: {candidate.story_image_path}, url: {candidate.news_url}. Post without link instead."
                    )
                    self.client.photo_upload_to_story(candidate.story_image_path)
                    published_story_count += 1
                except Exception as e:
                    if (
                        "feedback_required: We restrict certain activity to protect our community"
                        in str(e)
                    ):
                        info(f"Published instagram story: {candidate.story_image_path}")
                        published_story_count += 1
                    error(f"Exception in publishing instagram story: {e}")
                    raise e
            if published_story_count >= publish_limit:
                break
            time.sleep(
                random.randint(20, 30)
            )  # sleep for 20-30 seconds between each post to avoid instagram ban

    def get_most_similar_posted_ins_and_similarity_score(self, content: str):
        user_id = self.client.user_id
        most_similar_post = None
        most_similar_post_similarity_score = 0
        medias = self.client.user_medias(user_id, amount=20)
        for media in medias:
            caption_text = media.caption_text
            if caption_text is None or len(caption_text) < 10:
                continue
            try:
                similarity = (
                    TextEmbeddingCache.get_instance().get_text_similarity_score(
                        content, caption_text
                    )
                )
                if similarity > most_similar_post_similarity_score:
                    most_similar_post_similarity_score = similarity
                    most_similar_post = caption_text
            except Exception as e:
                error(
                    f"Exception in getting similarity score between media({media.pk}). caption_text: {caption_text} and content: {content}. Error:{e}."
                )
        return most_similar_post, most_similar_post_similarity_score

    def get_most_recent_posted_ins_ids(self, user_id=None):
        if not user_id:
            user_id = self.client.user_id
        medias = self.client.user_medias(user_id, amount=20)
        medias = sorted(medias, key=lambda x: x.pk, reverse=True)
        return [media.pk for media in medias]

    def dm_influencers(self, seed_query, total_users_to_reach=10):
        matched_users = self.client.search_users(
            seed_query
        )  # normally 20 will be returned
        info(
            f"dm_influencers: Matched users: {len(matched_users)} for query: {seed_query}"
        )
        user_ids_reached = []
        visited_influencers_dict = get_visited_influencer_id_dict(
            InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto
        )
        for user in matched_users:
            if user.pk in visited_influencers_dict:
                info(f"Skip reaching out visited user: {user.username}")
                continue
            dm_message_1 = f"Hey {user.full_name}, as an official partner with BingX, we're excited to extend an exclusive offer: [40% discount on crypto trading fee at BingX].\nThe offer is automatically applied when you sign up using the link below:\n\nhttps://bingx.com/en-us/invite/MUPZYNVN"
            dm_message_2 = f"To be completely transparent on how this works, you'll receive 40% commission rebate in USDT every day, we'll receive a modest 2.5% service fee from BingX.\nWe also offer other incentive programs for qualified crypto traders or influencers. Feel free to reply if you have any questions.\nLooking forward to connecting!\n - the Crypto News Pulse operation team"
            bingx_photo_path = os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "static",
                "bingx_en.jpg",
            )
            try:
                self.client.direct_send(dm_message_1, [user.pk])
                time.sleep(random.randint(15, 20))
                self.client.direct_send_photo(bingx_photo_path, [user.pk])
                time.sleep(random.randint(15, 20))
                self.client.direct_send(dm_message_2, [user.pk])
                info(f"Sent DM to user: {user.username}({user.pk})")
                user_ids_reached.append(user.pk)
                add_visited_influencer_id(
                    InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto,
                    user.pk,
                )
                time.sleep(random.randint(15, 20))
            except Exception as e:
                error(f"Exception in sending DM to user: {e}")
                continue
            if len(user_ids_reached) >= total_users_to_reach:
                break
        info(f"Total influencer reached: {len(user_ids_reached)}")
        return user_ids_reached

    def comment_media_from_searched_users(self, seed_search_query, comment_text):
        matched_users = self.client.search_users(
            seed_search_query
        )  # normally 20 will be returned
        info(f"Matched users: {len(matched_users)} for query: {seed_search_query}")
        total_users_to_reach = 10
        total_posts_to_comment_per_user = 2
        total_users_reached = 0
        total_posts_commented = 0
        for user in matched_users:
            recent_posts = self.client.user_medias(
                user.pk, amount=total_posts_to_comment_per_user
            )
            info(
                f"  Recent posts: {len(recent_posts)} for user: {user.username}({user.pk})"
            )
            total_posts_commented_for_current_user = 0
            for post in recent_posts:
                try:
                    self.client.media_like(post.pk)
                    info(
                        f"Liked post: {post.caption_text} from user: {user.username}({user.pk})"
                    )
                    time.sleep(random.randint(10, 12))
                    post_caption_text = post.caption_text.replace("\n", " ").strip()
                    conmment_content = f"🔥 Breaking News Just In 🔥 - {comment_text}\n{self.comment_text_suffix}"
                    self.client.media_comment(post.pk, conmment_content)
                    time.sleep(random.randint(10, 12))
                    total_posts_commented_for_current_user += 1
                    total_posts_commented += 1
                    info(
                        f"Commented post: {post_caption_text} from user: {user.username}({user.pk}) current user total posts commented: {total_posts_commented_for_current_user}, total posts commented: {total_posts_commented}"
                    )
                except Exception as e:
                    error(f"Exception during commenting post: {e}")
                    if "login_required" in str(e):
                        error("Instagram login required during liking and commenting")
                        self.login_user()
                if (
                    total_posts_commented_for_current_user
                    >= total_posts_to_comment_per_user
                ):
                    break
            total_users_reached += 1
            info(
                f"Finished commenting on user: {user.username}({user.pk}). total users reached: {total_users_reached}. total posts commented: {total_posts_commented}"
            )
            if total_users_reached >= total_users_to_reach:
                break
        info(f"Total comment reached: {total_posts_commented}")

    def get_commenter_user_ids(self, poster_user_id) -> set[str]:
        post_amount = 20
        user_medias = self.client.user_medias(poster_user_id, amount=post_amount)
        commenter_ids = set()
        for media in user_medias:
            comments = self.client.media_comments(media.pk)
            for comment in comments:
                commenter_ids.add(comment.user.pk)
        info(f"{len(commenter_ids)} commenter ids fetched from {poster_user_id}")
        return commenter_ids

    def get_non_private_influencers(self, seed_query) -> List:
        search_users_result = self.client.search_users_v1(seed_query, count=200)
        non_private_users = [u for u in search_users_result if not u.is_private]
        return non_private_users

    def get_follower_ids(self, user_name, amount=200) -> Dict:
        user_id = self.client.user_id_from_username(user_name)
        followers = self.client.user_followers(user_id, amount=amount)
        return followers

    def reach_out_to_influencers(self, seed_query, limit=10):
        non_private_users = self.get_non_private_influencers(seed_query)
        info(f"Non private users: {len(non_private_users)}")
        total_users_reached = 0
        for user in non_private_users:
            dm_sent = False
            try:
                self.client.direct_send("TESTING MESSAGE!", [user.pk])
                info(f"Sent DM to user: {user.username}({user.pk})")
                total_users_reached += 1
                dm_sent = True
            except Exception as e:
                error(f"Exception in sending DM to user: {e}")
                if "login_required" in str(e):
                    error("Instagram login required during sending DM")
                    self.login_user()
            if not dm_sent:
                continue
            recent_posts = self.client.user_medias(user.pk, amount=2)
            dm_reminder_posted = 0
            for post in recent_posts:
                try:
                    time.sleep(random.randint(10, 12))
                    conmment_content = f"🔥 test comment 🔥"
                    self.client.media_comment(post.pk, conmment_content)
                    time.sleep(random.randint(10, 12))
                    info(f"Commented DM reminder for user: {user.username}({user.pk})")
                    dm_reminder_posted += 1
                except Exception as e:
                    error(f"Exception during commenting post: {e}")
                    if "login_required" in str(e):
                        error("Instagram login required during liking and commenting")
                        self.login_user()
            info(
                f"DM reminder posted for user: {user.username}({user.pk}) - {dm_reminder_posted}"
            )
            if total_users_reached >= limit:
                break
        info(f"Total users reached: {total_users_reached}")


if __name__ == "__main__":
    # res = requests.get("https://proxy.webshare.io/api/v2/proxy/list/?mode=direct&page=1&page_size=25", headers={
    #     "Authorization": "Token "}).text
    # list = json.loads(res)
    # ips = []
    # for result in list['results']:
    #     ip = f"{result['proxy_address']}:{str(result['port'])}"
    #     ips.append(ip)
    # print(ips)
    # ip = requests.get(
    #     "https://ipv4.webshare.io/",
    #     proxies={
    #         "http": "http://niqgiyim-rotate:1fslh9b34rss@p.webshare.io:80/",
    #         "https": "http://niqgiyim-rotate:1fslh9b34rss@p.webshare.io:80/"
    #     }
    # ).text
    # print(ip)
    apiManager = InstagramAPIManager(
        InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeOther,
        "58pjoy1f",
        "HgMHufzr",
    )
    user_id = apiManager.client.user_id_from_username("crypto_news_pulse")
    post_ids = apiManager.get_most_recent_posted_ins_ids(user_id)
    print(post_ids)

    # apiManager.publish_image_story(
    #     '/Users/chengjiang/Dev/NewsBite/data/fintech_1690581671.jpg', 'crypto_news_pulse')
    # links = [StoryLink(
    #     webUri='https://ambcrypto.com/how-azukis-attempt-at-recouping-plunged-prices-instead')]
    # apiManager.client.photo_upload_to_story(
    #     '/Users/chengjiang/Dev/NewsBite/data/fintech_1690581671.jpg', links=links)

    # id1 = apiManager.client.user_id_from_username('jaycee.1214')
    # id2 = apiManager.client.user_id_from_username('crypto_news_pulse')
    # id3 = apiManager.client.user_id_from_username('fintech_news_pulse')
    # print(id3)
    # commenter_user_ids = apiManager.get_commenter_user_ids(id2)
    # for commenter_user_id in commenter_user_ids:
    #     print(apiManager.client.username_from_user_id(commenter_user_id))
    # un = apiManager.client.username_from_user_id('57783781091')
    # print(un)
    # info1 = apiManager.client.user_info('57783781091')
    # info2 = apiManager.client.user_info('60853548164')
    # msg = apiManager.client.direct_send(
    #     "hi", [id1, id2])
    # msg = apiManager.client.direct_send(
    #     '🔥 Fresh crypto currency news updates help you make right quality decisions! 🔥\n @crypto_news_pulse <<< Follow to stay updated!', ['545357425',  '57783781091'])  # bad: '57783781091', '35830230157', '8788712384' good: '60853548164' '53120050', '8788712384'
    # info(msg)
    # thread_id = msg.thread_id
    # user_ids = [57783781091, 35830230157,
    #             60853548164, 53120050, 8788712384, id3]
    # for user_id in user_ids:
    #     success = apiManager.client.add_users_to_direct_thread(
    #         thread_id=thread_id, user_ids=[user_id])
    #     info(f'{user_id} - {success}')
    # apiManager.client.direct_send(
    #     '🔥 Fresh crypto currency news updates help you make right quality decisions! 🔥\n @crypto_news_pulse <<< Follow to stay updated!', thread_ids=[thread_id])
    # followers = apiManager.get_followers('bitboy_crypto')
    # print(len(followers))
    # for k in followers.keys():
    #     f = followers[k]
    #     print(f'{k} - {f.username}')
    # crypto_trader_query = 'crypto trader'
    # trader_users = apiManager.get_influencers(crypto_trader_query)
    # print(len(trader_users))
    # apiManager.reach_out_to_influencers('jaycee.1214', limit=1)

    # apiManager.like_and_comment_media('bitcoin')

    # apiManager = InstagramAPIManager(
    #     InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeFintech)
    # apiManager.like_and_comment_media('stock')

# media = cl.photo_upload(
#     "/Users/chengjiang/Dev/NewsBite/poster.jpg",
#     "Get ready for a bumpy ride ahead with inflation! The annual U.S. CPI rate is benefiting from \'base effects\'. Shelter costs make up a third of the CPI. In the last six months, the monthly rate has been around 0.25%, or over 3% annualized.",
#     extra_data={
#         "custom_accessibility_caption": "alt text example",
#         "like_and_view_counts_disabled": 1,
#         "disable_comments": 1,
#     }
# )
