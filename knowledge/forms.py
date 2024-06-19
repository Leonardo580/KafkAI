from django import forms
from django.forms import inlineformset_factory
from .models import Knowledge, KnowledgeFile


class KnowledgeForm(forms.ModelForm):
    class Meta:
        model = Knowledge
        fields = ['title', 'description']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3}),
        }


class KnowledgeFileForm(forms.ModelForm):
    class Meta:
        model = KnowledgeFile
        fields = ['file', 'file_type']

