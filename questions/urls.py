from django.urls import path

from . import views

app_name = "questions"

urlpatterns = [
    path("", views.index, name="index"),
    path("hot", views.hot, name="hot"),
    path("tag/<str:tag_name>", views.tag, name="tag"),
    path("question/<int:question_num>", views.question, name="question"),
    path("ask", views.ask, name="ask")
]
