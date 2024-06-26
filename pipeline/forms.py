from django import forms

from knowledge.models import Knowledge





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
    instruction = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500',
            'placeholder': 'Enter instructions here',
            'rows': 4
        })
    )
    variable = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500',
            'placeholder': 'Variable'
        })
    )
    knowledge = forms.ModelMultipleChoiceField(
        queryset=Knowledge.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
    )




def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    for field in self.fields:
        self.fields[field].label_attrs = {'class': 'block mb-2 text-sm font-medium text-gray-900 dark:text-white'}
