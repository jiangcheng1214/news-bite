import json
import time
import os
from utils.TextEmbeddingCache import TextEmbeddingCache
from twitter.TwitterAPIManager import TwitterPostCandidate
from utils.Logging import error, info, warn
from threads import Threads
from enum import Enum
from typing import List
from utils.Constants import THREADS_SIMILARITY_CHECK_COVERAGE_IN_SEC, THREADS_DEFAULT_POST_LIMIT, THREADS_SIMILARITY_FOR_POSTING_GUARD_THRESHOLD, THREADS_SIMILARITY_FOR_REPLY
from dotenv import load_dotenv
load_dotenv()


class ThreadsAPIManagerAccountType(Enum):
    ThreadsAPIManagerAccountTypeCrypto = 0
    ThreadsAPIManagerAccountTypeFintech = 1


class ThreadsAPIManager:
    def __init__(self, accountType: ThreadsAPIManagerAccountType):
        if accountType == ThreadsAPIManagerAccountType.ThreadsAPIManagerAccountTypeCrypto:
            INSTAGRAM_USERNAME = os.environ.get('THREADS_CRYPTO_USER_NAME')
            INSTAGRAM_PASSWORD = os.environ.get('THREADS_CRYPTO_PASSWORD')
            self.api = Threads(username=INSTAGRAM_USERNAME,
                               password=INSTAGRAM_PASSWORD)
        elif accountType == ThreadsAPIManagerAccountType.ThreadsAPIManagerAccountTypeFintech:
            INSTAGRAM_USERNAME = os.environ.get('THREADS_FINTECH_USER_NAME')
            INSTAGRAM_PASSWORD = os.environ.get('THREADS_FINTECH_PASSWORD')
            self.api = Threads(username=INSTAGRAM_USERNAME,
                               password=INSTAGRAM_PASSWORD)
        else:
            raise Exception("Invalid account type")
        self.user_id = self.api.private_api.user_id
        self.private_api = self.api.private_api
        self.public_api = self.api.public_api

    def get_recent_posted_threads(self, retry=False) -> List:
        try:
            recent_posted_threads_items = self.public_api.get_user_threads(
                id=self.user_id)['data']['mediaData']['threads']
        except Exception as e:
            if retry:
                error("Error getting posted thread: " + str(e))
                return []
            else:
                time.sleep(10)
                return self.get_recent_posted_threads(retry=True)
        recent_posted_threads = []
        for t in recent_posted_threads_items[:200]:  # check up to 200 threads
            try:
                thread_items = t['thread_items']
                if len(thread_items) > 1:
                    warn("Thread has more than 1 item. Only read first item")
                if len(thread_items) == 0:
                    warn("Thread has no item")
                    continue
                thread_item_posted = thread_items[0]['post']
                created_at = thread_item_posted['taken_at']
                second_since_created = int(
                    time.time() - created_at)
                if second_since_created > THREADS_SIMILARITY_CHECK_COVERAGE_IN_SEC:
                    continue
                caption = thread_item_posted['caption']['text']
                id = t['id']
                recent_posted_threads.append([caption, id])
            except Exception as e:
                if retry:
                    error(
                        f"Error getting posted thread: {str(e)}. {json.dumps(t)}")
                    continue
        return recent_posted_threads

    def compose_thread(self, content: str, hashtags: str or List[str]):
        t_content = content
        hashtag_list = []
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

        # Compose hashtags
        hashtags_string = ''
        while len(clean_hashtags) > 0:
            tag = clean_hashtags.pop()
            if not tag or len(tag) <= 2:
                continue
            if t_content.find(tag) != -1:
                continue
            hashtags_string = f'{hashtags_string} {tag}'.strip()

        # Compose thread content
        if hashtags_string:
            t_content = f'{t_content}\n\n{hashtags_string}'

        return t_content

    def get_most_similar_posted_thread_id_and_similarity_score(self, content, recent_posted_thread_contents=None):
        if not recent_posted_thread_contents:
            recent_posted_thread_contents = self.get_recent_posted_threads()
        most_similar_post_id = None
        most_similar_post_similarity_score = 0
        for recent_post in recent_posted_thread_contents:
            recent_post_content = recent_post[0].replace(
                '\n', ' ')
            similarity = TextEmbeddingCache.get_instance().get_text_similarity_score(
                content, recent_post_content)
            if similarity > most_similar_post_similarity_score:
                most_similar_post_similarity_score = similarity
                most_similar_post_id = recent_post[1]
        return most_similar_post_id, most_similar_post_similarity_score

    def post_threads(self, candidates: List[TwitterPostCandidate], post_limit: int = THREADS_DEFAULT_POST_LIMIT):
        if len(candidates) == 0:
            return
        post_count = 0
        composed_threads = []
        recent_posted_threads = self.get_recent_posted_threads()
        if len(recent_posted_threads) == 0:
            warn('No recent posted thread found')
        for c in candidates:
            composed_thread = self.compose_thread(c.news_content, c.hashtags)
            similar_id, similar_score = self.get_most_similar_posted_thread_id_and_similarity_score(
                c.news_content, recent_posted_threads)
            composed_threads.append(
                (composed_thread, c.is_video, c.news_url, similar_id, similar_score))

        for (thread_content, is_video, news_url, most_similar_id, most_similar_score) in composed_threads:
            try:
                if not is_video and most_similar_score > THREADS_SIMILARITY_FOR_POSTING_GUARD_THRESHOLD:
                    warn(
                        f'Thread is too similar to a recently posted thread, similarity: {most_similar_score}. recent_post_id: {most_similar_id}')
                    continue
                elif most_similar_score > THREADS_SIMILARITY_FOR_REPLY:
                    self.private_api.create_thread(
                        caption=thread_content, url=news_url, reply_to=most_similar_id)
                    info(
                        f'Thread posted with reply id ({most_similar_score}): {most_similar_id} - {thread_content}')
                    post_count += 1
                else:
                    self.private_api.create_thread(
                        caption=thread_content, url=news_url)
                    info(f'Thread posted: {thread_content}')
                    post_count += 1
            except Exception as e:
                error("Error posting Thread: " + str(e))
                continue
            if post_count >= post_limit:
                break
        info(f'Posted {post_count} Threads')
        return post_count


if __name__ == '__main__':
    pass
    # apiManager = ThreadsAPIManager(
    #     ThreadsAPIManagerAccountType.TwitterAPIManagerAccountTypeCrypto)

    # created_thread = apiManager.private_api.create_thread(
    #     caption='Crypto crime has dropped by 65% through the end of June this year, as compared to the same period in 2022. However, the same cannot be said about ransomware attacks.',
    #     url='https://ambcrypto.com/crypto-crime-drops-significantly-in-2023-but-its-not-all-good-news/'
    # )

    # print(json.dumps(created_thread, indent=4))
    # created_thread = threads.private_api.create_thread(
    #     caption='Hello, world!',
    #     url='https://www.youtube.com/watch?v=lc4qU6BakvE'
    # )

    # created_thread = threads.private_api.create_thread(
    #     caption='Hello, world!',
    #     image_url='https://raw.githubusercontent.com/dmytrostriletskyi/threads-net/main/assets/picture.png',
    # )

    # created_thread = threads.private_api.create_thread(
    #     caption='Hello, world!',
    #     image_url='/Users/dmytrostriletskyi/projects/threads/assets/picture.png',
    # )

    # created_thread = threads.private_api.create_thread(
    #     caption='Hello, world!',
    #     image_url='https://raw.githubusercontent.com/dmytrostriletskyi/threads-net/main/assets/picture.png',
    #     reply_to=3141055616164096839,
    # )

    # user_id = apiManager.private_api.get_user_id(username='crypto_news_pulse')
    # print(user_id)
    # user = apiManager.private_api.get_user(id=user_id)
    # print(json.dumps(user, indent=4))
    # posted_threads = apiManager.public_api.get_user_threads(id=user_id)
    # print(json.dumps(posted_threads, indent=4))
