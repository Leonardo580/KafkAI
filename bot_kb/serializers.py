# serializers.py
from rest_framework import serializers
from .models import KnowledgeBase, Issue, Tag


class KnowledgeBaseSerializer(serializers.ModelSerializer):
    related_issue_id = serializers.PrimaryKeyRelatedField(queryset=Issue.objects.all(), source='related_issue')
    tags = serializers.SlugRelatedField(slug_field='name', queryset=Tag.objects.all(), many=True)

    class Meta:
        model = KnowledgeBase
        fields = ['subject', 'question', 'answer', 'related_issue_id', 'tags']

    def create(self, validated_data):
        tags_data = validated_data.pop('tags')
        knowledge_base = KnowledgeBase.objects.create(**validated_data)
        for tag_name in tags_data:
            tag, created = Tag.objects.get_or_create(name=tag_name)
            knowledge_base.tags.add(tag)
        return knowledge_base
