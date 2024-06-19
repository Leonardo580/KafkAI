import json
from pprint import pprint

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from django.forms import inlineformset_factory
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from knowledge.forms import KnowledgeFileForm, KnowledgeForm
from knowledge.models import Knowledge, KnowledgeFile
from users.views import AdminRequiredMixin
from django.views.generic import ListView, CreateView, View


# Create your views here.

class KnowledgeView(AdminRequiredMixin, ListView):
    model = Knowledge
    template_name = 'knowledge/show.html'
    context_object_name = 'knowledge'

    def get_queryset(self):
        user = self.request.user
        return Knowledge.objects.filter(creator=user).order_by('-created_at')


class CreateKnowledgeView(AdminRequiredMixin, View):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):

        try:
            title = request.POST.get('title')
            description = request.POST.get('description')

            # Validate the title and description
            if not title or not description:
                return JsonResponse({'success': False, 'message': 'Title and description are required'}, status=400)

            # Create Knowledge instance
            knowledge = Knowledge.objects.create(
                creator=request.user,
                title=title,
                description=description
            )

            # Process each file
            for key, file in request.FILES.items():
                file_type = file.content_type

                if file_type not in ['text/plain', 'application/pdf', 'application/msword', 'application/vnd.ms-excel',
                                     'text/csv']:
                    return JsonResponse({'success': False, 'message': 'Unknown file type'}, status=400)

                KnowledgeFile.objects.create(
                    knowledge=knowledge,
                    file=file,
                    file_type=file_type
                )

            knowledge.save()

            return JsonResponse({'success': True, 'knowledge_id': knowledge.id})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)


class DeleteKnowledgeView(AdminRequiredMixin, View):
    def post(self, request, knowledge_id):
        try:
            knowledge = Knowledge.objects.get(id=knowledge_id)
            knowledge.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)


class KnowledgeFilesView(View):
    def get(self, request, knowledge_id):
        try:
            knowledge = Knowledge.objects.get(id=knowledge_id)
            files = [{'name': file.file.name} for file in knowledge.files.all()]
            return JsonResponse({'files': files})
        except Knowledge.DoesNotExist:
            return JsonResponse({'error': 'Knowledge not found.'}, status=404)

    def delete(self, request, knowledge_id):
        try:
            knowledge = Knowledge.objects.get(id=knowledge_id)
            body = json.loads(request.body)
            filename = body.get('filename')
            if not filename:
                return JsonResponse({'success': False, 'message': 'Filename is required'}, status=400)

            file_to_delete = None
            for file in knowledge.files.all():
                if file.file.name == filename:
                    file_to_delete = file
                    break

            if file_to_delete:
                file_to_delete.delete()
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'message': 'File not found'}, status=404)

        except Knowledge.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Knowledge not found'}, status=404)


class EditKnowledgeView(AdminRequiredMixin, View):
    def put(self, request, knowledge_id):
        data = json.loads(request.body)
        title = data.get('title')
        description = data.get('description')

        try:
            knowledge = Knowledge.objects.get(id=knowledge_id)
        except ObjectDoesNotExist:
            return JsonResponse({'success': False, 'message': 'Knowledge not found'}, status=404)

        knowledge.title = title
        knowledge.description = description

        with transaction.atomic():
            knowledge.save()
            for key, file in request.FILES.items():
                file_type = file.content_type

                if file_type not in ['text/plain', 'application/pdf', 'application/msword',
                                     'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                                     'application/vnd.ms-excel',
                                     'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                     'text/csv']:
                    return JsonResponse({'success': False, 'message': 'Unknown file type'}, status=400)

                KnowledgeFile.objects.create(
                    knowledge=knowledge,
                    file=file,
                    file_type=file_type
                )

        return JsonResponse({'success': True})
