import os
import time
import openai
from dotenv import load_dotenv
from openai.error import APIError, InvalidRequestError, OpenAIError
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def gpt3_5_tweets_summarize(tweets, topic: str, num_retries: int = 3):
    tweets_by_line = '\n'.join(tweets)
    normalized_topic = topic.replace("_", " ")
    system_setup_prompt = f"Please act as a {normalized_topic} tweets analyzer and perform 3 things: \
             1. extract meaningful data from tweets ignoring referral program posts and questions\
             2. focus on government regulations and announcements from authoritative entities\
             3. provide a news style summary without mentioning twitter being the data source\
            The tweets are provided one line per tweet. Each tweet always starts with author name and their follower count.\
            Authoritative authors and the ones with large follower count should not be ignored."

    for i in range(num_retries):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_setup_prompt},
                    {"role": "user", "content": f"Summarize these tweets:\n{tweets_by_line}"}
                ],
                temperature=1,
                n=1,
                presence_penalty=0,
                frequency_penalty=0
            )
            return response
        except APIError as e:
            info(f"Error occurred: {e}")
            time.sleep(10)
        except InvalidRequestError as e:
            info(f"Error occurred: {e}")
            time.sleep(10)
        except OpenAIError as e:
            info(f"Error occurred: {e}")
            time.sleep(10)
    raise ValueError("Exceeded maximum number of retries")


# path = '/Users/chengjiang/Dev/NewsBite/data/tweets/financial/cleaned_1679536571.jsons'
# response = gpt3_5_tweets_summarize_with_file(path, TwitterTopic.FINANCIAL)
# info(response)
