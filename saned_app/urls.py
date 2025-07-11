from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('create_user/', views.create_user, name='create_user'),
    path('login_user/', views.login_user, name='login_user'),
    path('beneficiary/dashboard/', views.beneficiary_dashboard, name='beneficiary_dashboard'),
    path('ngo/dashboard/', views.ngo_dashboard, name='ngo_dashboard'),
    path('donor/dashboard/',views.donor_dashboard,name='donor_dashboard'),
    path('ngo/create/', views.ngo_create, name='ngo_create'),
    path('ngo/create_campaign/', views.create_campaign, name='create_campaign'),
    path('ngo/campaign_detail/', views.campaign_detail, name='campaign_detail'),
    path('beneficiary/my-requests/', views.my_requests, name='my_requests'),
    path('beneficiary/aid-request/', views.aid_request_form, name='aid_request_form'),
    path('beneficiary/submit-request/', views.submit_aid_request, name='submit_aid_request'),
    path('donor/donate_to_campaign/<int:campaign_id>/',views.donate_to_campaign,name="donate_to_campaign")
    
 
]