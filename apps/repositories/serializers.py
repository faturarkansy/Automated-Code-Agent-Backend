from rest_framework import serializers
from .models import Repository

class RepositorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Repository
        fields = ['id', 'name', 'clone_url', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

class WebhookPayloadSerializer(serializers.Serializer):
    commit_hash = serializers.CharField(max_length=40, required=True)
    branch = serializers.CharField(max_length=100, default='main')
    author = serializers.CharField(max_length=100, required=False, allow_blank=True)
    code_diff = serializers.CharField(required=True)