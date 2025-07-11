from django.shortcuts import render, redirect
from .models import *
from django.http import JsonResponse,HttpResponseForbidden
import bcrypt, json
from django.contrib import messages


def index(request):
    return render(request, 'index.html')


def register(request):
    cities = [
        "القدس", "رام الله", "البيرة", "نابلس", "الخليل", "بيت لحم",
        "قلقيلية", "طولكرم", "جنين", "سلفيت", "أريحا", "طوباس"
    ]    
    return render(request, 'auth/register.html', {'cities': cities})

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

        if data.get('role') == 'ngo' and files.get('licenseDocument'):
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
        request.session['role'] = user.role
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

def logout_user(request):
    request.session.flush()
    return redirect('/')

def beneficiary_dashboard(request):
    if 'user_id' not in request.session or request.session.get('role') != 'beneficiary':
        return redirect('login')
    user_id = request.session.get('user_id')
    recent_requests = AidRequest.objects.filter(beneficiary_id=user_id).order_by('-created_at')[:3]
    return render(request, 'beneficiary/dashboard.html', {
        'recent_requests': recent_requests
    })

def my_requests(request):
    if 'user_id' not in request.session:
        return redirect('login')   

    user = User.objects.get(id=request.session['user_id'])

    if user.role != 'beneficiary':
        return redirect('/')   

    aid_requests = AidRequest.objects.filter(beneficiary=user).order_by('-created_at')
    return render(request, 'beneficiary/my_requests.html', {'aid_requests': aid_requests})
    
def aid_request_form(request):
    if 'user_id' not in request.session:
        return redirect('login')

    user = User.objects.filter(id=request.session['user_id']).first()
    if not user or user.role != 'beneficiary':
        return HttpResponseForbidden("ليس لديك صلاحية الوصول إلى هذه الصفحة.")

    return render(request, 'beneficiary/aid_request_form.html')

def submit_aid_request(request):
    if request.method == 'POST':
        if 'user_id' not in request.session:
            return redirect('login')

        user = User.objects.filter(id=request.session['user_id']).first()
        if not user or user.role != 'beneficiary':
            return HttpResponseForbidden("ليس لديك صلاحية.")

        type = request.POST.get('type', '').strip()
        description = request.POST.get('description', '').strip()
        amount = request.POST.get('amount', '').strip()
        document = request.FILES.get('document')

        errors = {}
        if not type:
            errors['type'] = "يرجى كتابة نوع المساعدة المطلوبة"
        if not description:
            errors['description'] = "يرجى إدخال وصف للمساعدة"
        if not amount.isdigit():
            errors['amount'] = "يرجى إدخال مبلغ صحيح"
        if not document:
            errors['document'] = "يرجى رفع مستند يوضح الحالة"

        if errors:
            return render(request, 'beneficiary/aid_request_form.html', {'errors': errors})

        AidRequest.objects.create(
            type=type,
            description=description,
            amount_requested=int(amount),
            document=document,
            beneficiary=user
        )

        return redirect('beneficiary_dashboard')  
    return HttpResponseForbidden("طريقة غير مسموح بها.")

def delete_aid_request(request, request_id):
    if 'user_id' not in request.session or request.session.get('role') != 'beneficiary':
        return redirect('login')

    aid_request = AidRequest.objects.filter(id=request_id, beneficiary_id=request.session['user_id']).first()

    if not aid_request:
        messages.error(request, "الطلب غير موجود أو غير مسموح لك بحذفه.")
        return redirect('my_requests')

    if aid_request.status != 'pending':
        messages.error(request, "لا يمكنك حذف طلب تمت مراجعته أو الموافقة عليه.")
        return redirect('my_requests')

    aid_request.delete()
    messages.success(request, "تم حذف الطلب بنجاح.")
    return redirect('my_requests')