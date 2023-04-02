from django.core.management.base import BaseCommand
import requests
import json
from bb_finance_api.factory.bb_finance_story_factory import BBFinanceStoryFactory

from bb_finance_api.task import get_news_list


class Command(BaseCommand):
    help = 'Retrieves data from BBFinance API and stores it in the BBFinanceStory model'

    def handle(self, *args, **kwargs):

        get_news_list()
        # # News List API
        # url = "https://bb-finance.p.rapidapi.com/news/list"
        # querystring = {"id":"markets"}
        # headers = {
        #     "X-RapidAPI-Key": "6978d0ce6amsh90937165805856ap15260bjsn6ff4479a96f6",
        #     "X-RapidAPI-Host": "bb-finance.p.rapidapi.com"
        # }
        # response = requests.request("GET", url, headers=headers, params=querystring)
        # news_list = json.loads(response.text)
        # articles = []
        # # Connect to the RabbitMQ server
        # connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        # channel = connection.channel()

        # # Declare the queue
        # channel.queue_declare(queue='my_queue')

        # # Send a message to the queue
        # message = 'Hello, World!'
        # channel.basic_publish(exchange='', routing_key='my_queue', body=message)

        # # Close the connection
        # connection.close()

        # for module in news_list['modules']:
        #     if len(module['stories']) > 0:
        #         internal_id = module['stories'][0]['internal_id']
        #         # News Detail API
        #         url = "https://bb-finance.p.rapidapi.com/stories/detail"
        #         querystring = {"internalID": internal_id}
        #         response = requests.request("GET", url, headers=headers, params=querystring)
        #         article_dict = json.loads(response.text)
        #         articles.append(BBFinanceStoryFactory.create(article_dict).create(article_dict))
        # BBFinanceNews.objects.bulk_create(articles)
        # self.stdout.write(self.style.SUCCESS('Data saved successfully!'))
    
