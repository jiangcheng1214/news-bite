import time
from utils.Logging import error, info, warn
from instagrapi import Client
from instagrapi.exceptions import LoginRequired
from enum import Enum
from typing import List
import os
from dotenv import load_dotenv
from posterGeneration.PosterGenerator import PosterGenerator
from utils.TextEmbeddingCache import TextEmbeddingCache
load_dotenv()


class InstagramAPIManagerAccountType(Enum):
    InstagramAPIManagerAccountTypeCrypto = 0
    InstagramAPIManagerAccountTypeFintech = 1


class InstagramAPIManager:
    def __init__(self, accountType: InstagramAPIManagerAccountType):
        self.accountType = accountType
        self.posterGenerator = PosterGenerator()
        self.client = Client()
        self.client.delay_range = [1, 3]
        if accountType == InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto:
            self.username = os.environ.get('THREADS_CRYPTO_USER_NAME')
            self.password = os.environ.get('THREADS_CRYPTO_PASSWORD')
            self.session_path = os.path.join(os.path.dirname(
                __file__), '..', '..', 'cache', f'instagram_session_crypto.json')
            self.hashtag_appending = '#crypto #cryptocurrency #btc #bitcoin #passiveincome #eth #marketsentiment #cryptonews'
        elif accountType == InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeFintech:
            self.username = os.environ.get('THREADS_FINTECH_USER_NAME')
            self.password = os.environ.get('THREADS_FINTECH_PASSWORD')
            self.session_path = os.path.join(os.path.dirname(
                __file__), '..', '..', 'cache', f'instagram_session_fintech.json')
            self.hashtag_appending = '#financialnews #technews #quant #marketsentiment #passiveincome #stockmarket #marketindicator #fintech'
        else:
            raise Exception("Invalid account type")
        self.login_user()

    def login_user(self):
        username, password = self.username, self.password
        session = None
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

    def search(self, query):
        return self.client.direct_search(query)


if __name__ == "__main__":
    apiManager = InstagramAPIManager(
        InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto)
    # apiManager.post_image('/Users/chengjiang/Dev/NewsBite/data/crypto_post_candidate_1689670375.jpg',
    #                       'Coinbase CEO Brian Armstrong to meet with House Democrats to discuss crypto legislation. #Coinbase #crypto #legislation')
    # apiManager.get_most_similar_posted_ins_and_similarity_score()
    print(apiManager.search('fin'))

# media = cl.photo_upload(
#     "/Users/chengjiang/Dev/NewsBite/poster.jpg",
#     "Get ready for a bumpy ride ahead with inflation! The annual U.S. CPI rate is benefiting from \'base effects\'. Shelter costs make up a third of the CPI. In the last six months, the monthly rate has been around 0.25%, or over 3% annualized.",
#     extra_data={
#         "custom_accessibility_caption": "alt text example",
#         "like_and_view_counts_disabled": 1,
#         "disable_comments": 1,
#     }
# )
