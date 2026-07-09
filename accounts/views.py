from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
import json
from .models import CustomUser
from django.contrib.auth import logout
from django.shortcuts import redirect

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'login.html')


def logout_user(request):

    if request.method == "POST":
        print("hii")

        logout(request)

        return redirect("login")

    return redirect("dashboard")

@login_required
def dashboard(request):
    if request.user.is_admin():
        return redirect('admin_dashboard')
    else:
        return redirect('employee_dashboard')

@login_required
def admin_dashboard(request):
    if not request.user.is_admin():
        messages.error(request, 'Access denied. Admin only.')
        return redirect('dashboard')
    
    employees = CustomUser.objects.filter(role='employee')
    context = {
        'employees': employees,
        'total_employees': employees.count(),
        'total_admins': CustomUser.objects.filter(role='admin').count(),
    }
    return render(request, 'admin_dashboard.html', context)

@login_required
def employee_dashboard(request):
    if not request.user.is_employee():
        messages.error(request, 'Access denied. Employee only.')
        return redirect('dashboard')
    return render(request, 'employee_dashboard.html', {'user': request.user})

@login_required
def get_employees(request):
    if not request.user.is_admin():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    employees = CustomUser.objects.filter(role='employee').values(
        'id', 'username', 'email', 'first_name', 'last_name', 
        'phone', 'department', 'date_joined'
    )
    return JsonResponse(list(employees), safe=False)

@login_required
def create_employee(request):
    if not request.user.is_admin():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        data = json.loads(request.body)
        
        if CustomUser.objects.filter(username=data.get('username')).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)
        
        if CustomUser.objects.filter(email=data.get('email')).exists():
            return JsonResponse({'error': 'Email already exists'}, status=400)
        
        user = CustomUser.objects.create_user(
            username=data.get('username'),
            email=data.get('email'),
            password=data.get('password'),
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            phone=data.get('phone', ''),
            department=data.get('department', ''),
            role='employee'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Employee created successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': user.phone,
                'department': user.department
            }
        })

@login_required
def update_employee(request, user_id):
    if not request.user.is_admin():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        user = get_object_or_404(CustomUser, id=user_id, role='employee')
        data = json.loads(request.body)
        
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.email = data.get('email', user.email)
        user.phone = data.get('phone', user.phone)
        user.department = data.get('department', user.department)
        
        if data.get('password'):
            user.set_password(data.get('password'))
        
        user.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Employee updated successfully'
        })

@login_required
def delete_employee(request, user_id):
    
    if not request.user.is_admin():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'DELETE':
        user = get_object_or_404(CustomUser, id=user_id, role='employee')
        user.delete()
        return JsonResponse({
            'success': True,
            'message': 'Employee deleted successfully'
        })

@login_required
def change_role(request, user_id):
    if not request.user.is_admin():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        user = get_object_or_404(CustomUser, id=user_id)
        data = json.loads(request.body)
        new_role = data.get('role')
        
        if new_role in ['admin', 'employee']:
            user.role = new_role
            user.save()
            return JsonResponse({
                'success': True,
                'message': f'Role changed to {new_role}'
            })
        
        return JsonResponse({'error': 'Invalid role'}, status=400)