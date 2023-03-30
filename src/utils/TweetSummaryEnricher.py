import json
import numpy as np
import openai
import redis
import os
import time
from dotenv import load_dotenv
from utils.Utilities import MINIMAL_OPENAI_API_CALL_INTERVAL_SEC
from utils.Logging import info
from openAI.OpenaiGpt35ApiManager import OpenaiGpt35ApiManager
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


class TweetSummaryEnricher():
    def __init__(self, sources):
        self.sources = sources
        self.last_request_time = None  # error_code=None error_message='Rate limit reached for default-global-with-image-limits in organization org-mJUMNPeqLz41mk3VvrEAqOMV on requests per min. Limit: 60 / min. Please try again in 1s. Contact support@openai.com if you continue to have issues. Please add a payment method to your account to increase your rate limit. Visit https://platform.openai.com/account/billing to add a payment method.' error_param=None error_type=requests message='OpenAI API error received' stream_error=False
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.openaiApiManager = OpenaiGpt35ApiManager()

    def find_most_similar_url_uisng_openai_embedding(self, target_sentence):
        target_embedding = self.openaiApiManager.get_embedding(target_sentence)
        best_score = 0
        best_match = ""
        for source in self.sources:
            source_embedding = self.get_text_embedding(source)
            similarity = np.dot(source_embedding, target_embedding)
            if similarity > best_score:
                best_score = similarity
                best_match = source
        return best_match

    def get_text_embedding(self, text):
        first_100_char_of_text_as_cache_key = text[:100]
        if not self.redis_client.get(first_100_char_of_text_as_cache_key):
            if self.last_request_time is not None:
                time_elapsed = time.time() - self.last_request_time
                if time_elapsed < MINIMAL_OPENAI_API_CALL_INTERVAL_SEC:
                    time.sleep(
                        MINIMAL_OPENAI_API_CALL_INTERVAL_SEC - time_elapsed)
            embedding = self.openaiApiManager.get_embedding(text)
            self.last_request_time = time.time()
            self.redis_client.set(
                first_100_char_of_text_as_cache_key, json.dumps(embedding))
            info(f"{first_100_char_of_text_as_cache_key} cached")
        return json.loads(self.redis_client.get(first_100_char_of_text_as_cache_key))
