from django.urls import path

from .views import attempt_quiz, quiz_home, quiz_result

app_name = 'quiz'

urlpatterns = [
    path('', quiz_home, name='home'),
    path('attempt/', attempt_quiz, name='attempt'),
    path('result/<int:attempt_id>/', quiz_result, name='result'),
]
