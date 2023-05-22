import json
import numpy as np
import openai
import redis
import os
import time
from dotenv import load_dotenv
from utils.Utilities import MINIMAL_OPENAI_API_CALL_INTERVAL_SEC, DEFAULT_REDIS_CACHE_EXPIRE_SEC, OpenaiModelVersion, REDIS_TWEET_EMBEDDING_DICT_KEY, get_clean_text
from utils.Logging import info, warn
from openAI.OpenaiGptApiManager import OpenaiGptApiManager
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


class TweetSummaryEnricher():
    def __init__(self, sources=[]):
        self.sources = sources
        self.last_request_time = None  # error_code=None error_message='Rate limit reached for default-global-with-image-limits in organization org-mJUMNPeqLz41mk3VvrEAqOMV on requests per min. Limit: 60 / min. Please try again in 1s. Contact support@openai.com if you continue to have issues. Please add a payment method to your account to increase your rate limit. Visit https://platform.openai.com/account/billing to add a payment method.' error_param=None error_type=requests message='OpenAI API error received' stream_error=False
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.openaiApiManager = OpenaiGptApiManager(
            OpenaiModelVersion.GPT3_5.value)
        self.embedding_dict = self.redis_client.get(
            REDIS_TWEET_EMBEDDING_DICT_KEY)
        if self.embedding_dict is None:
            self.embedding_dict = {}
        else:
            self.embedding_dict = json.loads(self.embedding_dict)

    def find_best_match_and_score(self, target_sentence):
        best_score = 0
        best_match = ""
        for source in self.sources:
            similarity = self.get_similarity(source, target_sentence)
            if similarity > best_score:
                best_score = similarity
                best_match = source
        return best_match, best_score

    def get_similarity(self, text1, text2):
        embedding1 = self.get_text_embedding(text1)
        embedding2 = self.get_text_embedding(text2)
        similarity = np.dot(embedding1, embedding2)
        return similarity

    def get_text_embedding(self, text: str):
        if len(text) > 300:
            warn(f"Text length {len(text)} is longer than 300 chars")
        clean_text = get_clean_text(text)
        if text in self.embedding_dict:
            return self.embedding_dict[clean_text]
        if self.last_request_time:
            time_elapsed = time.time() - self.last_request_time
            if time_elapsed < MINIMAL_OPENAI_API_CALL_INTERVAL_SEC:
                time.sleep(
                    MINIMAL_OPENAI_API_CALL_INTERVAL_SEC - time_elapsed)
        embedding = self.openaiApiManager.get_embedding(clean_text)
        self.last_request_time = time.time()
        self.embedding_dict[clean_text] = embedding
        self.redis_client.set(REDIS_TWEET_EMBEDDING_DICT_KEY,
                              json.dumps(self.embedding_dict), ex=DEFAULT_REDIS_CACHE_EXPIRE_SEC)
        info(f"{text} cached. embedding_dict length: {len(self.embedding_dict)}")
        return self.embedding_dict[clean_text]
