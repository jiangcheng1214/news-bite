import json
from django.db import models
from django.utils import timezone

class BBFinanceStory(models.Model):
    abstract = models.JSONField()
    ad_params = models.JSONField()
    archived = models.BooleanField(default=False)
    attributor = models.CharField(max_length=255, default="")
    authored_region = models.CharField(max_length=255, default="")
    brand = models.CharField(max_length=255, default="")
    byline = models.CharField(max_length=255, default="")
    card = models.CharField(max_length=255, default="")
    components = models.JSONField(default=dict)
    content_tags = models.JSONField(default=dict)
    disable_ads = models.BooleanField(default=False)
    follow_author_details = models.JSONField(default=dict)
    id = models.CharField(max_length=255, primary_key=True)
    internal_id = models.CharField(max_length=255, default="")
    is_metered = models.BooleanField(default=False)
    lede_image = models.JSONField(default=dict)
    lede_video = models.JSONField(default=dict)
    long_url = models.TextField(default="")
    newsletter_tout_label = models.CharField(max_length=255, default="")
    premium = models.BooleanField(default=False)
    primary_category = models.CharField(max_length=255, default="")
    primary_site = models.CharField(max_length=255, default="")
    published = models.IntegerField(default=0)
    readings = models.JSONField(default=dict)
    resource_id = models.CharField(max_length=255, default="")
    resource_type = models.CharField(max_length=255, default="")
    secondary_brands = models.JSONField(default=dict)
    security_i_ds = models.JSONField(default=dict)
    short_url = models.CharField(max_length=255, default="")
    summary = models.TextField(blank=True, default="")
    themed_images = models.JSONField(default=dict)
    title = models.CharField(max_length=255, default="")
    topics = models.JSONField(default=dict)
    type = models.CharField(max_length=255, default="")
    updated_at = models.IntegerField(default=0)
    word_count = models.IntegerField(default=0)
    ai_summary = models.TextField(blank=True, default="")
    auto_generated_summary = models.TextField(blank=True, default="")
    created_at = models.IntegerField(default=timezone.now().timestamp())
    status = models.IntegerField(default=0)

    @staticmethod
    def get_text_from_components(components: str) -> str:
        """
            Given a JSON string of a BBFinanceStory's components, return a concatenated string of all text components
        """
        components = json.loads(components)
        result = ""
        for component in components:
            if component.get("role") != 'p' or component.get("role") != 'correction':
                space = " "
            else:
                space = ""
            for part in component["parts"]:
                if part.get("parts"):
                    for sub_part in part["parts"]:
                        if sub_part.get("role") == "text":
                            result += sub_part.get("text", "")
                else:
                    if part.get("role") == "text":
                        result += part.get("text", "") + space
        return result
    
    @staticmethod
    def get_text_from_components_by_class(components: str) -> str:
        components = json.loads(components)
        result = []
        for component in components:
            if component['role'] == 'image' or component['role'] == 'video':
                continue
            if "parts" in component:
                for part in component['parts']:
                    if "parts" in part:
                        for pp in part['parts']:
                            result.append(pp['text'])
                    else:
                        result.append(part['text'])
        return "".join(result)
            

    def __str__(self):
        return self.title
        
