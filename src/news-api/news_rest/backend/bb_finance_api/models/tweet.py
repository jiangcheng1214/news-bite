from django.db import models
from django.db.models import JSONField
from .author_metadata import AuthorMetadata

class Tweet(models.Model):
    author = models.ForeignKey(AuthorMetadata, on_delete=models.CASCADE)
    created_at = models.DateTimeField()
    edit_history_tweet_ids = JSONField()
    entities = JSONField()
    tweet_id = models.CharField(max_length=255, primary_key=True)
    lang = models.CharField(max_length=10)
    text = models.TextField()
