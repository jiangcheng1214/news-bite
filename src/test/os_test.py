import os

from dotenv import load_dotenv


load_dotenv()
key = os.getenv("TWITTER_BEARER_TOKEN")

print(key)