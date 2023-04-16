# app_name/management/commands/news_consumer.py
import json
import logging
import time
from MySQLdb import IntegrityError
import pika
from django.core.management.base import BaseCommand
import requests
from bb_finance_api.factory.bb_finance_story_factory import BBFinanceStoryFactory
from bb_finance_api.models import BBFinanceStory
from bb_finance_api.rapid_api.rapid_bb_finance_api import RapidBBFinanceAPI
from utils.redis_factory import RedisFactory


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Consume messages from RabbitMQ queues and create BBFinanceStory objects'

    def handle(self, *args, **options):
        markets = "markets|technology|view|pursuits|politics|green|citylab|businessweek|fixed-income|hyperdrive|cryptocurrencies|wealth|latest|personalFinance|quickTake|world|industries|stocks|currencies|brexit"
        markets = markets.split("|")

        queues = []
        for market in markets:
            queues.append('news_queue_' + market)

        # Connect to the RabbitMQ server
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.basic_qos(prefetch_count=5)

        # Declare the queues
        for queue_name in queues:
            channel.queue_declare(queue=queue_name)

        # Define a callback function to handle incoming messages
        def callback(ch, method, properties, body):
            item = json.loads(body)
            print(f'Received message: on queue {method.routing_key} and InternalID {item["internal_id"]}')
            if not BBFinanceStory.objects.filter(internal_id=item['internal_id']).exists():
                url = "https://bloomberg-market-and-financial-news.p.rapidapi.com/stories/detail"
                querystring = {"internalID":{item["internal_id"]}}
                headers = {
	                "X-RapidAPI-Key": "6978d0ce6amsh90937165805856ap15260bjsn6ff4479a96f6",
	                "X-RapidAPI-Host": "bloomberg-market-and-financial-news.p.rapidapi.com"
                }
                response = requests.request("GET", url, headers=headers, params=querystring)
                time.sleep(0.2)
                if response.status_code == 200:
                    article_dict = json.loads(response.text)
                    if 'internalID' in article_dict:
                        RedisFactory().hmset(article_dict['internalID'], article_dict)
                        try:
                            BBFinanceStoryModel = BBFinanceStoryFactory.create(article_dict)
                            BBFinanceStoryModel.created_at = item['created_at']
                            BBFinanceStoryModel.auto_generated_summary = item['summary']
                            BBFinanceStoryModel.save()
                            self.stdout.write(self.style.SUCCESS('Data saved successfully!'))
                        except IntegrityError as e:
                            self.stdout.write(self.style.ERROR((f"Caught a SQL error: {e} and {item['internal_id']}")))
                    else:
                        self.stdout.write(self.style.ERROR((f"{response.text}")))
                else:
                    self.stdout.write(self.style.ERROR((f"Caught a HTTP error: {response.status_code} and {item['internal_id']}")))
                    
        # Set up the consumers to receive messages from the queues
        for queue_name in queues:
            channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

         # Start consuming messages from the queues
        self.stdout.write(self.style.SUCCESS('Waiting for messages...'))
        channel.start_consuming()
