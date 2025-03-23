from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DestinationViewSet, TravelAdviceViewSet, home

router = DefaultRouter()
router.register(r'destinations', DestinationViewSet)
router.register(r'advice', TravelAdviceViewSet)

urlpatterns = [
    path('', home, name='home'),
    path('api/', include(router.urls)),
] 