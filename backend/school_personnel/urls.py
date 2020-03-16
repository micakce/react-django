from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('professor/', views.get_all, name='get_all'),
    path('professor/<int:professor_id>/', views.get_professor, name='get_professor'),
    path('professor/add/', views.add_professor, name='add_professor'),
    path('professor/edit/<int:professor_id>/', views.edit_professor, name='edit_professor'),
    path('professor/delete/<int:professor_id>/', views.delete_professor, name='delete_professor'),
    # path('professor/<int:professor_id>/', views.add_professor, name='add_professor'),
]
