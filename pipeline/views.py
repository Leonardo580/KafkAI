from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.views.generic.edit import CreateView, FormView, DeleteView, UpdateView
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views import View
from react.render import render_component

from .models import Pipeline, PipelineProgress, RAGRetrieverConfig
from .serializers import PipelineSerializer
from .tasks import launch_pipeline_task
from rest_framework import viewsets
from knowledge.models import Knowledge
from pipeline.forms import CreateSimplePipelineForm, RAGRetrieverConfigForm, ModelForm, EmbeddingForm, \
    RouteQuestionForm, GraderForm, HallucinationForm, AnswerForm
from pipeline.models import Pipeline
from users.views import AdminRequiredMixin
from rest_framework.response import Response
from formtools.wizard.views import SessionWizardView


# Create your views here.
class PipelineView(AdminRequiredMixin, ListView):
    model = Pipeline
    template_name = 'pipeline/show.html'
    context_object_name = 'pipelines'


class CreateSimplePipelineView(AdminRequiredMixin, FormView):
    form_class = CreateSimplePipelineForm
    template_name = 'pipeline/create_simple_pipeline.html'
    success_url = reverse_lazy('show_pipeline')  # Replace with your actual success URL

    def form_valid(self, form):
        # Create Pipeline instance
        config = RAGRetrieverConfig.objects.create()
        pipeline = Pipeline.objects.create(
            name=form.cleaned_data['name'],
            description=form.cleaned_data['description'],
            creator=self.request.user,
            config=config
        )
        knowledge_ids = form.cleaned_data['knowledge']
        pipeline.knowledge.set(knowledge_ids)
        pipeline.save()
        return super().form_valid(form)


class UpdateAdvancedPipelineView(AdminRequiredMixin, SessionWizardView):
    template_name = 'pipeline/create_advanced_pipeline.html'
    form_list = [ModelForm, EmbeddingForm, RouteQuestionForm, GraderForm, HallucinationForm, AnswerForm]
    success_url = reverse_lazy('show_pipeline')

    def get_form_instance(self, queryset=None):
        return get_object_or_404(Pipeline, id=self.kwargs['pk']).config

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        headers = [
            "This form is used to configure the Language Model (LLM) settings, including selecting the LLM provider, specifying the model name, providing the API key, setting model arguments, and defining the model preamble.",
            "This form allows users to configure the embedding model settings. Users can select the embedding provider, specify the embedding model, provide the API key, and set the embedding model arguments.",
            "This form is used to set up routing questions, including defining the preamble text for routing questions and enabling or disabling history tracking for these questions.",
            "This form is designed for configuring grading settings. It includes fields for setting the preamble text for grading and specifying the grading prompt.",
            "This form is used to configure hallucination detection settings. Users can set the preamble text for hallucination detection and define the hallucination detection prompt.",
            "This form allows users to configure the settings for answering questions. It includes fields for setting the preamble text for answering questions and specifying the answering prompt."
        ]
        context['headers'] = headers
        return context

    def done(self, form_list, **kwargs):
        instance = self.get_form_instance(0)
        for form in form_list:
            if form.is_valid():
                for field, value in form.cleaned_data.items():
                    if isinstance(value, dict):
                        value = {k: self.convert_string(v) for k, v in value.items()}
                    setattr(instance, field, value)
        instance.save()
        return redirect(self.success_url)

    def convert_string(self, value):
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value


def test(request):
    # context = {
    #     'component': render_component(path='../static/react/components/multiStepForm.jsx', props= {'name': 'World'}),
    # }
    return render(request, 'pipeline/test.html')


class EditSimplePipelineView(AdminRequiredMixin, FormView):
    form_class = CreateSimplePipelineForm
    template_name = 'pipeline/update_simple_pipeline.html'
    success_url = reverse_lazy('show_pipeline')  # Replace with your actual success URL

    def get_object(self):
        return get_object_or_404(Pipeline, id=self.kwargs['pk'])

    def get_initial(self):
        pipeline = self.get_object()
        initial = super().get_initial()
        initial.update({
            'name': pipeline.name,
            'description': pipeline.description,
            'knowledge': pipeline.knowledge.all(),
        })
        return initial

    def form_valid(self, form):
        pipeline = self.get_object()

        # Update the associated Pipeline instance
        pipeline.name = form.cleaned_data['name']
        pipeline.description = form.cleaned_data['description']
        pipeline.save()

        # Update the many-to-many relationship
        knowledge_ids = form.cleaned_data['knowledge']
        pipeline.knowledge.set(knowledge_ids)

        return super().form_valid(form)


class DeletePipelineView(AdminRequiredMixin, DeleteView):
    model = Pipeline
    template_name = 'pipeline/delete_pipeline.html'
    success_url = reverse_lazy('show_pipeline')


class LaunchPipelineView(AdminRequiredMixin, View):
    def get(self, request, pk):
        pipeline = get_object_or_404(Pipeline, pk=pk)
        pipeline_progress, created = PipelineProgress.objects.get_or_create(pipeline=pipeline, status='running')

        launch_pipeline_task.delay(pipeline_progress.pk)
        return JsonResponse({'status': 'Pipeline launched'})


class GetProgressView(View):
    def get(self, request, pk):
        pipeline = get_object_or_404(Pipeline, pk=pk)
        current_progress = PipelineProgress.objects.filter(pipeline=pipeline) \
            .order_by('-last_updated').first()
        return JsonResponse({'progress': current_progress.progress, 'status': current_progress.status})


class GetPipelinesView(viewsets.ModelViewSet):
    serializer_class = PipelineSerializer
    queryset = Pipeline.objects.filter(is_active=True).order_by('name')

    def list(self, request, *args, **kwargs):
        query = self.get_queryset()
        serializer = self.get_serializer(query, many=True)
        return Response(serializer.data)
