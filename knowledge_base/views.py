import json

from _testcapi import raise_exception
from django.shortcuts import get_object_or_404
from rest_framework import views, viewsets, status

from rest_framework_api_key.permissions import HasAPIKey
from rest_framework.response import Response

from knowledge_base.models import KnowledgeBase
from knowledge_base.serializers import KnowledgeBaseSerializer


class ReceiveData(views.APIView):
    http_method_names = ["post", "delete"]
    permission_classes = [HasAPIKey]

    def post(self, request, *args, **kwargs):

        serializer = KnowledgeBaseSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        # Get the instance you want to delete
        instance = get_object_or_404(KnowledgeBase, pk=kwargs.get('id'))

        # Delete the instance
        instance.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)



