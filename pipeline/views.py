from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.views.generic.edit import CreateView, FormView, UpdateView

from knowledge.models import Knowledge
from pipeline.forms import CreateSimplePipelineForm
from pipeline.models import Pipeline, SimplePipeline


# Create your views here.
class PipelineView(ListView):
    model = Pipeline
    template_name = 'pipeline/show.html'
    context_object_name = 'pipelines'


class CreateSimplePipelineView(FormView):
    form_class = CreateSimplePipelineForm
    template_name = 'pipeline/create_simple_pipeline.html'
    success_url = reverse_lazy('show_pipeline')  # Replace with your actual success URL

    def form_valid(self, form):
        # Create Pipeline instance
        pipeline = Pipeline.objects.create(
            name=form.cleaned_data['name'],
            description=form.cleaned_data['description'],
            creator=self.request.user  # Assuming you want to set the creator
        )

        # Create SimplePipeline instance
        simple_pipeline = SimplePipeline.objects.create(
            pipeline=pipeline,
            instruction=form.cleaned_data['instruction'],
            variable=form.cleaned_data['variable']
        )

        # Set the many-to-many relationship
        knowledge_ids = form.cleaned_data['knowledge']
        simple_pipeline.knowledge.set(knowledge_ids)

        return super().form_valid(form)


class EditSimplePipelineView(UpdateView):
    model = SimplePipeline
    form_class = CreateSimplePipelineForm
    template_name = 'pipeline/create_simple_pipeline.html'
    success_url = reverse_lazy('show_pipeline')  # Replace with your actual success URL

    def get_object(self, queryset=None):
        return get_object_or_404(SimplePipeline, pk=self.kwargs['pk'])

    def get_initial(self):
        initial = super().get_initial()
        simple_pipeline = self.get_object()
        initial['name'] = simple_pipeline.pipeline.name
        initial['description'] = simple_pipeline.pipeline.description
        initial['instruction'] = simple_pipeline.instruction
        initial['variable'] = simple_pipeline.variable
        initial['knowledge'] = simple_pipeline.knowledge.all()
        return initial

    def form_valid(self, form):
        simple_pipeline = self.get_object()
        pipeline = simple_pipeline.pipeline

        # Update Pipeline instance
        pipeline.name = form.cleaned_data['name']
        pipeline.description = form.cleaned_data['description']
        pipeline.save()

        # Update SimplePipeline instance
        simple_pipeline.instruction = form.cleaned_data['instruction']
        simple_pipeline.variable = form.cleaned_data['variable']
        simple_pipeline.save()

        # Update the many-to-many relationship
        knowledge_ids = form.cleaned_data['knowledge']
        simple_pipeline.knowledge.set(knowledge_ids)

        return super().form_valid(form)
