from django.urls import path, re_path
from . import views
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GetPipelinesView

# Create a router and register the viewset
router = DefaultRouter()
router.register(r'', GetPipelinesView, basename='pipeline')
urlpatterns = [
    path('show/', views.PipelineView.as_view(), name='show_pipeline'),
    path('create_simple_pipeline/', views.CreateSimplePipelineView.as_view(), name='create_simple_pipeline'),
    path('update_advanced_pipeline/<int:pk>', views.UpdateAdvancedPipelineView.as_view(),
         name='update_advanced_pipeline'),
    path("index/", views.test, name="test"),
    path('edit_simple_pipeline/<int:pk>/', views.EditSimplePipelineView.as_view(), name='edit_simple_pipeline'),
    path('delete_simple_pipeline/<int:pk>/', views.DeletePipelineView.as_view(), name='delete_pipeline'),
    path('launch_pipeline/<int:pk>/', views.LaunchPipelineView.as_view(), name='launch_pipeline'),
    path('get_progress/<int:pk>/', views.GetProgressView.as_view(), name='get_progress'),
    path('list/', include(router.urls)),

]
