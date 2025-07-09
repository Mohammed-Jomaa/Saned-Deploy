from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('create_user/', views.create_user, name='create_user'),
    path('login_user/', views.login_user, name='login_user'),
]
