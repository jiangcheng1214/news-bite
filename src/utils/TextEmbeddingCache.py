import time
import json
from utils.RedisClient import RedisClient
from utils.Utilities import get_clean_text
from utils.Constants import OPENAI_API_KEY_EVAR_KEY, REDIS_TWEET_EMBEDDING_DICT_KEY,  MINIMAL_OPENAI_API_CALL_INTERVAL_SEC, MAX_EMBEDDING_CACHE_SIZE, REDIS_SAVE_EMBEDDING_CACHE_INTERVAL_SEC
from utils.Logging import info, warn, error
from openai.embeddings_utils import get_embedding
from dotenv import load_dotenv
import openai
import os
import numpy as np
from typing import List
load_dotenv()
openai.api_key = os.getenv(OPENAI_API_KEY_EVAR_KEY)

# Singleton class for caching text embeddings
class TextEmbeddingCache:
    _instance = None

    def __init__(self):
        assert TextEmbeddingCache._instance is None, "Singleton class"
        self.redis_client = RedisClient().connect()
        self.embedding_model = "text-embedding-ada-002"
        embedding_dict_json_string = self.redis_client.get(
            REDIS_TWEET_EMBEDDING_DICT_KEY)
        if embedding_dict_json_string is None:
            self.embedding_dict_cache = {}
        else:
            self.embedding_dict_cache = json.loads(embedding_dict_json_string)
        self.last_request_time = time.time()
        self.last_save_time = time.time()

    @staticmethod
    def get_instance():
        if TextEmbeddingCache._instance is None:
            TextEmbeddingCache._instance = TextEmbeddingCache()
        return TextEmbeddingCache._instance

    def embedding_of(self, text):
        clean_text = get_clean_text(text)
        if text not in self.embedding_dict_cache:
            if len(self.embedding_dict_cache) > MAX_EMBEDDING_CACHE_SIZE:
                warn(
                    f"Embedding cache size {len(self.embedding_dict_cache)} is larger than {MAX_EMBEDDING_CACHE_SIZE}")
                self.embedding_dict_cache = {}
            info(f"Embedding cache miss for {clean_text}")
            time_elapsed = time.time() - self.last_request_time
            if time_elapsed < MINIMAL_OPENAI_API_CALL_INTERVAL_SEC:
                time.sleep(
                    MINIMAL_OPENAI_API_CALL_INTERVAL_SEC - time_elapsed)
            self.embedding_dict_cache[clean_text] = get_embedding(
                clean_text, self.embedding_model)
            self.last_request_time = time.time()
            if time.time() - self.last_save_time > REDIS_SAVE_EMBEDDING_CACHE_INTERVAL_SEC:
                self.save()
        return self.embedding_dict_cache[clean_text]

    def get_text_similarity_score(self, text1: str, text2: str):
        text1_embedding = self.embedding_of(text1)
        text2_embedding = self.embedding_of(text2)
        similarity = np.dot(text1_embedding, text2_embedding)
        return similarity

    def find_best_match_and_score(self, candidates: List[str], target: str):
        best_score = 0
        best_match = ""
        for source in candidates:
            similarity = self.get_text_similarity_score(source, target)
            if similarity > best_score:
                best_score = similarity
                best_match = source
        return best_match, best_score

    def save(self):
        try:
            info(
                f"Saving embedding cache (size: {len(self.embedding_dict_cache)}) to redis")
            embedding_dict_cache_json_string = json.dumps(
                self.embedding_dict_cache)
            self.redis_client.set(REDIS_TWEET_EMBEDDING_DICT_KEY,
                                  embedding_dict_cache_json_string)
            self.last_save_time = time.time()
        except Exception as e:
            error(f"Failed to save embedding cache: {e}")

    def clear(self):
        try:
            self.embedding_dict_cache = {}
            self.redis_client.delete(REDIS_TWEET_EMBEDDING_DICT_KEY)
            info("Embedding cache cleared")
        except Exception as e:
            error(f"Failed to clear embedding cache: {e}")
