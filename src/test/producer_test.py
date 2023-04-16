import json
from utils.Decorators import rabbitmq_decorator
import os

script_dir = os.path.dirname(os.path.realpath(__file__))
tweet_path = os.path.join(script_dir, 'tweet.json')

@rabbitmq_decorator('twitter_data')
def test_function():
    with open(tweet_path, 'r') as f:
        data = json.load(f)
    return data

if __name__ == "__main__":
    test_function()
