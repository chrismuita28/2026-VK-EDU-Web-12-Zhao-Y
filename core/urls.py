from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("profile", views.profile, name="profile"),
    path('profile/<str:nickname>/', views.profile, name="profile_by_nickname"),
    path("login", views.user_login, name="login"),
    path("signup", views.signup, name="signup"),
    path("logout", views.user_logout, name="logout"),
    path("edit_profile", views.edit_profile, name="edit_profile")
]
