from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AnalysisRunViewSet, DashboardMetricsView

router = DefaultRouter()
router.register(r'audit-runs', AnalysisRunViewSet, basename='audit-run')

urlpatterns = [
    path('analytics/metrics/', DashboardMetricsView.as_view(), name='dashboard-metrics'),
    path('', include(router.urls)),
]