from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('create_user/', views.create_user, name='create_user'),
    path('login_user/', views.login_user, name='login_user'),
    path('logout/', views.logout_user, name='logout'),
    path('beneficiary/dashboard/', views.beneficiary_dashboard, name='beneficiary_dashboard'),
    path('beneficiary/request/', views.aid_request_form, name='aid_request_form'),
    path('beneficiary/my-requests/', views.my_requests, name='my_requests'),
    path('beneficiary/aid-request/', views.aid_request_form, name='aid_request_form'),
    path('beneficiary/submit-request/', views.submit_aid_request, name='submit_aid_request'),
    path('beneficiary/delete-request/<int:request_id>/', views.delete_aid_request, name='delete_aid_request'),

]
