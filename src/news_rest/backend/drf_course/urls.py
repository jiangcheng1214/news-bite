from django.urls import path
from django.contrib import admin
from bb_finance_api import views as bb_finance_api_views
#from core import views as core_views
#from ecommerce import views as ecommerce_views
from rest_framework import routers
from rest_framework.authtoken.views import obtain_auth_token



router = routers.DefaultRouter()
#router.register(r'item', ecommerce_views.ItemViewSet, basename='item')
#router.register(r'order', ecommerce_views.OrderViewSet, basename='order')
router.register(r'bb-finance-stories', bb_finance_api_views.BBFinanceStoryViewSet)


urlpatterns = router.urls

urlpatterns += [
    path('admin/', admin.site.urls),
    #path('contact/', core_views.ContactAPIView.as_view()),
    path('api-token-auth/', obtain_auth_token),
]