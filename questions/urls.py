from django.urls import path

from . import views

app_name = "questions"

urlpatterns = [
    path("", views.index, name="index"),
    path("hot", views.hot, name="hot"),
    path("tag/<str:tag_name>", views.tag, name="tag"),
    path("question/<int:question_id>", views.question, name="question"),
    path("ask", views.ask, name="ask"),
    path("question/<int:question_id>/like/", views.like_question, name="like_question"),
    path("answer/<int:answer_id>/like/", views.like_answer, name="like_answer"),
    path('answer/<int:answer_id>/mark-best/', views.mark_best_answer, name='mark_best_answer')
]
