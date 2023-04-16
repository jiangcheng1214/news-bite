from django.db import models
from django.db.models import JSONField

class AuthorMetadata(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    url = models.URLField()
    description = models.TextField()
    protected = models.BooleanField()
    verified = models.BooleanField()
    location = models.CharField(max_length=255)
    created_at = models.DateTimeField()
    public_metrics = JSONField()
