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

# example 1 - chat

# chat = ChatOpenAI(temperature=0.2, openai_api_key=OPENAI_KEY)
# result = chat([
#     SystemMessage(
#         content="You are a nice AI bot that helps generate news tweet based on the content I provide."),
#     HumanMessage(content="Coinbase will also supply services for Valkyrie and Bitwise's bitcoin spot ETF, according to individuals familiar with the situation.")
# ])
# print(result.content)

# example 2 - llms
# llm = OpenAI(model='text-ada-001', openai_api_key=OPENAI_KEY)
# result = llm("What is Valkyrie in crypto?")
# print(result)

# example 3 - chat with llms
# chat = ChatOpenAI(temperature=0.3, openai_api_key=OPENAI_KEY,
#                   model='gpt-3.5-turbo-16k-0613')
# result = chat([
#     SystemMessage(
#         content="You are a nice AI bot that helps generate news tweet based on the content I provide. Try to make is easy to understand."),
#     HumanMessage(content="Coinbase will also supply services for Valkyrie and Bitwise's bitcoin spot ETF, according to individuals familiar with the situation.")
# ])
# print(result.content)

# example 4 - embedding texts
# embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_KEY)
# text_embedding = embeddings.embed_query('text to be embedded')

# example 5 - prompts
# llm = ChatOpenAI(model='gpt-3.5-turbo-16k-0613', openai_api_key=OPENAI_KEY)
# template = """
# Please summarize the following text:
# {text}
# """
# prompt = PromptTemplate(template=template, input_variables=['text'])
# result = llm([
#     HumanMessage(content=prompt.format(text="📢 Exciting news! Coinbase, a leading cryptocurrency exchange, is set to provide services for Valkyrie and Bitwise's bitcoin spot ETF. This means that investors will be able to trade and access these ETFs through Coinbase's platform. Stay tuned for more updates on this development! 🚀 #Coinbase #Bitcoin #ETF"))
# ])
# print(result)

# example 6 - example selectors
# llm = OpenAI(model='text-davinci-003', openai_api_key=OPENAI_KEY)
# example_prompt = PromptTemplate(
#     template="Example input: {input}\nExample output: {output}", input_variables=['input', 'output'])

# examples = [
#     {"input": "boy", "output": "man"},
#     {"input": "puppy", "output": "dog"},
#     {"input": "girl", "output": "lady"},
#     {"input": "small", "output": "big"},
# ]

# example_selector = SemanticSimilarityExampleSelector.from_examples(
#     examples, OpenAIEmbeddings(openai_api_key=OPENAI_KEY), FAISS, k=2)
# similarity_prompt = FewShotPromptTemplate(
#     example_selector=example_selector,
#     example_prompt=example_prompt,
#     prefix="Given the following input and output pairs, please generate the next word in the sequence:\n",
#     suffix="\nInput: {query}\nOutput:",
#     input_variables=['query']
# )

# result = llm(similarity_prompt.format(query='snake'))
# print(result)


# example 7 - output parser

# llm = OpenAI(temperature=0.2, model='text-davinci-003',
#  openai_api_key=OPENAI_KEY)
response_schemas = [
    ResponseSchema(name='tweet_content',
                   description='Tweet content without hashtags'),
    ResponseSchema(name='hashtags',
                   description='Hashtags based on the content'),
]
output_parser = StructuredOutputParser.from_response_schemas(
    response_schemas=response_schemas)
format_instructions = output_parser.get_format_instructions()
print(format_instructions)

template = """
Generate tweet content and hashtags separately based on following information:\n

{format_instructions}

% NEWS TITLE %:\n{news_title}\n
% NEWS ABSTRACT %:\n{news_abstract}\n
% NEWS TOPICS %:\n{news_topics}\n
% NEWS SOURCE %:\n{news_source}\n

% YOUR RESPONSE %:\n
"""

prompt = PromptTemplate(template=template, input_variables=[
                        'news_title', 'news_abstract', 'news_topics', 'news_source'],
                        partial_variables={"format_instructions": format_instructions})

prompt_values = prompt.format(
    news_title="Coinbase To Support Valkyrie And Bitwise Bitcoin Spot ETFs: Report",
    news_abstract="Coinbase will also supply services for Valkyrie and Bitwise's bitcoin spot ETF, according to individuals familiar with the situation.",
    news_topics=[],
    news_source="Coincu"
)
# result = llm(prompt_values)
# print(result)
# parsed_result = output_parser.parse(result)
# print(parsed_result)


chat = ChatOpenAI(temperature=0.2, openai_api_key=OPENAI_KEY,
                  model='gpt-3.5-turbo-16k-0613')
result = chat([
    SystemMessage(
        content="You are a nice AI bot that helps generate news tweet based on the news title, news abstract, news topics and news source that I provide."),
    HumanMessage(content=prompt_values)
])
parsed_result = output_parser.parse(result.content)
print(parsed_result)
