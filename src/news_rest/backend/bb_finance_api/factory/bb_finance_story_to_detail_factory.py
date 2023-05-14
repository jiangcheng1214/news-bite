import json
import sys
from typing import Dict

from bb_finance_api.models import BBFinanceStory

class BBFinanceStoryToDetailFactory:
    @staticmethod
    def create(story: BBFinanceStory) -> Dict:
        return {
            "abstract": story.abstract,
            "adParams":  json.loads(story.ad_params),
            "archived": story.archived,
            "attributor": story.attributor,
            "authoredRegion": story.authored_region,
            "brand": story.brand,
            "byline": story.byline,
            "card": story.card,
            "components":  json.loads(story.components)  if story.components else None,
            "contentTags": json.loads(story.content_tags) if story.content_tags else None,
            "disableAds": story.disable_ads,
            "followAuthorDetails": json.loads(story.follow_author_details) if story.follow_author_details else None,
            "internalID": story.internal_id,
            "isMetered": story.is_metered,
            "ledeImage": json.loads(story.lede_image) if story.lede_image else None,
            "longURL": story.long_url,
            "newsletterToutLabel": story.newsletter_tout_label,
            "premium": story.premium,
            "primaryCategory": story.primary_category,
            "primarySite": story.primary_site,
            "published": story.published,
            "readings": json.loads(story.readings) if story.readings else None,
            "resourceID": story.resource_id,
            "resourceType": story.resource_type,
            "secondaryBrands": json.loads(story.secondary_brands) if story.secondary_brands else None,
            "securityIDs": json.loads(story.security_i_ds) if story.security_i_ds else None,
            "shortURL": story.short_url,
            "summary": story.summary,
            "themedImages": json.loads(story.themed_images) if story.themed_images else None,
            "title": story.title,
            "topics": json.loads(story.topics) if story.topics else None,
            "type": story.type,
            "updatedAt": story.updated_at,
            "wordCount": story.word_count,
            "ai_summary": story.ai_summary
        }
