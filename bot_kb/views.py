import json

from rest_framework import views, viewsets

from rest_framework_api_key.permissions import HasAPIKey
from rest_framework.response import Response


class ReceiveData(views.APIView):
    http_method_names = ["post"]
    permission_classes = [HasAPIKey]

    def post(self, request):
        print(request.data)
        return Response("success")
