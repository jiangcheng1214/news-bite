import json

from django.core.management.base import BaseCommand
from bb_finance_api.factory.bb_finance_story_factory import BBFinanceStoryFactory
from bb_finance_api.rapid_api.rapid_bb_finance_api import RapidBBFinanceAPI

class Command(BaseCommand):
    help = 'Retrieves data from BBFinance API and stores it in the BBFinanceStory model'

    def add_arguments(self, parser):
        parser.add_argument('--api-key', type=str, help='Your RapidAPI key')
        parser.add_argument('--internal_id', default="", type=str, help='Story Detail Internal ID')
        parser.add_argument('--debug', default=False, type=bool, help='Debug mode which not request http')

    def handle(self, *args, **kwargs):

        try:
            # Get the RapidAPI key from command line arguments
            debug = kwargs['debug']
            rapidapi_key = kwargs['api_key']
            internal_id = kwargs['internal_id'] if debug == False else "QFY0Y6T0AFB501"
            article_dict = ""
            if debug:
                # Assuming the JSON file is named "example.json" and is located in the "json_data" directory
                with open('static/json_data/example_.json') as f:
                    article_dict = json.load(f)
            else:
                 bb_finance_api = RapidBBFinanceAPI(rapidapi_key)
                 article_dict = bb_finance_api.get_story_detail(internal_id)
            
            
            BBFinanceStoryFactory.create(article_dict).save()
            self.stdout.write(self.style.SUCCESS('Data saved successfully!'))

        except Exception as e:
             print(e)
