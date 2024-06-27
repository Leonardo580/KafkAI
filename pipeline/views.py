from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.views.generic.edit import CreateView, FormView, DeleteView

from knowledge.models import Knowledge
from pipeline.forms import CreateSimplePipelineForm
from pipeline.models import Pipeline, SimplePipeline, PipelineConfig
from users.views import AdminRequiredMixin


# Create your views here.
class PipelineView(AdminRequiredMixin, ListView):
    model = Pipeline
    template_name = 'pipeline/show.html'
    context_object_name = 'pipelines'


class CreateSimplePipelineView(AdminRequiredMixin,FormView):
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
        config = PipelineConfig.objects.create()
        # Create SimplePipeline instance
        simple_pipeline = SimplePipeline.objects.create(
            pipeline=pipeline,
            instruction=form.cleaned_data['instruction'],
            variable=form.cleaned_data['variable'],
            config=config
        )

        # Set the many-to-many relationship
        knowledge_ids = form.cleaned_data['knowledge']
        simple_pipeline.knowledge.set(knowledge_ids)

        return super().form_valid(form)


class EditSimplePipelineView(AdminRequiredMixin,FormView):
    form_class = CreateSimplePipelineForm
    template_name = 'pipeline/update_simple_pipeline.html'
    success_url = reverse_lazy('show_pipeline')  # Replace with your actual success URL

    def get_object(self):
        return get_object_or_404(Pipeline, id=self.kwargs['pk'])

    def get_initial(self):
        pipeline = self.get_object()
        simple_pipeline = SimplePipeline.objects.get(pipeline=pipeline)
        initial = super().get_initial()
        initial.update({
            'name': pipeline.name,
            'description': pipeline.description,
            'instruction': simple_pipeline.instruction,
            'variable': simple_pipeline.variable,
            'knowledge': simple_pipeline.knowledge.all(),
        })
        return initial

    def form_valid(self, form):
        pipeline = self.get_object()
        simple_pipeline = SimplePipeline.objects.get(pipeline=pipeline)

        # Update the associated Pipeline instance
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


class DeletePipelineView(AdminRequiredMixin, DeleteView):
    model = Pipeline
    template_name = 'pipeline/delete_pipeline.html'
    success_url = reverse_lazy('show_pipeline')
