from openai.error import APIError, InvalidRequestError, OpenAIError
from openai.embeddings_utils import get_embedding
from utils.Utilities import OpenaiFinishReason, TwitterTopic
from utils.Logging import info, warn
from dotenv import load_dotenv
import openai
import time
import os
import nltk
import json
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


class OpenaiGpt35ApiManager():
    def __init__(self):
        self.gpt3_5_model_name = "gpt-3.5-turbo"
        self.API = openai
        self.embedding_model = "text-embedding-ada-002"
        # 4096 tokens for gpt-3.5-turbo
        self.token_size_limit = 4096
        # 60% of the token size limit will be used for the prompt
        self.token_size_limit_usage_ratio = 0.6

    def _get_complete_response(self, system_prompt: str, user_prompt: str):
        try:
            finish_reason = 'null'
            text = ''
            prompt_tokens = 0
            total_tokens = 0
            completion_tokens = 0
            turns = 0
            if system_prompt:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            else:
                messages = [
                    {"role": "user", "content": user_prompt}
                ]
            while finish_reason != OpenaiFinishReason.STOP.value and turns < 3:
                response = self.API.ChatCompletion.create(
                    model=self.gpt3_5_model_name,
                    messages=messages,
                    temperature=1,
                    n=1,
                    presence_penalty=0,
                    frequency_penalty=0
                )
                finish_reason = response['choices'][0]['finish_reason']
                if finish_reason == OpenaiFinishReason.LENGTH.value:
                    warn(
                        f'OpenAI response is too long. response={json.dumps(response)} messages={json.dumps(messages)}')
                text += response['choices'][0]['message']['content']
                text += '\n'
                prompt_tokens += response['usage']['prompt_tokens']
                total_tokens += response['usage']['total_tokens']
                completion_tokens += response['usage']['completion_tokens']
                messages = [
                    {"role": "user", "content": user_prompt},
                    response['choices'][0]['message'],
                    {"role": "user", "content": 'continue'},
                ]
                turns += 1

            if finish_reason != OpenaiFinishReason.STOP.value:
                info("OpenAI did not stop but reached the turn limit")
            return {'usage': {'prompt_tokens': prompt_tokens, 'total_tokens': total_tokens, 'completion_tokens': completion_tokens}, 'text': text.strip(), 'finish_reason': finish_reason, 'turns': turns}
        except APIError as e:
            info(f"OpenAI API Error: {e}")
            return None

    def summarize_tweets(self, tweets, topic: str, num_retries: int = 3):
        tweets_by_line = '\n'.join(tweets)
        normalized_topic = topic.replace("_", " ")
        system_setup_prompt = f"As an tweet analyzer, your specific tasks are following:\
            1. Filter out tweets unrelated to {normalized_topic} \
            2. Filter out promotional tweets, questions and tweets with 5 or less words \
            3. Combine similar tweets and extract valuable information into bullet point news-style format \
            4. Prioritize tweets related to government regulations or official announcements made by authoritative sources \
            The tweets are in a single line format and always start with the author name and their number of followers. \
            Keep in mind that tweets from authoritative authors and those with large follower count should not be ignored."
        user_prompt = f"Summarize these tweets into up to 10 most important bullet points:\n{tweets_by_line}"
        for i in range(num_retries):
            try:
                response = self._get_complete_response(
                    system_setup_prompt, user_prompt)
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

    """
    Combine hourly summaries using GPT-3.5-turbo
    Parameters:
        hourly_summaries (list): list of hourly summaries.
            example: [
                "1. Google and MeitY Startup Hub Launches Appscale Academy to Help 100 Innovative Indian Startups Grow",
                "2. Artists fight AI programs that copy their styles",
                ...,
                "30. Elon Musk announces that from April 15 only verified accounts will be eligible to be in the 'For You' recommendation on Twitter."]
        topic (str): topic of the tweets. example: 'financial'
    """

    def hourly_tweet_summary_generator(self, hourly_summary_text_list, topic: str):
        news_groups = []
        news_group_growing = ''
        for hourly_summary_text in hourly_summary_text_list:
            for news_text in hourly_summary_text.split('\n'):
                if not news_text:
                    continue
                news_tokenized = nltk.word_tokenize(news_text)
                news_token_count = len(news_tokenized)
                news_group_tokenized = nltk.word_tokenize(
                    news_group_growing)
                news_group_token_count = len(news_group_tokenized)
                if news_group_token_count + news_token_count < self.token_size_limit * self.token_size_limit_usage_ratio:
                    news_group_growing += news_text
                    news_group_growing += '\n'
                else:
                    news_groups.append(news_group_growing)
                    news_group_growing = ''
        news_groups.append(news_group_growing)
        info(f'{len(hourly_summary_text_list)} {topic} summaries are grouped into {len(news_groups)} chuncks for further summarization')
        # further_summaries = []
        for n in range(len(news_groups)):
            news_group = news_groups[n]
            info(
                f"Summarizing {topic} news, batch {n+1}/{len(news_groups)}")
            normalized_topic = topic.replace("_", " ")
            system_setup_prompt = f"As an hourly news summarizer, your specific tasks are following:\
                        1. Filter out tweets unrelated to {normalized_topic} \
                        2. Filter out promotional tweets, questions and tweets with 5 or less words \
                        3. Combine similar tweets and extract valuable information into bullet point news-style format \
                        4. Prioritize tweets related to government regulations or official announcements made by authoritative sources \
                        The tweets are in a single line format and always start with the author name and their number of followers. \
                        Keep in mind that tweets from authoritative authors and those with large follower count should not be ignored."
            user_prompt = f"Generate a {normalized_topic} news summary with up to 20 bullet points based on following news:\n{news_group}"
            for i in range(3):
                response = self._get_complete_response(
                    system_setup_prompt, user_prompt)
                if response is not None:
                    break
                else:
                    info(f"OpenAI API Error: Retrying {i+1} out of 3")
                    time.sleep(10)
            yield response

    # WIP
    def filter_unrelated_tweets(self, tweets, topic: str):
        tweets_by_line = '\n'.join(tweets)
        normalized_topic = topic.replace("_", " ")
        user_prompt = f"As a twitter filter, please extract {normalized_topic} news from following tweets. You need to drop unrelated ones and return the rest without changing format.\n\n{tweets_by_line}"
        for i in range(3):
            response = self._get_complete_response(
                None, user_prompt)
            if response is not None:
                break
            else:
                info(f"OpenAI API Error: Retrying {i+1} out of 3")
                time.sleep(10)
        return response

    def get_embedding(self, text: str):
        return get_embedding(text, self.embedding_model)


class OpenaiGpt4ApiManager():
    def __init__(self):
        self.gpt4_model_name = "gpt-4"
        self.API = openai
        self.embedding_model = "text-embedding-ada-002"
        # 4096 tokens for gpt-4
        self.token_size_limit = 8192
        # 80% of the token size limit will be used for the prompt
        self.token_size_limit_usage_ratio = 0.8

    def _gpt4_get_complete_response(self, system_prompt: str, user_prompt: str):
        try:
            finish_reason = 'null'
            text = ''
            prompt_tokens = 0
            total_tokens = 0
            completion_tokens = 0
            turns = 0
            if system_prompt:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            else:
                messages = [
                    {"role": "user", "content": user_prompt}
                ]
            while finish_reason != OpenaiFinishReason.STOP.value and turns < 3:
                response = self.API.ChatCompletion.create(
                    model=self.gpt4_model_name,
                    messages=messages,
                    temperature=1,
                    n=1,
                    presence_penalty=0,
                    frequency_penalty=0
                )
                finish_reason = response['choices'][0]['finish_reason']
                if finish_reason == OpenaiFinishReason.LENGTH.value:
                    warn(
                        f'OpenAI response is too long. response={json.dumps(response)} messages={json.dumps(messages)}')
                text += response['choices'][0]['message']['content']
                text += '\n'
                prompt_tokens += response['usage']['prompt_tokens']
                total_tokens += response['usage']['total_tokens']
                completion_tokens += response['usage']['completion_tokens']
                messages = [
                    {"role": "user", "content": user_prompt},
                    response['choices'][0]['message'],
                    {"role": "user", "content": 'continue'},
                ]
                turns += 1

            if finish_reason != OpenaiFinishReason.STOP.value:
                info("OpenAI did not stop but reached the turn limit")
            return {'usage': {'prompt_tokens': prompt_tokens, 'total_tokens': total_tokens, 'completion_tokens': completion_tokens}, 'text': text.strip(), 'finish_reason': finish_reason, 'turns': turns}
        except APIError as e:
            info(f"OpenAI API Error: {e}")
            return None

    def summarize_tweets(self, tweets, topic: str, num_retries: int = 3):
        tweets_by_line = '\n'.join(tweets)
        normalized_topic = topic.replace("_", " ")
        system_setup_prompt = f"As an tweet analyzer, you will perform following tasks:\
            1. Filter out tweets unrelated to {normalized_topic} \
            2. Filter out promotional tweets, questions and tweets with 5 or less words \
            3. Combine similar tweets and extract valuable information into bullet point news-style format \
            4. Prioritize tweets related to government regulations or official announcements made by authoritative sources \
            The tweets are in a single line format and always start with the author name and their number of followers. \
            Keep in mind that tweets from authoritative authors and those with large follower count should not be ignored."
        user_prompt = f"Summarize these tweets into up to 10 most important bullet points without mentioning source:\n{tweets_by_line}"
        for i in range(num_retries):
            try:
                response = self._gpt4_get_complete_response(
                    system_setup_prompt, user_prompt)
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

    def hourly_tweet_summary_generator(self, hourly_summary_text_list, topic: str):
        news_groups = []
        news_group_growing = ''
        for hourly_summary_text in hourly_summary_text_list:
            for news_text in hourly_summary_text.split('\n'):
                if not news_text:
                    continue
                news_tokenized = nltk.word_tokenize(news_text)
                news_token_count = len(news_tokenized)
                news_group_tokenized = nltk.word_tokenize(
                    news_group_growing)
                news_group_token_count = len(news_group_tokenized)
                if news_group_token_count + news_token_count < self.token_size_limit * self.token_size_limit_usage_ratio:
                    news_group_growing += news_text
                    news_group_growing += '\n'
                else:
                    news_groups.append(news_group_growing)
                    news_group_growing = ''
        news_groups.append(news_group_growing)
        info(f'{len(hourly_summary_text_list)} {topic} summaries are grouped into {len(news_groups)} chuncks for further summarization')
        # further_summaries = []
        for n in range(len(news_groups)):
            news_group = news_groups[n]
            info(
                f"Summarizing {topic} news, batch {n+1}/{len(news_groups)}")
            normalized_topic = topic.replace("_", " ")
            system_setup_prompt = f"As an hourly news summarizer, your specific tasks are following:\
                        1. Filter out tweets unrelated to {normalized_topic} \
                        2. Filter out promotional tweets, questions and tweets with 5 or less words \
                        3. Combine similar tweets and extract valuable information into bullet point news-style format \
                        4. Prioritize tweets related to government regulations or official announcements made by authoritative sources \
                        The tweets are in a single line format and always start with the author name and their number of followers. \
                        Keep in mind that tweets from authoritative authors and those with large follower count should not be ignored."
            user_prompt = f"Generate a {normalized_topic} news summary with up to 20 bullet points based on following news without mentioning source:\n{news_group}"
            for i in range(3):
                response = self._gpt4_get_complete_response(
                    system_setup_prompt, user_prompt)
                if response is not None:
                    break
                else:
                    info(f"OpenAI API Error: Retrying {i+1} out of 3")
                    time.sleep(10)
            yield response

    # WIP
    def filter_unrelated_tweets(self, tweets, topic: str):
        tweets_by_line = '\n'.join(tweets)
        normalized_topic = topic.replace("_", " ")
        user_prompt = f"As a twitter filter, please extract {normalized_topic} news from following tweets. You need to drop unrelated ones and return the rest without changing format.\n\n{tweets_by_line}"
        for i in range(3):
            response = self._gpt4_get_complete_response(
                None, user_prompt)
            if response is not None:
                break
            else:
                info(f"OpenAI API Error: Retrying {i+1} out of 3")
                time.sleep(10)
        return response

    def get_embedding(self, text: str):
        return get_embedding(text, self.embedding_model)


if __name__ == "__main__":
    # models = openai.Model.list()
    # print([m.id for m in models.data])
    openaiGP35ApiManager = OpenaiGpt35ApiManager()
    openaiGPT4ApiManager = OpenaiGpt4ApiManager()
    tweets = open(os.path.join(os.path.dirname(__file__),
                  '../../data_example/tweets/crypto_currency/20230331/clean_11'), 'r').readlines()
    info(openaiGP35ApiManager.summarize_tweets(
        tweets, TwitterTopic.CRYPTO_CURRENCY.value))
    info(openaiGPT4ApiManager.summarize_tweets(
        tweets, TwitterTopic.CRYPTO_CURRENCY.value))

    pass
