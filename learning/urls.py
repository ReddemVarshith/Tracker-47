from django.urls import path
from . import views

app_name = 'learning'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('module/<int:module_id>/', views.module_detail, name='module_detail'),
    path('problem/<int:problem_id>/', views.problem_detail, name='problem_detail'),
    path('problem/<int:problem_id>/toggle/', views.toggle_problem_status, name='toggle_problem_status'),
    path('api/execute-code/', views.execute_code, name='execute_code'),
    path('quiz/<int:module_id>/', views.module_quiz, name='module_quiz'),
    path('quiz/<int:module_id>/submit/', views.quiz_submit, name='quiz_submit'),
    path('quiz/attempt/<int:attempt_id>/results/', views.quiz_results, name='quiz_results'),
    path('quiz/history/', views.quiz_history, name='quiz_history'),
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-review/', views.admin_quiz_list, name='admin_quiz_list'),
    path('admin-review/<int:attempt_id>/', views.admin_quiz_review, name='admin_quiz_review'),
    path('admin-review/action/', views.admin_review_action, name='admin_review_action'),
]
