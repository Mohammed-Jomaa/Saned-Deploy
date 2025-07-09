from django.shortcuts import render, redirect
from .models import User
from django.http import JsonResponse
import bcrypt, json


def index(request):
    return render(request, 'index.html')


def register(request):
    return render(request, 'auth/register.html')

def login(request):
    return render(request, 'auth/login.html')

def create_user(request):
    if request.method == 'POST':
        if request.content_type.startswith('multipart'):
            data = request.POST
            files = request.FILES
        else:
            data = json.loads(request.body)
            files = {}

        errors = User.objects.user_validator(data)

        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        hashed_pw = bcrypt.hashpw(data['registerPassword'].encode(), bcrypt.gensalt()).decode()

        user = User.objects.create(
            first_name=data['registerFirstName'],
            last_name=data['registerLastName'],
            email=data['registerEmail'],
            region=data['registerRegion'],
            password=hashed_pw,
            role=data.get('role', 'beneficiary')
        )

        if data.get('role') == 'ngo' and 'licenseDocument' in files:
            NGOProfile.objects.create(
                organization_name=f"{user.first_name} {user.last_name}",
                license_document=files['licenseDocument'],
                user=user
            )

        request.session['user_id'] = user.id
        request.session['name'] = f"{user.first_name} {user.last_name}"
        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'errors': {'general': 'طلب غير صالح'}})


def login_user(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'errors': {'general': 'بيانات غير صالحة'}})

        errors = User.objects.login_validator(data)

        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        user = User.objects.filter(email=data['loginEmail']).first()
        request.session['user_id'] = user.id
        request.session['name'] = f"{user.first_name} {user.last_name}"

        redirect_url = '/dashboard'
        if user.role == 'beneficiary':
            redirect_url = '/beneficiary/dashboard'
        elif user.role == 'donor':
            redirect_url = '/donor/dashboard'
        elif user.role == 'ngo':
            redirect_url = '/ngo/dashboard'

        return JsonResponse({'success': True, 'redirect_url': redirect_url})

    return JsonResponse({'success': False, 'errors': {'general': 'طلب غير صالح'}})