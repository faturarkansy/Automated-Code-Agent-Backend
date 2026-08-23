from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from .models import AnalysisRun
from .serializers import AnalysisRunSerializer
from .services import AnalyticsService

class AnalysisRunViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AnalysisRun.objects.all().order_by('-created_at')
    serializer_class = AnalysisRunSerializer

class DashboardMetricsView(APIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request, *args, **kwargs):
        repo_id = request.query_params.get("repository_id", None)
        metrics = AnalyticsService.get_dashboard_metrics(repository_id=repo_id)
        return Response(metrics, status=status.HTTP_200_OK)