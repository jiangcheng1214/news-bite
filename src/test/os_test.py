import os

from dotenv import load_dotenv
from Constants import TWITTER_BEARER_TOKEN_EVAR_KEY

load_dotenv()
key = os.getenv(TWITTER_BEARER_TOKEN_EVAR_KEY)

print(key)