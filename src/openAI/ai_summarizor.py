from openai.error import APIError, InvalidRequestError, OpenAIError
from utils.Utilities import SUM_TWEET_FILE_PREFIX
from utils.Logging import info
from dotenv import load_dotenv
import openai
import time
import os
import nltk
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

OPEN_AI_TOKEN_SIZE_LIMIT = 4096  # 4096 tokens for gpt-3.5-turbo-0301
OPEN_AI_TOKEN_SIZE_LIMIT_BUFFER_PERCENT = 0.8


def gpt3_5_tweets_summarize(tweets, topic: str, num_retries: int = 3):
    tweets_by_line = '\n'.join(tweets)
    normalized_topic = topic.replace("_", " ")
    system_setup_prompt = f"As an tweet analyzer, your specific tasks are following:\
        1. Filter out tweets unrelated to {normalized_topic} \
        1. Filter out promotional tweets, questions and tweets with 5 or less words \
        2. Prioritize tweets related to government regulations or official announcements made by authoritative sources \
        3. Combine similar tweets and extract valuable information into bullet point news-style format \
        4. Pick 10 most informational summary points \
        The tweets are in a single line format and always start with the author name and their number of followers. \
        Keep in mind that tweets from authoritative authors and those with large follower count should not be ignored."

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


def gpt3_5_combine_hourly_summary(summaries, topic: str, num_retries: int = 3):
    news_groups = []
    news_group_growing = ''
    for summary in summaries:
        for news in summary.split('\n'):
            if not news:
                continue
            news_tokenized = nltk.word_tokenize(news)
            news_token_count = len(news_tokenized)
            news_group_tokenized = nltk.word_tokenize(news_group_growing)
            news_group_token_count = len(news_group_tokenized)
            if news_group_token_count + news_token_count < OPEN_AI_TOKEN_SIZE_LIMIT * OPEN_AI_TOKEN_SIZE_LIMIT_BUFFER_PERCENT:
                news_group_growing += news
                news_group_growing += '\n'
            else:
                news_groups.append(news_group_growing)
                news_group_growing = ''
    news_groups.append(news_group_growing)
    info(f'{len(summaries)} {topic} summaries are grouped into {len(news_groups)} chuncks for further summarization')
    further_summaries = []
    for news_group in news_groups:
        normalized_topic = topic.replace("_", " ")
        for i in range(num_retries+1):
            if i == num_retries:
                raise ValueError("Exceeded maximum number of retries")
            try:
                system_setup_prompt = f"As a news analyzer, your specific tasks are following:\
                    1. Filter out news unrelated to {normalized_topic} \
                    2. Prioritize news about government regulations \
                    3. Prioritize official announcements made by authoritative sources \
                    4. Prioritize news with valuable information \
                    5. Combine similar news and extract valuable information into bullet point news-style summaries \
                    6. Pick top 10 summaries \
                    Please be aware that you will received one news per line "
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_setup_prompt},
                        {"role": "user",
                            "content": f"Summarize following {normalized_topic} news\n{news_group}"}
                    ],
                    temperature=1,
                    n=1,
                    presence_penalty=0,
                    frequency_penalty=0
                )
                further_summaries.append(response)
                break
            except APIError as e:
                info(f"Error occurred: {e}")
                time.sleep(10)
            except InvalidRequestError as e:
                info(f"Error occurred: {e}")
                time.sleep(10)
            except OpenAIError as e:
                info(f"Error occurred: {e}")
                time.sleep(10)
    return further_summaries


# dir_path = '/Users/chengjiang/Dev/NewsBite/data/tweets/crypto_currency/20230324'
# summaries = []
# for file_name in os.listdir(dir_path):
#     if file_name.startswith(SUM_TWEET_FILE_PREFIX):
#         lines = open(os.path.join(dir_path, file_name), 'r').readlines()
#         for line in lines:
#             summary_json = json.loads(line)
#             summaries.append(summary_json['choices'][0]['message']['content'])

# response = gpt3_5_combine_hourly_summary(
#     summaries, TwitterTopic.CRYPTO_CURRENCY.value)
# info(response)

# response = gpt3_5_tweets_summarize(tweets, TwitterTopic.FINANCIAL.value)
# info(response)
