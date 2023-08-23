from langchain import PromptTemplate
from langchain.prompts.example_selector import SemanticSimilarityExampleSelector
from langchain.vectorstores import FAISS
from langchain.prompts import PromptTemplate, FewShotPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.llms import OpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.output_parsers import ResponseSchema, StructuredOutputParser

import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_KEY = os.getenv("OPENAI_API_KEY")


class LangChainAPIManager:
    def __init__(self):
        self.chatModel = ChatOpenAI(
            temperature=0.2, openai_api_key=OPENAI_KEY, model="gpt-4"
        )

    """
    Generate tweet content and hashtags:
    {
        tweet_content: "Tweet content",
        hashtags: ["hashtag1", "hashtag2", ...]
    }
    """

    def generate_tweet_dict(self, title, abstract, topics, source):
        response_schemas = [
            ResponseSchema(
                name="tweet_content", description="Tweet content without hashtags"
            ),
            ResponseSchema(
                name="hashtags", description="Hashtags based on the content"
            ),
        ]
        output_parser = StructuredOutputParser.from_response_schemas(
            response_schemas=response_schemas
        )
        format_instructions = output_parser.get_format_instructions()
        # print(format_instructions)

        template = """
        You are a helpful tweet content generator.
        Based on a given news, generate tweet content which should be less than 260 chars.
        The generated content needs to be easy to understand for people with no access to news source.
        You shouldn't miss any key points of the given news.
        You need to generate relavant hashtags as well.\n

        {format_instructions}

        % NEWS TITLE %:\n{news_title}\n
        % NEWS ABSTRACT %:\n{news_abstract}\n
        % NEWS TOPICS %:\n{news_topics}\n
        % NEWS SOURCE %:\n{news_source}\n

        % YOUR RESPONSE %:\n
        """

        prompt = PromptTemplate(
            template=template,
            input_variables=[
                "news_title",
                "news_abstract",
                "news_topics",
                "news_source",
            ],
            partial_variables={"format_instructions": format_instructions},
        )

        prompt_values = prompt.format(
            news_title=title,
            news_abstract=abstract,
            news_topics=topics,
            news_source=source,
        )
        result = self.chatModel(
            [
                SystemMessage(
                    content="You will help generate tweet content based on given information, including news title, news abstract, news topics and news source."
                ),
                HumanMessage(content=prompt_values),
            ]
        )
        parsed_result = output_parser.parse(result.content)
        return parsed_result
