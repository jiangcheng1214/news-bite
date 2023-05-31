import re
from openai.error import APIError, InvalidRequestError, OpenAIError
from utils.Utilities import OpenaiFinishReason, OpenaiModelVersion
from utils.Logging import info, warn, error
from dotenv import load_dotenv
import openai
import time
import os
import nltk
import json
from typing import List
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


class OpenaiGptApiManager():
    def __init__(self, gpt_model_version: OpenaiModelVersion):
        self.API = openai
        # self.embedding_model = "text-embedding-ada-002"
        self.summarize_ratio = 0.2
        if gpt_model_version == OpenaiModelVersion.GPT3_5.value:
            self.gpt_model_name = "gpt-3.5-turbo"
            # 4096 tokens for gpt-3.5-turbo
            self.token_size_limit = 4096
            # 60% of the token size limit will be used for the prompt
            self.token_size_limit_usage_ratio_for_summarization = 0.5
        elif gpt_model_version == OpenaiModelVersion.GPT4.value:
            self.gpt_model_name = "gpt-4"
            # 4096 tokens for gpt-4
            self.token_size_limit = 8192
            # x of the token size limit will be used for the prompt
            self.token_size_limit_usage_ratio_for_summarization = 0.7

    def _get_complete_gpt_response(self, system_prompt: str, user_prompt: str, num_retries=3):
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
        error(
            f"OpenAI API Error: Failed to get response after {num_retries} retries")
        return None

    def summarize_tweets(self, tweets: List[str]):
        system_setup_prompt = f"As a tweet analyzer, you will perform the following tasks:\
            1. Ignore tweets that contains question mark or exclamation mark. \
            2. Ignore advertisements and extract informational tweets. \
            3. Exclude tweets pertaining to countries categorized as less developed. \
            4. Prioritize breaking news and contents from authors with large follower count. \
            Tweet inputs are in the format: (author name) (follower count) (tweet)"

        system_setup_prompt_token_size = len(
            nltk.word_tokenize(system_setup_prompt))
        responses = []
        while len(tweets) > 0:
            if len(tweets) < 20:
                info(
                    f"skipping summarizing {len(tweets)} tweets because it's too short")
                break
            current_tweet_group = []
            while tweets and system_setup_prompt_token_size + len(nltk.word_tokenize('\n'.join(current_tweet_group))) < self.token_size_limit * self.token_size_limit_usage_ratio_for_summarization:
                current_tweet_group.append(tweets.pop(0))
            target_summary_item_count = int(
                len(current_tweet_group) * self.summarize_ratio)
            user_prompt_intro = f"Summarize these tweets into up to ${target_summary_item_count} points and rephrase them to news that is easy for people to understand\n"
            tweets_by_line = '\n'.join(current_tweet_group)
            user_prompt = f"{user_prompt_intro}{tweets_by_line}"
            estimated_token_size = system_setup_prompt_token_size + \
                len(nltk.word_tokenize(user_prompt))
            info(
                f"start summarizing {len(current_tweet_group)} tweets into {target_summary_item_count} items. estimated token size: {estimated_token_size}. ({len(tweets)} tweets left)")
            try:
                response = self._get_complete_gpt_response(
                    system_setup_prompt, user_prompt)
                if response:
                    responses.append(response)
            except Exception as e:
                error(f"Error occurred: {e}")
                time.sleep(5)
        return responses

    def merge_summary_items(self, all_summary_items):
        current_group = []
        while 1:
            while all_summary_items and len(nltk.word_tokenize('\n'.join(current_group))) < self.token_size_limit * self.token_size_limit_usage_ratio_for_summarization:
                current_group.append(all_summary_items.pop(0))
            user_prompt_intro = f"Merge similar news and generate up to 20 news in the language that is easy to understand. Inputs are one news per line:\n"
            summary_by_line = '\n'.join(current_group)
            user_prompt = f"{user_prompt_intro}{summary_by_line}"
            estimated_token_size = len(nltk.word_tokenize(user_prompt))
            info(
                f"start merging {len(current_group)} summary items. Estimated prompt token size: {estimated_token_size}. ({len(all_summary_items)} summaries left)")
            try:
                response = self._get_complete_gpt_response(
                    None, user_prompt)
                if response:
                    summary_items = response['text'].split('\n')
                    info(
                        f"summary items merged {len(current_group)} => {len(summary_items)} prompt_tokens:{response['usage']['prompt_tokens']} completion_tokens:{response['usage']['completion_tokens']} total_tokens:{response['usage']['total_tokens']}")
                    current_group = []
                    if len(all_summary_items) > 0:
                        all_summary_items += summary_items
                    else:
                        return summary_items
                else:
                    error("Error occurred: response is None")
                    time.sleep(5)
            except Exception as e:
                error(f"Error occurred: {e}")
                time.sleep(5)

    def generate_hashtags(self, summary_items: List[str]):
        user_prompt_intro = f"Generate hashtags for the following news. Make sure the hashtags are not generic words. Make sure the number of hashtag groups returned matches the number of input tweet. Output format should be comma separated for each tweet, for example: \"#line1tag1 #line1tag2,#line2tag1 #line2tag2,#line3tag1,#line3tag2, ...\"\n"
        summary_by_line = '\n'.join(summary_items)
        user_prompt = f"{user_prompt_intro}{summary_by_line}"
        estimated_token_size = len(nltk.word_tokenize(user_prompt))
        info(
            f"start generating hashtags for {len(summary_items)} summary items. Estimated prompt token size: {estimated_token_size}.")
        try:
            response = self._get_complete_gpt_response(None, user_prompt)
            if response:
                hashtags = response['text'].split(',')
                info(
                    f"hashtags generated {len(summary_items)} => {len(hashtags)} prompt_tokens:{response['usage']['prompt_tokens']} completion_tokens:{response['usage']['completion_tokens']} total_tokens:{response['usage']['total_tokens']}")
                if len(hashtags) > 0:
                    return hashtags
                else:
                    error("Hashtag generation response is []")
                    return []
        except Exception as e:
            error(f"Error occurred: {e}")
            return []

    def generate_hashtags_for_single_tweet(self, tweet: str):
        user_prompt_intro = f"Generate up to 3 twitter hashtags for the following news. Make sure the hashtags are not generic words. Output format should be space separated hashtags, for example: \"#hashtag1 #hashtag2 ...\"\n"
        user_prompt = f"{user_prompt_intro}{tweet}"
        estimated_token_size = len(nltk.word_tokenize(user_prompt))
        info(
            f"start generating hashtags for 1 tweet. Estimated prompt token size: {estimated_token_size}.")
        try:
            response = self._get_complete_gpt_response(None, user_prompt)
            if response:
                hashtags = response['text']
                info(
                    f"hashtags generated {hashtags} prompt_tokens:{response['usage']['prompt_tokens']} completion_tokens:{response['usage']['completion_tokens']} total_tokens:{response['usage']['total_tokens']}")
                if hashtags:
                    return hashtags
                else:
                    error("Hashtag generation response is empty")
                    return ""
        except Exception as e:
            error(f"Error occurred: {e}")
            return ""


if __name__ == "__main__":
    # models = openai.Model.list()
    # print([m.id for m in models.data])
    openaiGP35ApiManager = OpenaiGptApiManager(OpenaiModelVersion.GPT3_5.value)
    # tweets = open(os.path.join(os.path.dirname(__file__),
    #               '../../data_example/tweets/crypto_currency/20230331/clean_11'), 'r').readlines()
    # info(openaiGP35ApiManager.summarize_tweets(
    #     tweets))
    with open('/Users/chengjiang/Dev/NewsBite/data/tweet_summaries/technology_finance/20230529/summary_21', 'r') as f:
        lines = f.readlines()
        hashtags = openaiGP35ApiManager.generate_hashtags(lines)
        for i in range(len(lines)):
            info(lines[i])
            info(hashtags[i])
    pass
