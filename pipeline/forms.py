import json

from django import forms
from django_select2.forms import Select2MultipleWidget
from .models import knowledge_models, RAGRetrieverConfig
from django import forms
from .models import RAGRetrieverConfig
from flat_json_widget.widgets import FlatJsonWidget


class CreateSimplePipelineForm(forms.Form):
    name = forms.CharField(
        label='Name',
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500',
            'placeholder': 'Pipeline Name'
        })
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500',
            'placeholder': 'Description'
        })
    )
    knowledge = forms.ModelMultipleChoiceField(
        queryset=knowledge_models.Knowledge.objects.all(),
        widget=Select2MultipleWidget(attrs={
            'class': 'select2-multiple bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500'}),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].label_attrs = {'class': 'block mb-2 text-sm font-medium text-gray-900 dark:text-white'}


class RAGRetrieverConfigForm(forms.ModelForm):
    class Meta:
        model = RAGRetrieverConfig
        fields = '__all__'
        widgets = {
            'model_preamble': forms.Textarea(attrs={'rows': 4,
                                                    'class': 'block w-full mt-1 p-2.5 bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500'}),
            'grade_preamble': forms.Textarea(attrs={'rows': 4,
                                                    'class': 'block w-full mt-1 p-2.5 bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500'}),
            'route_question_preamble': forms.Textarea(attrs={'rows': 4,
                                                             'class': 'block w-full mt-1 p-2.5 bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500'}),
            'enable_history': forms.Textarea(attrs={'rows': 4,
                                                    'class': 'block w-full mt-1 p-2.5 bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500'}),
            'hallucination_preamble': forms.Textarea(attrs={'rows': 4,
                                                            'class': 'block w-full mt-1 p-2.5 bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500'}),
            'answer_preamble': forms.Textarea(attrs={'rows': 4,
                                                     'class': 'block w-full mt-1 p-2.5 bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500'}),
            'grade_prompt': forms.Textarea(attrs={'rows': 4,
                                                  'class': 'block w-full mt-1 p-2.5 bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500'}),
            'hallucination_prompt': forms.Textarea(attrs={'rows': 4,
                                                          'class': 'block w-full mt-1 p-2.5 bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500'}),
            'answer_prompt': forms.Textarea(attrs={'rows': 4,
                                                   'class': 'block w-full mt-1 p-2.5 bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500'}),
            'llm_provider': forms.TextInput(attrs={
                'class': 'block w-full mt-1 p-2.5 bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500'}),
            'model_name': forms.TextInput(attrs={
                'class': 'block w-full mt-1 p-2.5 bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500'}),
            'model_args': forms.NumberInput(attrs={
                'class': 'block w-full mt-1 p-2.5 bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500'}),
            'embedding_provider': forms.TextInput(attrs={
                'class': 'block w-full mt-1 p-2.5 bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500'}),
            'embedding_model': forms.TextInput(attrs={
                'class': 'block w-full mt-1 p-2.5 bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500'}),
            'ocr_url': forms.URLInput(attrs={
                'class': 'block w-full mt-1 p-2.5 bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500'}),
            'ocr_api_key': forms.TextInput(attrs={
                'class': 'block w-full mt-1 p-2.5 bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500'}),
        }


class FlowbiteFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            self.apply_flowbite_style(field)

    def apply_flowbite_style(self, field):
        # Default classes for all fields
        default_classes = "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"

        # Add default classes to the field
        field.widget.attrs['class'] = default_classes

        # Additional styling based on field type
        if isinstance(field.widget, forms.CheckboxInput):
            field.widget.attrs[
                'class'] = "w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
        elif isinstance(field.widget, forms.Select):
            field.widget.attrs[
                'class'] = "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"


class KeyValueWidget(forms.Widget):
    template_name = 'widgets/key_value_widget.html'

    def __init__(self, attrs=None):
        super().__init__(attrs)

    def value_from_datadict(self, data, files, name):
        keys = data.getlist(f'{name}_key')
        values = data.getlist(f'{name}_value')
        dic = dict(zip(keys, values))
        return json.dumps({k: v for k, v in dic.items() if v})

    def format_value(self, value):
        if not value:
            return []
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                value = {}
        if isinstance(value, dict):
            return value.items()
        return []

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['value'] = self.format_value(value)
        return context


class PartiallyMaskedTextInput(forms.TextInput):
    template_name = 'widgets/partially_masked_text_input.html'

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if value:
            visible_part = value[:5]
            masked_part = '*' * (len(value) - 5)
            context['widget']['masked_value'] = visible_part + masked_part
        return context


class ModelForm(FlowbiteFormMixin, forms.ModelForm):
    class Meta:
        model = RAGRetrieverConfig
        fields = ["llm_provider", "model_name", "model_api_key", "model_args", "model_preamble"]
        widgets = {
            'model_args': KeyValueWidget(),
            "model_api_key": PartiallyMaskedTextInput(),
        }
        help_texts = {
            'llm_provider': 'Select the LLM provider you want to use.',
            'model_name': 'Enter the name of the model.',
            'model_api_key': 'Enter the API key for the model.',
            'model_args': 'Enter the arguments for the model as key-value pairs.',
            'model_preamble': 'Enter the preamble text for the model.',
        }


class EmbeddingForm(FlowbiteFormMixin, forms.ModelForm):


    class Meta:
        model = RAGRetrieverConfig
        fields = ["embedding_provider", "embedding_model", "embedding_api_key", "embedding_args"]
        widgets = {
            'embedding_args': KeyValueWidget(),
            "embedding_api_key": PartiallyMaskedTextInput(),
        }
        help_texts = {
            'embedding_provider': 'Select the embedding provider you want to use.',
            'embedding_model': 'Enter the name of the embedding model.',
            'embedding_api_key': 'Enter the API key for the embedding model.',
            'embedding_args': 'Enter the arguments for the embedding model as key-value pairs.',
        }


class RouteQuestionForm(FlowbiteFormMixin, forms.ModelForm):
    class Meta:
        model = RAGRetrieverConfig
        fields = ["route_question_preamble", "enable_history"]
        help_texts = {
            'route_question_preamble': 'Enter the preamble text for routing questions.',
            'enable_history': 'Enable or disable conversation history awareness  tracking for routing questions.',
        }


class GraderForm(FlowbiteFormMixin, forms.ModelForm):
    class Meta:
        model = RAGRetrieverConfig
        fields = ["grade_preamble", "grade_prompt"]
        help_texts = {
            'grade_preamble': 'Enter the preamble text for grading the output of the model.',
            'grade_prompt': 'Enter the prompt text for grading the output of the model.',
        }


class HallucinationForm(FlowbiteFormMixin, forms.ModelForm):
    class Meta:
        model = RAGRetrieverConfig
        fields = ["hallucination_preamble", "hallucination_prompt"]
        help_texts = {
            'hallucination_preamble': 'Enter the preamble text for hallucination detection.',
            'hallucination_prompt': 'Enter the prompt text for hallucination detection.',
        }


class AnswerForm(FlowbiteFormMixin, forms.ModelForm):
    class Meta:
        model = RAGRetrieverConfig
        fields = ["answer_preamble", "answer_prompt"]
        help_texts = {
            'answer_preamble': 'Enter the preamble text for generating answers for questions.',
            'answer_prompt': 'Enter the prompt text for generating answers for questions.',
        }
