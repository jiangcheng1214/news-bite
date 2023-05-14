from rest_framework import serializers
from .models import BBFinanceStory

class BBFinanceStorySerializer(serializers.ModelSerializer):
    #created = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)
    #ai_summary = serializers.CharField(max_length=500)

    class Meta:
        model = BBFinanceStory
        fields = '__all__'
