from rest_framework.routers import DefaultRouter
from .views import AnalysisRunViewSet

router = DefaultRouter()
router.register(r'audit-runs', AnalysisRunViewSet, basename='audit-run')

urlpatterns = router.urls