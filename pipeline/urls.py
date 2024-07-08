from django.urls import path, include
from . import views

urlpatterns = [
    path('show/', views.PipelineView.as_view(), name='show_pipeline'),
    path('create_simple_pipeline/', views.CreateSimplePipelineView.as_view(), name='create_simple_pipeline'),
    path('edit_simple_pipeline/<int:pk>/', views.EditSimplePipelineView.as_view(), name='edit_simple_pipeline'),
    path('delete_simple_pipeline/<int:pk>/', views.DeletePipelineView.as_view(), name='delete_pipeline'),
    path('launch_pipeline/<int:pk>/', views.LaunchPipelineView.as_view(), name='launch_pipeline'),
    path('get_progress/<int:pk>/', views.GetProgressView.as_view(), name='get_progress'),
]
