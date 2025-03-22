from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User, Group
from .models import UserProfile, Block, Farmer, MonthlyReport
from django.db.models import Q
from datetime import datetime
import json
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from .forms import UserForm, BlockCreateForm, BlockUpdateForm, FarmerForm
from django.core.paginator import Paginator
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django import forms
from .models import Farmer
from .forms import UserProfileForm, FarmerForm, FarmerImageForm, FarmerAadharForm, ChangePasswordForm
from django.utils import timezone
from django.db import IntegrityError
import redis
import csv
import os

# Initialize Redis connection
r = redis.Redis(host='localhost', port=6379, db=0)

# Token generator
def generate_token():
    return uuid.uuid4().hex  # 32-char token

# Token validator (Using session)
def verify_token(request):
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Token '):
        return None
    token = auth_header.split(' ')[1]
    stored_token = request.session.get('auth_token')
    if stored_token != token or not request.session.session_key:
        return None
    if not request.user.is_authenticated:
        return None
    return request.user

# Role Check Helpers
def is_admin(user):
    return user.is_superuser

def is_supervisor(user):
    return user.groups.filter(name='Supervisors').exists()

def is_surveyor(user):
    return user.groups.filter(name='Surveyors').exists()

# UI Views (Frontend - Session-based)
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')
        return render(request, 'farmers/login.html', {'error': 'Invalid credentials'})
    return render(request, 'farmers/login.html')

def home_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'farmers/home.html', {'username': request.user.username})

def logout_view(request):
    if request.user.is_authenticated:
        if 'auth_token' in request.session:
            del request.session['auth_token']  # Clear token from session
        logout(request)
    return redirect('login')

# Admin Dashboard Views
def admin_dashboard(request):
    if not request.user.is_authenticated or not is_admin(request.user):
        return redirect('login')
    
    # Users (ordered by id)
    users = User.objects.all().order_by('id')
    user_query = request.GET.get('user_q', '')
    if user_query:
        users = users.filter(
            Q(username__icontains=user_query) |
            Q(email__icontains=user_query) |
            Q(profile__block__name__icontains=user_query)
        )
    
    # Handle cascading filters from POST
    selected_roles = request.POST.getlist('role')  # Get multiple roles
    selected_blocks = request.POST.getlist('block')  # Get multiple blocks
    
    if request.method == 'POST' and 'role' in request.POST:
        if selected_roles:
            if 'Admin' in selected_roles:
                users = users.filter(is_superuser=True)
            else:
                users = users.filter(groups__name__in=selected_roles)
        if selected_blocks:
            users = users.filter(profile__block__name__in=selected_blocks)
    
    user_per_page = int(request.GET.get('user_per_page', 10))
    user_paginator = Paginator(users, user_per_page)
    user_page_number = request.GET.get('user_page', 1)
    user_page_obj = user_paginator.get_page(user_page_number)
    user_data = [
        {
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'role': u.groups.first().name if u.groups.exists() else 'Admin' if u.is_superuser else 'None',
            'block': u.profile.block.name if hasattr(u, 'profile') and u.profile.block else None
        } for u in user_page_obj
    ]
    
    # Blocks (ordered by id)
    blocks = Block.objects.all().order_by('id')
    block_query = request.GET.get('block_q', '')
    if block_query:
        blocks = blocks.filter(
            Q(name__icontains=block_query) |
            Q(id__icontains=block_query)
        )
    if request.method == 'POST' and 'role' in request.POST:
        if selected_blocks:
            blocks = blocks.filter(name__in=selected_blocks)
        elif selected_roles:
            if 'Admin' in selected_roles:
                admin_profiles = UserProfile.objects.filter(user__is_superuser=True)
                blocks = blocks.filter(assigned_users__in=admin_profiles)
            else:
                blocks = blocks.filter(assigned_users__user__groups__name__in=selected_roles)
    
    block_per_page = int(request.GET.get('block_per_page', 10))
    block_paginator = Paginator(blocks, block_per_page)
    block_page_number = request.GET.get('block_page', 1)
    block_page_obj = block_paginator.get_page(block_page_number)
    block_data = [
        {
            'id': b.id,
            'name': b.name,
            'supervisor': User.objects.filter(groups__name='Supervisors', profile__block=b).first().username if User.objects.filter(groups__name='Supervisors', profile__block=b).exists() else None,
            'surveyors': [s.username for s in User.objects.filter(groups__name='Surveyors', profile__block=b)]
        } for b in block_page_obj
    ]
    
    # Data for cascading dropdowns
    all_roles = ['Admin', 'Supervisors', 'Surveyors']
    role_block_data = {}
    for role in all_roles:
        if role == 'Admin':
            role_users = User.objects.filter(is_superuser=True)
        else:
            role_users = User.objects.filter(groups__name=role)
        role_blocks = role_users.filter(profile__block__isnull=False).values_list('profile__block__name', flat=True).distinct()
        role_block_data[role] = list(role_blocks)
    
    # Fetch monthly reports, only include those where the file exists
    monthly_reports = [
        report for report in MonthlyReport.objects.all().order_by('-year', '-month')
        if os.path.exists(report.file_path)
    ]

    return render(request, 'farmers/admin_dashboard.html', {
        'users': user_data,
        'blocks': block_data,
        'user_query': user_query,
        'block_query': block_query,
        'user_page_obj': user_page_obj,
        'block_page_obj': block_page_obj,
        'user_per_page': user_per_page,
        'block_per_page': block_per_page,
        'all_roles': all_roles,
        'role_block_data': json.dumps(role_block_data),
        'selected_roles': selected_roles,  # Pass list of selected roles
        'selected_blocks': selected_blocks,  # Pass list of selected blocks
        'monthly_reports': monthly_reports,  # Pass monthly reports
    })

def download_farmers_csv(request):
    if not request.user.is_authenticated or not is_admin(request.user):
        return redirect('login')

    if request.method == 'POST':
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, "Invalid date format. Please use YYYY-MM-DD.")
            return redirect('admin_dashboard')

        # Filter farmers by date range
        farmers = Farmer.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )

        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="farmers_{start_date}_to_{end_date}.csv"'

        writer = csv.writer(response)
        writer.writerow(['Name', 'Aadhar ID', 'Surveyor', 'Block', 'Farm Area', 'Created At'])

        for farmer in farmers:
            writer.writerow([
                farmer.name,
                farmer.aadhar_id,
                farmer.surveyor.username if farmer.surveyor else 'N/A',
                farmer.block.name if farmer.block else 'N/A',
                farmer.farm_area,
                farmer.created_at
            ])

        return response

    return redirect('admin_dashboard')

def download_monthly_report(request, report_id):
    if not request.user.is_authenticated or not is_admin(request.user):
        return redirect('login')

    report = get_object_or_404(MonthlyReport, id=report_id)
    if not os.path.exists(report.file_path):
        messages.error(request, "Report file not found.")
        return redirect('admin_dashboard')

    with open(report.file_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="monthly_report_{report.year}-{report.month:02d}.csv"'
        return response

class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(widget=forms.PasswordInput, label="Current Password")
    new_password = forms.CharField(widget=forms.PasswordInput, label="New Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm New Password")

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")
        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError("New passwords do not match.")
        return cleaned_data

def user_profile(request, id):
    user = get_object_or_404(User, id=id)
    if request.user != user and not request.user.is_superuser:
        return redirect('login')
    
    profile, created = UserProfile.objects.get_or_create(user=user)
    form = ChangePasswordForm()  # Always initialize form
    profile_form = UserProfileForm(instance=profile)  # Always initialize profile_form
    
    if request.method == 'POST':
        if 'change_password' in request.POST:
            form = ChangePasswordForm(request.POST)
            if form.is_valid():
                if user.check_password(form.cleaned_data['current_password']):
                    user.set_password(form.cleaned_data['new_password'])
                    user.save()
                    update_session_auth_hash(request, user)
                    messages.success(request, "Password changed successfully.")
                else:
                    form.add_error('current_password', "Current password is incorrect.")
        elif 'upload_image' in request.POST:
            profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
            if form.is_valid():
                profile_form.save()
                messages.success(request, "Profile image updated successfully.")
    
    return render(request, 'farmers/user_profile.html', {
        'user': user,
        'form': form,
        'profile_form': profile_form
    })

def farmer_profile(request, id):
    print("FARMER_PROFILE CALLED")
    farmer = get_object_or_404(Farmer, id=id)
    if request.user != farmer.surveyor and not request.user.is_superuser:
        print("Redirecting to login")
        return redirect('login')
    
    if request.method == 'POST':
        print("POST received in farmer_profile")
        print("POST data:", request.POST)
        print("FILES data:", request.FILES)
        if 'image' in request.FILES:
            print("Saving farmer image:", request.FILES['image'].name)
            if farmer.image and farmer.image.name != 'farmer_images/default.jpg':
                farmer.image.delete()
            farmer.image = request.FILES['image']
            farmer.save()
            messages.success(request, "Farmer image uploaded successfully")
            return redirect('farmer_profile', id=id)
        elif 'aadhar_image' in request.FILES:
            print("Saving Aadhar image:", request.FILES['aadhar_image'].name)
            if farmer.aadhar_image:
                farmer.aadhar_image.delete()
            farmer.aadhar_image = request.FILES['aadhar_image']
            farmer.save()
            messages.success(request, "Aadhar image uploaded successfully")
            return redirect('farmer_profile', id=id)
        print("No valid file uploaded")
    
    print("Rendering farmer_profile.html")
    return render(request, 'farmers/farmer_profile.html', {'farmer': farmer})

def user_create(request):
    if not request.user.is_authenticated or not is_admin(request.user):
        return redirect('login')
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            form.save(created_by=request.user)
            return redirect('admin_dashboard')
        return render(request, 'farmers/user_form.html', {'form': form, 'title': 'Create'})
    else:
        form = UserForm()
    return render(request, 'farmers/user_form.html', {'form': form, 'title': 'Create'})

def user_update(request, id):
    if not request.user.is_authenticated or not is_admin(request.user):
        return redirect('login')
    user = get_object_or_404(User, id=id)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save(created_by=request.user)
            return redirect('admin_dashboard')
        return render(request, 'farmers/user_form.html', {'form': form, 'title': 'Update'})
    else:
        form = UserForm(instance=user, initial={'group': user.groups.first()})
    return render(request, 'farmers/user_form.html', {'form': form, 'title': 'Update'})

def user_delete(request, id):
    if not request.user.is_authenticated or not is_admin(request.user):
        return redirect('login')
    user = get_object_or_404(User, id=id)
    user.delete()
    return redirect('admin_dashboard')

def block_create(request):
    if not request.user.is_authenticated or not is_admin(request.user):
        return redirect('login')
    if request.method == 'POST':
        form = BlockCreateForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
        return render(request, 'farmers/block_form.html', {'form': form, 'title': 'Create'})
    form = BlockCreateForm()
    return render(request, 'farmers/block_form.html', {'form': form, 'title': 'Create'})

def block_update(request, id):
    if not request.user.is_authenticated or not is_admin(request.user):
        return redirect('login')
    block = get_object_or_404(Block, id=id)
    if request.method == 'POST':
        form = BlockUpdateForm(request.POST, instance=block)
        if form.is_valid():
            block = form.save()
            supervisor = form.cleaned_data['supervisor']
            surveyors = form.cleaned_data['surveyors']
            if supervisor:
                supervisor.profile.block = block
                supervisor.profile.save()
            UserProfile.objects.filter(block=block, user__groups__name='Supervisors').exclude(user=supervisor).update(block=None)
            UserProfile.objects.filter(block=block, user__groups__name='Surveyors').exclude(user__in=surveyors).update(block=None)
            if surveyors:
                UserProfile.objects.filter(user__in=surveyors).update(block=block)
            return redirect('admin_dashboard')
        return render(request, 'farmers/block_form.html', {'form': form, 'title': 'Update'})
    form = BlockUpdateForm(instance=block, initial={
        'supervisor': User.objects.filter(groups__name='Supervisors', profile__block=block).first(),
        'surveyors': User.objects.filter(groups__name='Surveyors', profile__block=block)
    })
    return render(request, 'farmers/block_form.html', {'form': form, 'title': 'Update'})

def block_delete(request, id):
    if not request.user.is_authenticated or not is_admin(request.user):
        return redirect('login')
    block = get_object_or_404(Block, id=id)
    block.delete()
    return redirect('admin_dashboard')

# Supervisor Dashboard Views
def supervisor_dashboard(request):
    if not request.user.is_authenticated or not request.user.groups.filter(name='Supervisors').exists():
        return redirect('login')
    block = request.user.profile.block
    if not block:
        return render(request, 'farmers/supervisor_dashboard.html', {'error': 'No block assigned'})
    
    # Surveyors (ordered by id)
    surveyors = User.objects.filter(groups__name='Surveyors', profile__block=block).order_by('id')  # Add ordering
    surveyor_query = request.GET.get('surveyor_q', '')
    if surveyor_query:
        surveyors = surveyors.filter(
            Q(username__icontains=surveyor_query) |
            Q(email__icontains=surveyor_query)
        )
    surveyor_per_page = int(request.GET.get('surveyor_per_page', 10))
    surveyor_paginator = Paginator(surveyors, surveyor_per_page)
    surveyor_page_number = request.GET.get('surveyor_page', 1)
    surveyor_page_obj = surveyor_paginator.get_page(surveyor_page_number)
    surveyor_data = [
        {'id': s.id, 'username': s.username, 'email': s.email}
        for s in surveyor_page_obj
    ]
    
    # Farmers (ordered by id)
    farmers = Farmer.objects.filter(block=block).order_by('id')  # Add ordering
    farmer_query = request.GET.get('farmer_q', '')
    if farmer_query:
        farmers = farmers.filter(
            Q(name__icontains=farmer_query) |
            Q(aadhar_id__icontains=farmer_query) |
            Q(farm_area__icontains=farmer_query)
        )
    farmer_per_page = int(request.GET.get('farmer_per_page', 10))
    farmer_paginator = Paginator(farmers, farmer_per_page)
    farmer_page_number = request.GET.get('farmer_page', 1)
    farmer_page_obj = farmer_paginator.get_page(farmer_page_number)
    farmer_data = [
        {'id': f.id, 'name': f.name, 'aadhar_id': f.aadhar_id, 'farm_area': f.farm_area, 'block': f.block.name}
        for f in farmer_page_obj
    ]
    
    return render(request, 'farmers/supervisor_dashboard.html', {
        'block_name': block.name,
        'supervisor_username': request.user.username,
        'surveyors': surveyor_data,
        'farmers': farmer_data,
        'surveyor_query': surveyor_query,
        'farmer_query': farmer_query,
        'surveyor_page_obj': surveyor_page_obj,
        'farmer_page_obj': farmer_page_obj,
        'surveyor_per_page': surveyor_per_page,
        'farmer_per_page': farmer_per_page
    })

# Surveyor Dashboard Views
def surveyor_dashboard(request):
    if not request.user.is_authenticated or not request.user.groups.filter(name='Surveyors').exists():
        return redirect('login')
    block = request.user.profile.block
    if not block:
        return render(request, 'farmers/surveyor_dashboard.html', {'error': 'No block assigned'})
    
    # Farmers (ordered by id)
    farmers = Farmer.objects.filter(surveyor=request.user).order_by('id')  # Add ordering
    query = request.GET.get('q', '')
    if query:
        farmers = farmers.filter(
            Q(name__icontains=query) |
            Q(aadhar_id__icontains=query) |
            Q(block__name__icontains=query) |
            Q(farm_area__icontains=query)
        )
    
    per_page = int(request.GET.get('per_page', 10))  # Default 10, adjustable
    paginator = Paginator(farmers, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    farmer_data = [
        {'id': f.id, 'name': f.name, 'aadhar_id': f.aadhar_id, 'farm_area': f.farm_area, 'block': f.block.name}
        for f in page_obj
    ]
    return render(request, 'farmers/surveyor_dashboard.html', {
        'block_name': block.name,
        'surveyor_username': request.user.username,
        'farmers': farmer_data,
        'query': query,
        'page_obj': page_obj,
        'per_page': per_page
    })

def farmer_create(request):
    if not request.user.is_authenticated or not is_surveyor(request.user):
        return redirect('login')
    
    if request.method == 'POST':
        form = FarmerForm(request.POST, surveyor=request.user)
        if form.is_valid():
            aadhar_id = form.cleaned_data['aadhar_id']
            lock_key = f"lock:farmer:{aadhar_id}"
            if r.set(lock_key, "1", ex=20, nx=True):
                try:
                    farmer = form.save(commit=False)
                    farmer.surveyor = request.user
                    farmer.created_by = request.user
                    farmer.last_updated_by = request.user
                    farmer.created_at = timezone.now()
                    farmer.save()
                    messages.success(request, "Farmer created successfully!")
                    return redirect('surveyor_dashboard')
                except IntegrityError:
                    messages.error(request, "A farmer with this Aadhar ID already exists.")
                    return render(request, 'farmers/farmer_form.html', {'form': form, 'title': 'Create'})
                finally:
                    r.delete(lock_key)
            else:
                messages.error(request, "Another request is processing this Aadhar ID. Please try again.")
                return render(request, 'farmers/farmer_form.html', {'form': form, 'title': 'Create'})
        return render(request, 'farmers/farmer_form.html', {'form': form, 'title': 'Create'})
    else:
        form = FarmerForm(surveyor=request.user)
    return render(request, 'farmers/farmer_form.html', {'form': form, 'title': 'Create'})

def farmer_update(request, id):
    farmer = get_object_or_404(Farmer, id=id)
    if request.user != farmer.surveyor and not request.user.is_superuser:
        return redirect('login')
    
    if request.method == 'POST':
        form = FarmerForm(request.POST, instance=farmer, surveyor=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Farmer updated successfully.")
            return redirect('surveyor_dashboard')  # Redirect to dashboard, not profile
    else:
        form = FarmerForm(instance=farmer, surveyor=request.user)
    
    return render(request, 'farmers/farmer_update.html', {'form': form, 'farmer': farmer})

def farmer_delete(request, id):
    if not request.user.is_authenticated or not is_surveyor(request.user):
        return redirect('login')
    farmer = get_object_or_404(Farmer, id=id, surveyor=request.user)
    farmer.delete()
    return redirect('surveyor_dashboard')

# API Views (Session-based Token Auth)
@csrf_exempt
def api_login(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        if not all([username, password]):
            return JsonResponse({'error': 'Missing username or password'}, status=400)
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            token = request.session.get('auth_token')
            if not token:
                token = generate_token()
                request.session['auth_token'] = token
            return JsonResponse({'token': token, 'user_id': user.id}, status=200)
        return JsonResponse({'error': 'Invalid credentials'}, status=401)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

@csrf_exempt
def api_logout(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    user = verify_token(request)
    if not user:
        return JsonResponse({'error': 'Invalid or expired token'}, status=401)
    if 'auth_token' in request.session:
        del request.session['auth_token']
    logout(request)
    return JsonResponse({'message': 'Logged out'}, status=200)

@csrf_exempt
def api_users(request):
    user = verify_token(request)
    if not user:
        return JsonResponse({'error': 'Invalid or expired token'}, status=401)

    if request.method == 'GET':
        role_filter = request.GET.get('role')
        if is_admin(user):
            users = User.objects.all()
            if role_filter:
                users = users.filter(groups__name=role_filter.capitalize())
            name_filter = request.GET.get('name')
            join_date = request.GET.get('join_date')
            search = request.GET.get('search')
            if name_filter:
                users = users.filter(username__icontains=name_filter)
            if join_date:
                try:
                    join_date = datetime.strptime(join_date, '%Y-%m-%d').date()
                    users = users.filter(profile__created_at__date=join_date)
                except ValueError:
                    return JsonResponse({'error': 'Invalid join_date format'}, status=400)
            if search:
                users = users.filter(Q(username__icontains=search) | Q(email__icontains=search))
            data = [
                {
                    'id': u.id,
                    'username': u.username,
                    'email': u.email,
                    'role': u.groups.first().name if u.groups.exists() else ('Admin' if u.is_superuser else 'None'),
                    'block': u.profile.block.name if hasattr(u, 'profile') and u.profile.block else None
                } for u in users
            ]
            return JsonResponse({'users': data}, status=200)
        elif is_supervisor(user) and role_filter == 'surveyors':
            block = user.profile.block
            if not block:
                return JsonResponse({'error': 'No block assigned'}, status=404)
            surveyors = User.objects.filter(groups__name='Surveyors', profile__block=block)
            data = {
                'block': block.name,
                'supervisor': user.username,
                'surveyors': [{'id': s.id, 'username': s.username, 'email': s.email} for s in surveyors]
            }
            return JsonResponse(data, status=200)
        elif is_surveyor(user) and role_filter == 'self':
            data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'block': user.profile.block.name if hasattr(user, 'profile') and user.profile.block else None
            }
            return JsonResponse(data, status=200)
        return JsonResponse({'error': 'Unauthorized or invalid role filter'}, status=403)

    elif request.method == 'POST':
        if not is_admin(user):
            return JsonResponse({'error': 'Only admin can create users'}, status=403)
        try:
            data = json.loads(request.body)
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            group_name = data.get('group')
            block_id = data.get('block_id')
            if not all([username, email, password, group_name]):
                return JsonResponse({'error': 'Missing required fields'}, status=400)
            if group_name not in ['Supervisors', 'Surveyors']:
                return JsonResponse({'error': 'Invalid group (use Supervisors or Surveyors)'}, status=400)
            if User.objects.filter(username=username).exists():
                return JsonResponse({'error': 'Username already exists'}, status=400)
            group = Group.objects.get(name=group_name)
            block = Block.objects.get(id=block_id) if block_id else None
            if block and group_name == 'Supervisors' and UserProfile.objects.filter(block=block, user__groups__name='Supervisors').exists():
                return JsonResponse({'error': 'This block already has a supervisor'}, status=400)
            new_user = User.objects.create_user(username=username, email=email, password=password)
            UserProfile.objects.create(user=new_user, block=block, created_by=user)
            new_user.groups.add(group)
            return JsonResponse({'id': new_user.id, 'username': new_user.username}, status=201)
        except (Group.DoesNotExist, Block.DoesNotExist):
            return JsonResponse({'error': 'Invalid group or block ID'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

@csrf_exempt
def api_users_detail(request, id):
    user = verify_token(request)
    if not user:
        return JsonResponse({'error': 'Invalid or expired token'}, status=401)
    target_user = get_object_or_404(User, id=id)

    if request.method == 'GET':
        if is_admin(user) or (is_supervisor(user) and target_user.groups.filter(name='Surveyors').exists() and target_user.profile.block == user.profile.block) or (is_surveyor(user) and target_user == user):
            data = {
                'id': target_user.id,
                'username': target_user.username,
                'email': target_user.email,
                'role': target_user.groups.first().name if target_user.groups.exists() else ('Admin' if target_user.is_superuser else 'None'),
                'block': target_user.profile.block.name if hasattr(target_user, 'profile') and target_user.profile.block else None
            }
            return JsonResponse(data, status=200)
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    elif request.method in ['PUT', 'PATCH']:
        if not is_admin(user):
            return JsonResponse({'error': 'Only admin can update users'}, status=403)
        try:
            data = json.loads(request.body)
            # print(f"API updating user {target_user.username} with data: {data}")  # Debug
            if 'email' in data:
                target_user.email = data['email']
            if 'new_password' in data:
                target_user.set_password(data['new_password'])
                print(f"Password updated for {target_user.username} to {data['new_password']}")
            if 'group' in data:
                group_name = data['group']
                if group_name not in ['Supervisors', 'Surveyors']:
                    return JsonResponse({'error': 'Invalid group'}, status=400)
                group = Group.objects.get(name=group_name)
                target_user.groups.clear()
                target_user.groups.add(group)
            if 'block_id' in data:
                block = Block.objects.get(id=data['block_id']) if data['block_id'] else None
                is_supervisor_after_update = ('group' in data and data['group'] == 'Supervisors') or is_supervisor(target_user)
                if block and is_supervisor_after_update and UserProfile.objects.filter(block=block, user__groups__name='Supervisors').exclude(user=target_user).exists():
                    return JsonResponse({'error': 'This block already has a supervisor'}, status=400)
                target_user.profile.block = block
                target_user.profile.last_updated_by = user
                target_user.profile.last_updated_at = datetime.now()
                target_user.profile.save()
            target_user.save()
            # print(f"Post-update password hash for {target_user.username}: {target_user.password}") #debug
            return JsonResponse({'id': target_user.id, 'username': target_user.username}, status=200)
        except (Group.DoesNotExist, Block.DoesNotExist):
            return JsonResponse({'error': 'Invalid group or block ID'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    elif request.method == 'DELETE':
        if not is_admin(user):
            return JsonResponse({'error': 'Only admin can delete users'}, status=403)
        target_user.delete()
        return JsonResponse({'message': 'User deleted'}, status=204)

    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def api_blocks(request):
    user = verify_token(request)
    if not user or not is_admin(user):
        return JsonResponse({'error': 'Invalid or expired token or not admin'}, status=401)

    if request.method == 'GET':
        blocks = Block.objects.all()
        data = [
            {
                'id': b.id,
                'name': b.name,
                'supervisor': User.objects.filter(groups__name='Supervisors', profile__block=b).first().username if User.objects.filter(groups__name='Supervisors', profile__block=b).exists() else None,
                'surveyors': [s.username for s in User.objects.filter(groups__name='Surveyors', profile__block=b)]
            } for b in blocks
        ]
        return JsonResponse({'blocks': data}, status=200)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            if not name:
                return JsonResponse({'error': 'Name required'}, status=400)
            if Block.objects.filter(name=name).exists():
                return JsonResponse({'error': 'Block name already exists'}, status=400)
            block = Block.objects.create(name=name)
            return JsonResponse({'id': block.id, 'name': block.name}, status=201)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

@csrf_exempt
def api_blocks_detail(request, id):
    user = verify_token(request)
    if not user or not is_admin(user):
        return JsonResponse({'error': 'Invalid or expired token or not admin'}, status=401)
    block = get_object_or_404(Block, id=id)

    if request.method == 'GET':
        data = {
            'id': block.id,
            'name': block.name,
            'supervisor': User.objects.filter(groups__name='Supervisors', profile__block=block).first().username if User.objects.filter(groups__name='Supervisors', profile__block=block).exists() else None,
            'surveyors': [s.username for s in User.objects.filter(groups__name='Surveyors', profile__block=block)]
        }
        return JsonResponse(data, status=200)

    elif request.method in ['PUT', 'PATCH']:
        try:
            data = json.loads(request.body)
            if 'name' in data:
                if Block.objects.filter(name=data['name']).exclude(id=block.id).exists():
                    return JsonResponse({'error': 'Block name already exists'}, status=400)
                block.name = data['name']
            block.save()
            return JsonResponse({'id': block.id, 'name': block.name}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    elif request.method == 'DELETE':
        block.delete()
        return JsonResponse({'message': 'Block deleted'}, status=204)

    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def api_farmers(request):
    user = verify_token(request)
    if not user or not (is_supervisor(user) or is_surveyor(user)):
        return JsonResponse({'error': 'Invalid or expired token or unauthorized'}, status=401)

    if request.method == 'GET':
        farmers = Farmer.objects.filter(surveyor=user) if is_surveyor(user) else Farmer.objects.filter(block=user.profile.block)
        data = [
            {
                'id': f.id,
                'name': f.name,
                'aadhar_id': f.aadhar_id,
                'block': f.block.name,
                'farm_area': f.farm_area,
                'created_at': f.created_at.isoformat()
            } for f in farmers
        ]
        return JsonResponse({'farmers': data}, status=200)

    elif request.method == 'POST':
        if not is_surveyor(user):
            return JsonResponse({'error': 'Only surveyors can create farmers'}, status=403)
        try:
            data = json.loads(request.body)
            name = data.get('name')
            aadhar_id = data.get('aadhar_id')
            block_id = data.get('block_id')
            farm_area = data.get('farm_area')
            if not all([name, aadhar_id, block_id, farm_area]):
                return JsonResponse({'error': 'Missing required fields'}, status=400)
            if Farmer.objects.filter(aadhar_id=aadhar_id).exists():
                return JsonResponse({'error': 'Aadhar ID already exists'}, status=400)
            block = Block.objects.get(id=block_id)
            if user.profile.block != block:
                return JsonResponse({'error': 'You are not assigned to this block'}, status=403)
            farmer = Farmer.objects.create(
                name=name,
                aadhar_id=aadhar_id,
                block=block,
                surveyor=user,
                farm_area=farm_area,
                created_by=user
            )
            return JsonResponse({'id': farmer.id, 'name': farmer.name}, status=201)
        except Block.DoesNotExist:
            return JsonResponse({'error': 'Block not found'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

@csrf_exempt
def api_farmers_detail(request, id):
    user = verify_token(request)
    if not user or not (is_supervisor(user) or is_surveyor(user)):
        return JsonResponse({'error': 'Invalid or expired token or unauthorized'}, status=401)
    farmer = get_object_or_404(Farmer, id=id)
    if (is_surveyor(user) and farmer.surveyor != user) or (is_supervisor(user) and farmer.block != user.profile.block):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    if request.method == 'GET':
        data = {
            'id': farmer.id,
            'name': farmer.name,
            'aadhar_id': farmer.aadhar_id,
            'block': farmer.block.name,
            'farm_area': farmer.farm_area,
            'created_at': farmer.created_at.isoformat()
        }
        return JsonResponse(data, status=200)

    elif request.method in ['PUT', 'PATCH']:
        if not is_surveyor(user) or farmer.surveyor != user:
            return JsonResponse({'error': 'Only the surveyor who created this farmer can update it'}, status=403)
        try:
            data = json.loads(request.body)
            if 'name' in data:
                farmer.name = data['name']
            if 'farm_area' in data:
                farmer.farm_area = data['farm_area']
            farmer.last_updated_by = user
            farmer.last_updated_at = datetime.now()
            farmer.save()
            return JsonResponse({'id': farmer.id, 'name': farmer.name}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    elif request.method == 'DELETE':
        if not is_surveyor(user) or farmer.surveyor != user:
            return JsonResponse({'error': 'Only the surveyor who created this farmer can delete it'}, status=403)
        farmer.delete()
        return JsonResponse({'message': 'Farmer deleted'}, status=204)

    return JsonResponse({'error': 'Method not allowed'}, status=405)