from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Repository
from .serializers import RepositorySerializer, WebhookPayloadSerializer
from apps.audit_logs.models import AnalysisRun

class RepositoryViewSet(viewsets.ModelViewSet):
    serializer_class = RepositorySerializer

    def get_queryset(self):
        # Query optimization: select_related jika nanti ada relasi user
        return Repository.objects.filter(is_active=True)

    def perform_create(self, serializer):
        # Default fallback user pertama jika belum pasang auth JWT
        from django.contrib.auth.models import User
        user = self.request.user if self.request.user.is_authenticated else User.objects.first()
        serializer.save(user=user)

    @action(detail=True, methods=['post'], url_path='webhook')
    def receive_webhook(self, request, pk=None):
        repository = self.get_object()
        serializer = WebhookPayloadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        # Buat record analysis run dengan status PENDING
        run = AnalysisRun.objects.create(
            repository=repository,
            commit_hash=data['commit_hash'],
            branch=data.get('branch', 'main'),
            author=data.get('author', ''),
            status=AnalysisRun.StatusChoices.PENDING
        )

        # (Pada Hari ke-3 & 4, langkah ini akan memicu Celery Worker async)
        return Response({
            "message": "Webhook received successfully. Analysis queued.",
            "analysis_id": str(run.id),
            "status": run.status
        }, status=status.HTTP_202_ACCEPTED)