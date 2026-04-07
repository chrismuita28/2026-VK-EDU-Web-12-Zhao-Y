from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("profile", views.profile, name="profile"),
    path("login", views.user_login, name="login"),
    path("signup", views.signup, name="signup")
]
