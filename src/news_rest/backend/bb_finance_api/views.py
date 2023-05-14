from rest_framework import viewsets
from .models import BBFinanceStory
from .serializers import BBFinanceStorySerializer

class BBFinanceStoryViewSet(viewsets.ModelViewSet):
    queryset = BBFinanceStory.objects.all()
    serializer_class = BBFinanceStorySerializer
