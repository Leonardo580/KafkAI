# serializers.py
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.relations import SlugRelatedField
from .models import KnowledgeBase, Tag
from . import weaviate_init


class TagRelatedField(SlugRelatedField):
    def to_internal_value(self, data):
        try:
            return self.get_queryset().get_or_create(**{self.slug_field: data})[0]
        except ObjectDoesNotExist:
            self.fail('does_not_exist', slug_name=self.slug_field, value=data)
        except (TypeError, ValueError):
            self.fail('invalid')


class KnowledgeBaseSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
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
        fields = ['id', 'subject', 'question', 'answer', 'related_knowledge_base', 'tags']

    def create(self, validated_data):
        tags_data = validated_data.pop('tags', [])
        related_knowledge_base_data = validated_data.pop('related_knowledge_base', None)
        knowledge_base = None
        if KnowledgeBase.objects.filter(id=validated_data['id']):
            knowledge_base = KnowledgeBase.objects.get(pk=validated_data['id'])
            knowledge_base.subject = validated_data['subject']
            knowledge_base.question = validated_data['question']
            knowledge_base.answer = validated_data['answer']
            knowledge_base.save()
        else:
            knowledge_base = KnowledgeBase.objects.create(**validated_data)
        client = weaviate_init.WeaviateConnector().get_instance().client
        tags = client.collections.get("tags")
        kb = client.collections.get("knowledge_base")
        tags_uuid = 0
        for tag in tags_data:
            knowledge_base.tags.add(tag)
            tags_uuid = tags.data.insert(properties={
                "name": tag.name
            }
            )
        knowledge_base_uuid = kb.data.insert(properties=
        {
            "subject": knowledge_base.subject,
            "question": knowledge_base.question,
            "answer": knowledge_base.answer
        })
        print(knowledge_base_uuid)
        if related_knowledge_base_data:
            related_knowledge_base = KnowledgeBase.objects.get(pk=related_knowledge_base_data.pk)
            knowledge_base.related_knowledge_base = related_knowledge_base
            kb.data.update(knowledge_base_uuid, references={
                "tags": tags_uuid
            })
        # knowledge_base.id = validated_data['id']

        knowledge_base.save()
        return knowledge_base
