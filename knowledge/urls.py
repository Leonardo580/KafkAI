from django.urls import path

from . import views

urlpatterns = [
    path('show/', views.KnowledgeView.as_view(), name='show_knowledge'),
    path('create/', views.CreateKnowledgeView.as_view(), name='create_knowledge'),
    path('delete/<int:knowledge_id>/', views.DeleteKnowledgeView.as_view(), name='delete_knowledge'),
    path('<int:knowledge_id>/files/', views.KnowledgeFilesView.as_view(), name='knowledge_files'),
    path('edit/<int:knowledge_id>/', views.EditKnowledgeView.as_view(), name='edit_knowledge'),
]