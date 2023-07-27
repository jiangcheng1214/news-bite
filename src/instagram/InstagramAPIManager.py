import json
import random
import time
from utils.Constants import PAST_DM_USER_IDS_REDIS_KEY_CRYPTO, PAST_VISITED_INFLUENCER_IDS_REDIS_KEY_CRYPTO, TODO_DM_USER_IDS_REDIS_KEY_CRYPTO
from utils.RedisClient import RedisClient
from utils.Logging import error, info, warn
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, UnknownError
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
    assert accountType == InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto
    past_dm_user_ids_str = RedisClient.shared().get(
        PAST_DM_USER_IDS_REDIS_KEY_CRYPTO)
    if past_dm_user_ids_str:
        past_dm_user_ids = set(json.loads(past_dm_user_ids_str))
    else:
        past_dm_user_ids = set()
    return past_dm_user_ids


def record_dm_user_ids(accountType: InstagramAPIManagerAccountType, user_ids: List[str]):
    assert accountType == InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto
    past_dm_user_ids = get_past_dm_user_ids(accountType)
    past_dm_user_ids.update(user_ids)
    past_dm_user_ids = list(past_dm_user_ids)
    RedisClient.shared().set(PAST_DM_USER_IDS_REDIS_KEY_CRYPTO,
                             json.dumps(past_dm_user_ids), ex=60*60*24*7)

def get_past_visited_influencer_ids(accountType: InstagramAPIManagerAccountType) -> set[str]:
    assert accountType == InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto
    past_visited_influencer_ids_str = RedisClient.shared().get(
        PAST_VISITED_INFLUENCER_IDS_REDIS_KEY_CRYPTO)
    if past_visited_influencer_ids_str:
        past_visited_influencer_ids = set(
            json.loads(past_visited_influencer_ids_str))
    else:
        past_visited_influencer_ids = set()
    return past_visited_influencer_ids


def record_visited_influencer_id(accountType: InstagramAPIManagerAccountType, influencer_id: str):
    assert accountType == InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto
    past_visited_influencer_ids = get_past_visited_influencer_ids(accountType)
    past_visited_influencer_ids.add(influencer_id)
    past_visited_influencer_ids = list(past_visited_influencer_ids)
    RedisClient.shared().set(PAST_VISITED_INFLUENCER_IDS_REDIS_KEY_CRYPTO,
                             json.dumps(past_visited_influencer_ids), ex=60*60*24*7)


def get_todo_dm_user_ids(accountType: InstagramAPIManagerAccountType) -> set[str]:
    assert accountType == InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto
    todo_dm_user_ids_str = RedisClient.shared().get(
        TODO_DM_USER_IDS_REDIS_KEY_CRYPTO)
    if todo_dm_user_ids_str:
        todo_dm_user_ids = set(json.loads(todo_dm_user_ids_str))
    else:
        todo_dm_user_ids = set()
    return todo_dm_user_ids


def set_todo_dm_user_ids(accountType: InstagramAPIManagerAccountType, user_ids: set[str]):
    assert accountType == InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto
    RedisClient.shared().set(TODO_DM_USER_IDS_REDIS_KEY_CRYPTO,
                             json.dumps(list(user_ids)), ex=60*60*24*7)


class InstagramAPIManager:
    def __init__(self, accountType: InstagramAPIManagerAccountType, username=None, password=None, force_login=False):
        self.accountType = accountType
        self.posterGenerator = PosterGenerator()
        self.client = Client()
        self.client.delay_range = [0.5, 1.5]
        if accountType == InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto:
            self.username = os.environ.get('THREADS_CRYPTO_USER_NAME')
            self.password = os.environ.get('THREADS_CRYPTO_PASSWORD')
            self.session_path = os.path.join(os.path.dirname(
                __file__), '..', '..', 'cache', f'instagram_session_crypto.json')
            self.hashtag_appending = '#crypto #cryptocurrency #btc #bitcoin #passiveincome #eth #marketsentiment #cryptonews'
            self.comment_text_suffix = '🙌 Latest crypto updates and sentimental news. #MissNoMore 🙌'
        elif accountType == InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeFintech:
            self.username = os.environ.get('THREADS_FINTECH_USER_NAME')
            self.password = os.environ.get('THREADS_FINTECH_PASSWORD')
            self.session_path = os.path.join(os.path.dirname(
                __file__), '..', '..', 'cache', f'instagram_session_fintech.json')
            self.hashtag_appending = '#financialnews #technews #quant #marketsentiment #passiveincome #stockmarket #marketindicator #fintech'
            self.comment_text_suffix = '🙌 Latest financial / tech updates and sentimental news. #MissNoMore 🙌'
        else:
            assert accountType == InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeOther
            self.username = username
            self.password = password
            self.session_path = os.path.join(os.path.dirname(
                __file__), '..', '..', 'cache', f'instagram_session_{self.username}.json')
        self.login_user(force_login=force_login)

    def login_user(self, force_login=False):
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
                info(
                    f'Attempting to login via username and password. username: {username}')
                if self.client.login(username, password):
                    login_via_pw = True
                    self.client.dump_settings(self.session_path)
            except Exception as e:
                info("Couldn't login user using username and password: %s" % e)

        if not login_via_pw and not login_via_session:
            raise Exception(
                "Couldn't login user with either password or session")

    def generate_poster(self, text, image_url, sentiment):
        timestamp = int(time.time())
        prefix = 'crypto' if self.accountType == InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto else 'fintech'
        output_path = os.path.join(os.path.dirname(
            __file__), '..', '..', 'data', f'{prefix}_{timestamp}.jpg')
        try:
            info(
                f"Generating poster for instagram post: {text} - {output_path}")
            self.posterGenerator.generate_poster(
                text, image_url, sentiment, output_path)
        except Exception as e:
            error(f"Exception in generating poster: {e}")
        if os.path.exists(output_path):
            return output_path
        else:
            return None

    def post_image(self, candidates, post_limit=1):
        posted_count = 0
        for candidate in candidates:
            content = candidate.news_content
            image_url = candidate.image_url
            hashtags = candidate.hashtags
            if type(hashtags) == list:
                hashtag_list = hashtags
            elif type(hashtags) == str:
                hashtag_list = hashtags.split(',')
                clean_hashtags = []
                for h in hashtag_list:
                    tag = h.strip().replace('-', '').replace('.', '').replace('@', '').replace('/', '')
                    if not tag.startswith('#'):
                        clean_hashtags.append(f"#{tag}")
                    else:
                        clean_hashtags.append(tag)
                hashtag_list = clean_hashtags
            hashtag_string = ' '.join(hashtag_list).strip()
            if content.endswith(hashtag_string):
                content = content[:-len(hashtag_string)].strip()
            content_with_hashtags = f"{content}\n{hashtag_string}\n{self.hashtag_appending}"
            most_similar_post, most_similar_post_similarity_score = self.get_most_similar_posted_ins_and_similarity_score(
                content)
            if most_similar_post_similarity_score > 0.9:
                info(
                    f"Skip posting: {content}. Most similar post similarity score: {most_similar_post_similarity_score} - {most_similar_post}")
                continue
            image_path = self.generate_poster(
                content, image_url, candidate.sentiment)
            if image_path is None:
                error(f"Failed to generate poster for {content}")
                continue
            try:
                self.client.photo_upload(
                    image_path,
                    content_with_hashtags
                )
                info(f"Posted instagram image: {image_path}")
                posted_count += 1
            except Exception as e:
                if 'feedback_required: We restrict certain activity to protect our community' in str(e):
                    info(f"Posted instagram image: {image_path}")
                    posted_count += 1
                else:
                    error(f"Exception in posting instagram image: {e}")
            finally:
                if posted_count >= post_limit:
                    break

    def get_most_similar_posted_ins_and_similarity_score(self, content: str):
        user_id = self.client.user_id
        most_similar_post = None
        most_similar_post_similarity_score = 0
        medias = self.client.user_medias(user_id, amount=20)
        for media in medias:
            caption_text = media.caption_text
            similarity = TextEmbeddingCache.get_instance().get_text_similarity_score(
                content, caption_text)
            if similarity > most_similar_post_similarity_score:
                most_similar_post_similarity_score = similarity
                most_similar_post = caption_text
        return most_similar_post, most_similar_post_similarity_score

    def comment_media_from_searched_users(self, seed_search_query, comment_text, like_limit=20):
        matched_users = self.client.search_users(
            seed_search_query)  # normally 20 will be returned
        info(
            f"Matched users: {len(matched_users)} for query: {seed_search_query}")
        total_users_to_reach = 10
        total_posts_to_comment_per_user = 2
        total_users_reached = 0
        total_posts_commented = 0
        for user in matched_users:
            recent_posts = self.client.user_medias(
                user.pk, amount=total_posts_to_comment_per_user)
            info(
                f"  Recent posts: {len(recent_posts)} for user: {user.username}({user.pk})")
            total_posts_commented_for_current_user = 0
            for post in recent_posts:
                try:
                    self.client.media_like(post.pk)
                    info(
                        f'Liked post: {post.caption_text} from user: {user.username}({user.pk})')
                    time.sleep(random.randint(10, 12))
                    post_caption_text = post.caption_text.replace(
                        '\n', ' ').strip()
                    conmment_content = f"🔥 Breaking News Just In 🔥 - {comment_text}\n{self.comment_text_suffix}"
                    self.client.media_comment(post.pk, conmment_content)
                    time.sleep(random.randint(10, 12))
                    total_posts_commented_for_current_user += 1
                    total_posts_commented += 1
                    info(
                        f'Commented post: {post_caption_text} from user: {user.username}({user.pk}) current user total posts commented: {total_posts_commented_for_current_user}, total posts commented: {total_posts_commented}')
                except Exception as e:
                    error(f"Exception during commenting post: {e}")
                    if 'login_required' in str(e):
                        error("Instagram login required during liking and commenting")
                        self.login_user()
                if total_posts_commented_for_current_user >= total_posts_to_comment_per_user:
                    break
            total_users_reached += 1
            info(
                f"Finished commenting on user: {user.username}({user.pk}). total users reached: {total_users_reached}. total posts commented: {total_posts_commented}")
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
        search_users_result = self.client.search_users_v1(
            seed_query, count=200)
        non_private_users = [
            u for u in search_users_result if not u.is_private]
        return non_private_users

    def get_follower_ids(self, user_name, ammount=200) -> Dict:
        user_id = self.client.user_id_from_username(user_name)
        followers = self.client.user_followers(user_id, amount=ammount)
        return followers

    def reach_out_to_influencers(self, seed_query, limit=10):
        non_private_users = self.get_non_private_influencers(seed_query)
        info(f"Non private users: {len(non_private_users)}")
        total_users_reached = 0
        for user in non_private_users:
            dm_sent = False
            try:
                self.client.direct_send('TESTING MESSAGE!', [user.pk])
                info(f"Sent DM to user: {user.username}({user.pk})")
                total_users_reached += 1
                dm_sent = True
            except Exception as e:
                error(f"Exception in sending DM to user: {e}")
                if 'login_required' in str(e):
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
                    info(
                        f'Commented DM reminder for user: {user.username}({user.pk})')
                    dm_reminder_posted += 1
                except Exception as e:
                    error(f"Exception during commenting post: {e}")
                    if 'login_required' in str(e):
                        error("Instagram login required during liking and commenting")
                        self.login_user()
            info(
                f"DM reminder posted for user: {user.username}({user.pk}) - {dm_reminder_posted}")
            if total_users_reached >= limit:
                break
        info(f"Total users reached: {total_users_reached}")


if __name__ == "__main__":
    apiManager = InstagramAPIManager(
        InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeOther, 'zlvlpukyz1', 'PtHDQcMq')

    # id1 = apiManager.client.user_id_from_username('jaycee.1214')
    # id2 = apiManager.client.user_id_from_username('crypto_news_pulse')
    id3 = apiManager.client.user_id_from_username('fintech_news_pulse')
    print(id3)
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
