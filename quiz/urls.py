from django.urls import path

from . import views

app_name = "quiz"

urlpatterns = [
    path("", views.quiz_home, name="home"),

    path(
        "attempt/",
        views.attempt_quiz,
        name="attempt",
    ),

    path(
        "attempt/<int:page>/",
        views.attempt_quiz,
        name="attempt_page",
    ),

    path(
        "result/<int:attempt_id>/",
        views.quiz_result,
        name="result",
    ),

    path(
        "retry/<int:attempt_id>/",
        views.retry_quiz,
        name="retry",
    ),
]