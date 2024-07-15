from rest_framework import serializers
from .models import Pipeline


class PipelineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pipeline
        fields = ['id', 'creator', 'name', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    creator = serializers.StringRelatedField(
        read_only=True)  # or you can use serializers.PrimaryKeyRelatedField if you need the creator's ID
