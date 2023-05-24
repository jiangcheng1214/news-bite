import json
import openai
import redis
import os
from dotenv import load_dotenv
from utils.Utilities import OpenaiModelVersion, REDIS_TWEET_EMBEDDING_DICT_KEY
from utils.TextEmbeddingCache import TextEmbeddingCache
from utils.Logging import info, warn
from openAI.OpenaiGptApiManager import OpenaiGptApiManager
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


class TweetSummaryEnricher():
    def __init__(self, sources=[]):
        self.sources = sources
        self.last_request_time = None  # error_code=None error_message='Rate limit reached for default-global-with-image-limits in organization org-mJUMNPeqLz41mk3VvrEAqOMV on requests per min. Limit: 60 / min. Please try again in 1s. Contact support@openai.com if you continue to have issues. Please add a payment method to your account to increase your rate limit. Visit https://platform.openai.com/account/billing to add a payment method.' error_param=None error_type=requests message='OpenAI API error received' stream_error=False
        self.redis_client = redis.Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), db=os.getenv("REDIS_DB"), password=os.getenv("REDIS_PASS"))
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
            similarity = TextEmbeddingCache.get_instance().get_text_similarity_score(source, target_sentence)
            if similarity > best_score:
                best_score = similarity
                best_match = source
        return best_match, best_score
