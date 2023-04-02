import json
import logging
import sys
from django.core.management.base import BaseCommand
from bb_finance_api.factory.bb_finance_story_to_detail_factory import BBFinanceStoryToDetailFactory
from bb_finance_api.models import BBFinanceStory

logger = logging.getLogger(__name__)



class Command(BaseCommand):
    help = 'Retrieves data from BBFinance API and stores it in the BBFinanceStory model'

    def handle(self, *args, **kwargs):
        id = "RS87SGT0AFB401"
        if BBFinanceStory.objects.filter(internal_id=id).exists():
            story = BBFinanceStory.objects.get(internal_id=id)
            # Do something with the story
            story.ai_summary = "{}".format(BBFinanceStory.get_text_from_components_by_class(story.components))

            article_dict = BBFinanceStoryToDetailFactory.create(story)
            article_json = json.dumps(article_dict)
            print(article_json)
            #logger.debug(article_json)
            
        else:
            pass

        # Print out all of the story fields
        # print("Title: {}".format(story.title))
        # print("Abstract: {}".format(story.abstract))
        # print("Ad Params: {}".format(story.ad_params))
        # print("Archived: {}".format(story.archived))
        # print("Attributor: {}".format(story.attributor))
        # print("Authored Region: {}".format(story.authored_region))
        # print("Brand: {}".format(story.brand))
        # print("Byline: {}".format(story.byline))
        # print("Card: {}".format(story.card))
        # print("Components: {}".format(story.components))
        # print("Content Tags: {}".format(story.content_tags))
        # print("Disable Ads: {}".format(story.disable_ads))
        # print("Follow Author Details: {}".format(story.follow_author_details))
        # print("Internal ID: {}".format(story.internal_id))
        # print("Is Metered: {}".format(story.is_metered))
        # print("Lede Image: {}".format(story.lede_image))
        # print("Long URL: {}".format(story.long_url))
        # print("Newsletter Tout Label: {}".format(story.newsletter_tout_label))
        # print("Premium: {}".format(story.premium))
        # print("Primary Category: {}".format(story.primary_category))
        # print("Primary Site: {}".format(story.primary_site))
        # print("Published: {}".format(story.published))
        # print("Readings: {}".format(story.readings))
        # print("Resource ID: {}".format(story.resource_id))
        # print("Resource Type: {}".format(story.resource_type))
        # print("Secondary Brands: {}".format(story.secondary_brands))
        # print("Security IDs: {}".format(story.security_i_ds))
        # print("Short URL: {}".format(story.short_url))
        # print("Summary: {}".format(story.summary))
        # print("Themed Images: {}".format(story.themed_images))
        # print("Title: {}".format(story.title))
        # print("Topics: {}".format(story.topics))
        # print("Type: {}".format(story.type))
        # print("Updated At: {}".format(story.updated_at))
        # print("Word Count: {}".format(story.word_count))
        # print("AI Summary2: {}".format(BBFinanceStory.get_text_from_components(story.components)))


