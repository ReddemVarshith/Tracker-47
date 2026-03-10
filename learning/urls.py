from django.urls import path
from . import views

app_name = 'learning'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('module/<int:module_id>/', views.module_detail, name='module_detail'),
    path('problem/<int:problem_id>/', views.problem_detail, name='problem_detail'),
    path('problem/<int:problem_id>/toggle/', views.toggle_problem_status, name='toggle_problem_status'),
    path('api/execute-code/', views.execute_code, name='execute_code'),
]
