from django.shortcuts import render, redirect
from .models import *
from django.http import JsonResponse, HttpResponseForbidden,HttpResponse
from django.contrib import messages
from django.utils import timezone
import bcrypt, json
from django.views.decorators.http import require_POST


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

def logout_user(request):
    request.session.flush()
    return redirect('login')


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

        if user.role == 'beneficiary':
            redirect_url = '/beneficiary/dashboard'
        elif user.role == 'donor':
            redirect_url = '/donor/dashboard'
        elif user.role == 'ngo':
            ngo_profile = NGOProfile.objects.filter(user=user).first()
            if not ngo_profile or not ngo_profile.approved:
                redirect_url = '/ngo/pending-approval/'
            else:
                redirect_url = '/ngo/dashboard'
        else:
            redirect_url = '/'

        return JsonResponse({'success': True, 'redirect_url': redirect_url})

    return JsonResponse({'success': False, 'errors': {'general': 'طلب غير صالح'}})


def beneficiary_dashboard(request):
    if 'user_id' not in request.session or request.session.get('role') != 'beneficiary':
        return redirect('login')
    user_id = request.session.get('user_id')
    recent_requests = AidRequest.objects.filter(beneficiary_id=user_id).order_by('-created_at')[:3]
    return render(request, 'beneficiary/dashboard.html', {'recent_requests': recent_requests})


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

def pending_approval(request):
    return render(request, 'ngo/pending_approval.html')

def check_ngo_approval(request):
    if 'user_id' not in request.session or request.session.get('role') != 'ngo':
        return JsonResponse({'approved': False})

    user = User.objects.get(id=request.session['user_id'])
    ngo_profile = NGOProfile.objects.filter(user=user).first()
    return JsonResponse({'approved': ngo_profile.approved if ngo_profile else False})


def ngo_dashboard(request):
    if 'user_id' not in request.session or request.session.get('role') != 'ngo':
        return redirect('login')

    ngo_user = User.objects.get(id=request.session['user_id'])
    profile = NGOProfile.objects.get(user=ngo_user)

    regions = [r.strip() for r in ngo_user.region.split(',') if r.strip()]

    campaigns = Campaign.objects.filter(ngo=profile).order_by('-created_at')
    adopted_requests = AidRequest.objects.filter(
        beneficiary__region__in=regions,
        status='approved'
    ).order_by('-created_at')

    return render(request, 'ngo/dashboard.html', {
        'profile': profile,
        'campaigns': campaigns,
        'adopted_requests': adopted_requests,
    })



def region_requests(request):
    if 'user_id' not in request.session or request.session.get('role') != 'ngo':
        return redirect('login')

    ngo_user = User.objects.get(id=request.session['user_id'])
    regions = [r.strip() for r in ngo_user.region.split(',') if r.strip()]

    aid_requests = AidRequest.objects.filter(
        beneficiary__region__in=regions,
        status='pending'  
    ).order_by('-created_at')

    return render(request, 'ngo/region_requests.html', {
        'aid_requests': aid_requests,
        'region_list': regions
    })


@require_POST
def approve_aid_request(request, request_id):
    if 'user_id' not in request.session or request.session.get('role') != 'ngo':
        return redirect('login')

    aid_request = AidRequest.objects.filter(id=request_id, status='pending').first()
    if aid_request:
        aid_request.ngo = NGOProfile.objects.get(user_id=request.session['user_id'])
        aid_request.status = 'approved'
        aid_request.save()
        messages.success(request, "تمت الموافقة على الطلب.")
    return redirect('region_requests')


@require_POST
def reject_aid_request(request, request_id):
    if 'user_id' not in request.session or request.session.get('role') != 'ngo':
        return redirect('login')

    aid_request = AidRequest.objects.filter(id=request_id, status='pending').first()
    if aid_request:
        aid_request.status = 'rejected'
        aid_request.save()
        messages.warning(request, "تم رفض الطلب.")
    return redirect('region_requests')



def adopted_requests(request):
    if 'user_id' not in request.session or request.session.get('role') != 'ngo':
        return redirect('login')

    ngo_user = User.objects.get(id=request.session['user_id'])

    requests = AidRequest.objects.filter(
        status='approved',
        beneficiary__region__in=[r.strip() for r in ngo_user.region.split(',')]
    ).order_by('-created_at')

    return render(request, 'ngo/adopted_requests.html', {
        'adopted_requests': requests
    })

def my_campaigns(request):
    if 'user_id' not in request.session or request.session.get('role') != 'ngo':
        return redirect('login')

    user = User.objects.get(id=request.session['user_id'])
    ngo_profile = NGOProfile.objects.filter(user=user).first()

    if not ngo_profile:
        messages.error(request, "لا يمكنك عرض الحملات لأن الجمعية غير معتمدة.")
        return redirect('ngo_dashboard')

    campaigns = Campaign.objects.filter(ngo=ngo_profile).order_by('-created_at')
    return render(request, 'ngo/my_campaigns.html', {'campaigns': campaigns})


def create_campaign_form(request):
    if 'user_id' not in request.session or request.session.get('role') != 'ngo':
        return redirect('login')

    return render(request, 'ngo/create_campaign.html')


def create_campaign_submit(request):
    if request.method != 'POST':
        return redirect('create_campaign_form')

    if 'user_id' not in request.session or request.session.get('role') != 'ngo':
        return redirect('login')

    user = User.objects.get(id=request.session['user_id'])
    ngo_profile = NGOProfile.objects.filter(user=user, approved=True).first()

    if not ngo_profile:
        messages.error(request, "لا يمكنك إنشاء حملة حتى يتم اعتماد الجمعية.")
        return redirect('ngo_dashboard')

    title = request.POST.get('title', '').strip()
    description = request.POST.get('description', '').strip()
    goal_amount = request.POST.get('goal_amount', '').strip()
    deadline = request.POST.get('deadline', '').strip()

    Campaign.objects.create(
        title=title,
        description=description,
        goal_amount=int(goal_amount),
        deadline=deadline,
        ngo=ngo_profile
    )

    messages.success(request, "✅ تم إنشاء الحملة بنجاح.")
    return redirect('my_campaigns')