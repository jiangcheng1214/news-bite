from openai.error import APIError, InvalidRequestError, OpenAIError
from openai.embeddings_utils import get_embedding
from utils.Utilities import OpenaiFinishReason, TwitterTopic, OpenaiModelVersion
from utils.Logging import info, warn, error
from dotenv import load_dotenv
import openai
import time
import os
import nltk
import json
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


class OpenaiGptApiManager():
    def __init__(self, gpt_model_version: OpenaiModelVersion):
        self.API = openai
        self.embedding_model = "text-embedding-ada-002"
        self.summarize_ratio = 0.1
        if gpt_model_version == OpenaiModelVersion.GPT3_5.value:
            self.gpt_model_name = "gpt-3.5-turbo"
            # 4096 tokens for gpt-3.5-turbo
            self.token_size_limit = 4096
            # 60% of the token size limit will be used for the prompt
            self.token_size_limit_usage_ratio = 0.6
        elif gpt_model_version == OpenaiModelVersion.GPT4.value:
            self.gpt_model_name = "gpt-4"
            # 4096 tokens for gpt-4
            self.token_size_limit = 8192
            # x of the token size limit will be used for the prompt
            self.token_size_limit_usage_ratio = 0.7

    def _gpt35_get_complete_response(self, system_prompt: str, user_prompt: str, num_retries=3):
        for i in range(num_retries):
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
                        model=self.gpt_model_name,
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
                error(f"APIError occurred: {e}")
                time.sleep(5)
            except InvalidRequestError as e:
                error(f"InvalidRequestError occurred: {e}")
                time.sleep(5)
            except OpenAIError as e:
                error(f"OpenAIError occurred: {e}")
                time.sleep(5)
        raise Exception(
            f"OpenAI API Error: Failed to get response after {num_retries} retries")

    def summarize_tweets(self, tweets, topic: str):
        normalized_topic = topic.replace("_", " ")
        system_setup_prompt = f"As an tweet analyzer, you will perform following tasks:\
            1. Filter out tweets unrelated to {normalized_topic} \
            2. Filter out promotional tweets, questions and tweets with 5 or less words \
            3. Combine similar tweets and extract valuable information into bullet point news-style format \
            4. Prioritize tweets related to government regulations or official announcements made by authoritative sources \
            The tweets are in a single line format and always start with the author name and their number of followers. \
            Keep in mind that tweets from authoritative authors and those with large follower count should not be ignored."

        system_setup_prompt_token_size = len(
            nltk.word_tokenize(system_setup_prompt))
        responses = []
        while len(tweets) > 0:
            if len(tweets) < 20:
                info(
                    f"skipping summarizing {len(tweets)} {topic} tweets because it's too short")
                break
            current_tweet_group = []
            while tweets and system_setup_prompt_token_size + len(nltk.word_tokenize('\n'.join(current_tweet_group))) < self.token_size_limit * self.token_size_limit_usage_ratio:
                current_tweet_group.append(tweets.pop(0))
            target_summary_item_count = int(
                len(current_tweet_group) * self.summarize_ratio)
            user_prompt_intro = f"Summarize these tweets into up to ${target_summary_item_count} most important bullet points without mentioning source:\n"
            tweets_by_line = '\n'.join(current_tweet_group)
            user_prompt = f"{user_prompt_intro}{tweets_by_line}"
            estimated_token_size = system_setup_prompt_token_size + \
                len(nltk.word_tokenize(user_prompt))
            info(
                f"start summarizing {len(current_tweet_group)} tweets into {target_summary_item_count} items. estimated token size: {estimated_token_size}. ({len(tweets)} tweets left)")
            try:
                response = self._gpt35_get_complete_response(
                    system_setup_prompt, user_prompt)
                responses.append(response)
            except Exception as e:
                error(f"Error occurred: {e}")
                time.sleep(5)
        return responses

    def aggregate_hourly_tweet_summary(self, single_summary_text_list, topic: str):
        normalized_topic = topic.replace("_", " ")
        system_setup_prompt = f"As an hourly news summarizer, your specific tasks are following:\
                    1. Filter out tweets unrelated to {normalized_topic} \
                    2. Filter out promotional tweets, questions and tweets with 5 or less words \
                    3. Combine similar tweets and extract valuable information into bullet point news-style format \
                    4. Prioritize tweets related to government regulations or official announcements made by authoritative sources \
                    The tweets are in a single line format and always start with the author name and their number of followers. \
                    Keep in mind that tweets from authoritative authors and those with large follower count should not be ignored."
        system_setup_prompt_token_size = len(
            nltk.word_tokenize(system_setup_prompt))
        responses = []
        while len(single_summary_text_list) > 0:
            current_group = []
            while single_summary_text_list and system_setup_prompt_token_size + len(nltk.word_tokenize('\n'.join(current_group))) < self.token_size_limit * self.token_size_limit_usage_ratio:
                current_group.append(single_summary_text_list.pop(0))
            user_prompt_intro = f"Generate a {normalized_topic} news summary with up to 20 bullet points based on following news:\n"
            summary_by_line = '\n'.join(current_group)
            user_prompt = f"{user_prompt_intro}{summary_by_line}"
            estimated_token_size = system_setup_prompt_token_size + \
                len(nltk.word_tokenize(user_prompt))
            info(
                f"start merging {len(current_group)} summary items into up to 20 items. estimated token size: {estimated_token_size}. ({len(single_summary_text_list)} tweets left)")
            try:
                response = self._gpt35_get_complete_response(
                    system_setup_prompt, user_prompt)
                responses.append(response)
            except Exception as e:
                error(f"Error occurred: {e}")
                time.sleep(5)
        if len(responses) > 1:
            all_summary_items = []
            for r in responses:
                all_summary_items += r['text'].split('\n')
            return self.merge_summary_items(all_summary_items)
        assert len(responses) == 1
        return responses[0]['text'].split('\n')

    def merge_summary_items(self, all_summary_items, topic: str):
        normalized_topic = topic.replace("_", " ")
        current_group = []
        while 1:
            while all_summary_items and len(nltk.word_tokenize('\n'.join(current_group))) < self.token_size_limit * self.token_size_limit_usage_ratio:
                current_group.append(all_summary_items.pop(0))
            user_prompt_intro = f"Remove repetitive items, filter out items that are not {normalized_topic} news and generate up to 20 news bullet points. Following news items are one item per line:\n"
            summary_by_line = '\n'.join(current_group)
            user_prompt = f"{user_prompt_intro}{summary_by_line}"
            estimated_token_size = len(nltk.word_tokenize(user_prompt))
            info(
                f"start merging {len(current_group)} summary items. Estimated prompt token size: {estimated_token_size}. ({len(all_summary_items)} summaries left)")
            try:
                response = self._gpt35_get_complete_response(
                    None, user_prompt)
                summary_items = response['text'].split('\n')
                info(
                    f"summary items merged {len(current_group)} => {len(summary_items)} prompt_tokens:{response['usage']['prompt_tokens']} completion_tokens:{response['usage']['completion_tokens']} total_tokens:{response['usage']['total_tokens']}")
                current_group = []
                if len(all_summary_items) > 0:
                    all_summary_items += summary_items
                else:
                    return summary_items
            except Exception as e:
                error(f"Error occurred: {e}")
                time.sleep(5)

    def get_embedding(self, text: str):
        return get_embedding(text, self.embedding_model)


if __name__ == "__main__":
    # models = openai.Model.list()
    # print([m.id for m in models.data])
    openaiGP35ApiManager = OpenaiGptApiManager(OpenaiModelVersion.GPT3_5.value)
    tweets = open(os.path.join(os.path.dirname(__file__),
                  '../../data_example/tweets/crypto_currency/20230331/clean_11'), 'r').readlines()
    info(openaiGP35ApiManager.summarize_tweets(
        tweets, TwitterTopic.CRYPTO_CURRENCY.value))

    pass
