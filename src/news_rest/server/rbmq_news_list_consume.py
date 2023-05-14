import json
import sys
import time
import django
import pika
import os
from bb_finance_api.factory.bb_finance_story_factory import BBFinanceStoryFactory
from bb_finance_api.rapid_api.rapid_bb_finance_api import RapidBBFinanceAPI


markets = "markets|technology|view|pursuits|politics|green|citylab|businessweek|fixed-income|hyperdrive|cryptocurrencies|wealth|latest|personalFinance|quickTake|world|industries|stocks|currencies|brexit"
markets = markets.split("|")

queues = []
for market in markets:
    queues.append('news_queue_' + market)

# Connect to the RabbitMQ server
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare the queues
for queue_name in queues:
    channel.queue_declare(queue=queue_name)

# Define a callback function to handle incoming messages
def callback(ch, method, properties, body):
    print(f'Received message: on queue {method.routing_key}')
    news_list = json.loads(body)
    bb_finance_api = RapidBBFinanceAPI(os.getenv('RAPID_API_KEYS'))
    articles = []
    for item in news_list:
        article_dict = bb_finance_api.get_story_detail(item['internal_id'])
        articles.append(BBFinanceStoryFactory.create(article_dict))
        time.sleep(0.2)
    BBFinanceStoryFactory.objects.bulk_create(articles)
    

# Set up the consumers to receive messages from the queues
for queue_name in queues:
    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

# Start consuming messages from the queues
print('Waiting for messages...')
channel.start_consuming()


