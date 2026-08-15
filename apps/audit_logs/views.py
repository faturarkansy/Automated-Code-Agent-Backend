from rest_framework import viewsets
from .models import AnalysisRun
from .serializers import AnalysisRunSerializer

class AnalysisRunViewSet(viewsets.ReadOnlyModelViewSet):
    """Endpoint Read-Only untuk memantau status dan hasil analisis agent."""
    serializer_class = AnalysisRunSerializer

    def get_queryset(self):
        queryset = AnalysisRun.objects.select_related('repository').all()
        repo_id = self.request.query_params.get('repository_id')
        if repo_id:
            queryset = queryset.filter(repository_id=repo_id)
        return queryset