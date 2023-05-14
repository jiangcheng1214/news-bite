import json
from uuid import UUID
from bb_finance_api.models import BBFinanceStory


class BBFinanceStoryFactory:
    @staticmethod
    def create(article):
        return BBFinanceStory(
            id =  article['internalID'],
            abstract=article['abstract'] if 'abstract' in article else json.dumps([]) ,
            ad_params=json.dumps(article['adParams']) if 'adParams' in article else json.dumps({}),
            archived=article['archived'] if "archived" in article else 0,
            attributor=article['attributor'] if "attributor" in article else None,
            authored_region=article['authoredRegion'] if 'authoredRegion' in article else None,
            brand=article['brand'] if 'brand' in article else None,
            byline=article['byline'] if 'byline' in article else None,
            card=article['card'] if 'card' in article else None,
            components=json.dumps(article['components']) if "components" in article else json.dumps([]),
            content_tags=json.dumps(article['contentTags']) if "contentTags" in article else json.dumps([]),
            disable_ads=article['disableAds'] if 'disableAds' in article else 0,
            follow_author_details=json.dumps(article['followAuthorDetails']) if "followAuthorDetails" in article else json.dumps({}),
            internal_id=article['internalID'],
            is_metered=article['isMetered'] if "isMetered" in article else 0,
            lede_video=json.dumps(article['ledeVideo']) if 'ledeVideo' in article  else json.dumps({}),
            lede_image=json.dumps(article['ledeImage']) if "ledeImage" in article else json.dumps({}),
            long_url=article['longURL'] if "longURL" in article else None,
            newsletter_tout_label=article['newsletterToutLabel'] if "newsletterToutLabel" in article else None,
            premium=article['premium'] if 'premium' in article else 0,
            primary_category=article['primaryCategory'] if 'primaryCategory' in article else None,
            primary_site=article['primarySite'] if 'primarySite' in article else None,
            published=article['published'] if 'published' in article else 0,
            readings=json.dumps(article['readings']) if 'readings' in article else json.dumps([]),
            resource_id=article['resourceId'] if "resourceId" in article else None,
            resource_type=article['resourceType'] if "resourceType" in article else None,
            secondary_brands=json.dumps(article['secondaryBrands']) if "secondaryBrands" in article else json.dumps([]),
            security_i_ds=json.dumps(article['securityIDs']) if "securityIDs" in article else json.dumps([]),
            short_url=article['shortURL'] if "shortURL" in article else None,
            summary=article['summary'] if "summary" in article else None,
            themed_images=json.dumps(article['themedImages']) if "themedImages" in article else json.dumps([]), 
            title=article['title'] if "title" in article else None,
            topics=json.dumps(article['topics']) if "topics" in article else json.dumps([]),
            type=article['type'] if "type" in article else None,
            updated_at=article['updatedAt'] if "updatedAt" in article else 0,
            word_count=article['wordCount'] if "wordCount" in article else 0,
        )

