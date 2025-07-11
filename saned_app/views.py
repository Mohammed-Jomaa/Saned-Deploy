from django.shortcuts import render, redirect
from .models import *
from django.http import JsonResponse
import bcrypt, json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse,HttpResponseForbidden
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
            redirect_url ='/ngo/dashboard'

        return JsonResponse({'success': True, 'redirect_url': redirect_url})

    return JsonResponse({'success': False, 'errors': {'general': 'طلب غير صالح'}})


def beneficiary_dashboard(request):
    if 'user_id' not in request.session or request.session.get('role') != 'beneficiary':
        return redirect('login')
    return render(request, 'beneficiary/dashboard.html')

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
def ngo_dashboard(request):
    if request.method=="POST":
        organization_name=request.POST.get('organization_name')
        license_document=request.FILES.get('license_document')
        if not organization_name:
            messages.error(request,'اسم المنظمة مطلوب')
        elif not license_document:
            messages.error(request,'وثيقة الترخيص مطلوبة')
        else:
            user_id = request.session.get('user_id')
            user=User.objects.get(id=user_id)
            ngo_profile=NGOProfile.objects.create(
                user=user,
                organization_name=organization_name,
                license_document=license_document,
                approved=False
            )
            messages.success(request, 'بالامكان المتابعة وانشاء حملة او النظرالى طلبات المساعدات والمساهمة فيها') 
            return redirect('ngo_create')
    return render(request,'ngo/dashboard.html')

def ngo_create(request):
   
    user_id = request.session.get('user_id')
    if not user_id:
       
        messages.error(request, "يجب تسجيل الدخول أولاً.")
        return redirect('login')
    try:
        user=User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "المستخدم غير موجود.")
        return redirect('login')

    profile = NGOProfile.objects.filter(user=user).first()
    if profile is None:
        messages.error(request, "لا يوجد ملف منظمة مرتبط بهذا المستخدم.")
        return redirect('ngo_dashboard')

    if profile.approved:
        
        return render(request, 'ngo/create.html', {'profile': profile})
    else:
       
        messages.info(request, "طلبك قيد المراجعة من قبل المسؤول.")
        return redirect('ngo_dashboard')

def create_campaign(request):
    
    return render(request, 'ngo/create_campaign.html')

def campaign_detail(request):
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        if not user_id:
           messages.error(request, "Please log in first.")
           return redirect('login')

        try:
          user = User.objects.get(id=user_id)
        except User.DoesNotExist:
          messages.error(request, "User not found.")
          return redirect('login')
    
        ngo_profile = NGOProfile.objects.filter(user=user, approved=True).first()
        if not ngo_profile:
            messages.error(request, "لا يمكنك إنشاء حملة لأن ملفك غير معتمد أو غير موجود.")
            return redirect('ngo_dashboard')

        title = request.POST.get('title')
        description = request.POST.get('description')
        goal_amount = request.POST.get('goal_amount')
        deadline = request.POST.get('deadline')  
        campaign = Campaign.objects.create(
            title=title,
            description=description,
            goal_amount=goal_amount,
            deadline=deadline,
            ngo=ngo_profile
        )
        messages.success(request, "تم إنشاء الحملة بنجاح.")
        campaign=Campaign.objects.all()
        return render(request,'ngo/campaign_detail.html',{'campaign':campaign})
