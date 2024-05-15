# serializers.py
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.relations import SlugRelatedField
from .models import KnowledgeBase, Tag


class TagRelatedField(SlugRelatedField):
    def to_internal_value(self, data):
        try:
            return self.get_queryset().get_or_create(**{self.slug_field: data})[0]
        except ObjectDoesNotExist:
            self.fail('does_not_exist', slug_name=self.slug_field, value=data)
        except (TypeError, ValueError):
            self.fail('invalid')


class KnowledgeBaseSerializer(serializers.ModelSerializer):
    related_knowledge_base = serializers.PrimaryKeyRelatedField(
        queryset=KnowledgeBase.objects.all(),
        allow_null=True,
        required=False,
    )
    tags = TagRelatedField(
        slug_field='name',
        queryset=Tag.objects.all(),
        many=True,
    )

    class Meta:
        model = KnowledgeBase
        fields = ['subject', 'question', 'answer', 'related_knowledge_base', 'tags']

    def create(self, validated_data):
        tags_data = validated_data.pop('tags', [])
        related_knowledge_base_data = validated_data.pop('related_knowledge_base', None)
        knowledge_base = KnowledgeBase.objects.create(**validated_data)

        for tag in tags_data:
            knowledge_base.tags.add(tag)

        if related_knowledge_base_data:
            related_knowledge_base = KnowledgeBase.objects.get(pk=related_knowledge_base_data.pk)
            knowledge_base.related_knowledge_base = related_knowledge_base

        knowledge_base.save()
        return knowledge_base
