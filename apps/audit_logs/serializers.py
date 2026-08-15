from rest_framework import serializers
from .models import AnalysisRun

class AnalysisRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisRun
        fields = '__all__'
        read_only_fields = ['id', 'created_at']