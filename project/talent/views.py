from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
import json
import random
from django.http import JsonResponse, HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_http_methods
from django.middleware.csrf import get_token
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.conf import settings
from .models import User, Company, JobPosting, JobApplication, CandidateProfile, ContactMessage
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.urls import reverse
import datetime
import logging

logger = logging.getLogger(__name__)

# Create your views here.

def home(request):
  template = loader.get_template('index.html')
  return HttpResponse(template.render())

def about(request):
  template = loader.get_template('aboutus.html')
  return HttpResponse(template.render())

def contact(request):
  template = loader.get_template('contact.html')
  return HttpResponse(template.render())

def candLogin(request):
  template = loader.get_template('login.html')
  return HttpResponse(template.render())

def candSignup(request):
  template = loader.get_template('sign-up.html')
  return HttpResponse(template.render())

def cdash(request):
    # Get the logged-in user's ID from session
    user_id = request.session.get('user_id')
    if not user_id:
        return HttpResponseRedirect('/login.html')
    
    try:
        # Get the user and check their role
        user = User.objects.get(id=user_id)
        
        # Check if user has the correct role
        if user.role != 'user':
            return HttpResponseRedirect('/login.html')
        
        template = loader.get_template('cdashboard.html')
        context = {
            'user': user
        }
        return HttpResponse(template.render(context, request))
    except User.DoesNotExist:
        return HttpResponseRedirect('/login.html')

@require_http_methods(["GET", "POST"])
def cprofile(request):
    print(f"Session data in cprofile: {request.session.items()}")  # Debug log
    print(f"User ID from session in cprofile: {request.session.get('user_id')}")  # Debug log
    
    if not request.session.get('user_id'):
        print("No user_id in session for cprofile")  # Debug log
        return HttpResponseRedirect('/login.html')
    
    try:
        user = User.objects.get(id=request.session['user_id'])
        print(f"Found user in cprofile: {user.username}")  # Debug log
        profile, created = CandidateProfile.objects.get_or_create(user=user)
        
        if request.method == "POST":
            try:
                data = json.loads(request.body)
                
                # Update basic info
                profile.first_name = data.get('first_name', profile.first_name)
                profile.last_name = data.get('last_name', profile.last_name)
                profile.job_title = data.get('job_title', profile.job_title)
                profile.location = data.get('location', profile.location)
                profile.phone = data.get('phone', profile.phone)
                profile.website = data.get('website', profile.website)
                profile.languages = data.get('languages', profile.languages)
                profile.professional_summary = data.get('professional_summary', profile.professional_summary)
                profile.career_objective = data.get('career_objective', profile.career_objective)
                
                # Update JSON fields
                if 'work_experience' in data:
                    profile.work_experience = data['work_experience']
                if 'education' in data:
                    profile.education = data['education']
                if 'certifications' in data:
                    profile.certifications = data['certifications']
                if 'skills' in data:
                    profile.skills = data['skills']
                if 'social_media' in data:
                    profile.social_media = data['social_media']
                
                profile.save()
                return JsonResponse({'message': 'Profile updated successfully'})
                
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON data'}, status=400)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
        
        # For GET request, prepare profile data
        profile_data = {
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'mobile_number': user.mobile_number
            },
            'profile': {
                'first_name': profile.first_name,
                'last_name': profile.last_name,
                'job_title': profile.job_title,
                'location': profile.location,
                'phone': profile.phone,
                'website': profile.website,
                'languages': profile.languages,
                'avatar_url': profile.avatar.url if profile.avatar else None,
                'professional_summary': profile.professional_summary,
                'career_objective': profile.career_objective,
                'work_experience': profile.work_experience,
                'education': profile.education,
                'certifications': profile.certifications,
                'skills': profile.skills,
                'social_media': profile.social_media,
                'created_at': profile.created_at,
                'updated_at': profile.updated_at
            }
        }
        
        template = loader.get_template('cprofile.html')
        return HttpResponse(template.render(profile_data, request))
        
    except User.DoesNotExist:
        return HttpResponseRedirect('/login.html')
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def update_profile_avatar(request):
    """
    API endpoint for updating profile avatar
    """
    if not request.session.get('user_id'):
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    try:
        user = User.objects.get(id=request.session['user_id'])
        profile = CandidateProfile.objects.get(user=user)
        
        if 'avatar' not in request.FILES:
            return JsonResponse({'error': 'No avatar file provided'}, status=400)
        
        # Validate file type
        file = request.FILES['avatar']
        if not file.content_type.startswith('image/'):
            return JsonResponse({'error': 'File must be an image'}, status=400)
        
        # Validate file size (max 5MB)
        if file.size > 5 * 1024 * 1024:
            return JsonResponse({'error': 'File size must be less than 5MB'}, status=400)
        
        profile.avatar = file
        profile.save()
        
        return JsonResponse({
            'message': 'Avatar updated successfully',
            'avatar_url': profile.avatar.url
        })
        
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except CandidateProfile.DoesNotExist:
        return JsonResponse({'error': 'Profile not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def ceditprofile(request):
  template = loader.get_template('ceditprofile.html')
  return HttpResponse(template.render())

@require_http_methods(["GET"])
def cpreview(request):
    """
    View function to render the candidate profile preview page
    """
    if not request.session.get('user_id'):
        return HttpResponseRedirect('/login.html')
    
    try:
        user = User.objects.get(id=request.session['user_id'])
        profile = CandidateProfile.objects.get(user=user)
        
        # Prepare profile data for the template
        profile_data = {
            'user': user,
            'profile': profile
        }
        
        template = loader.get_template('cpreview.html')
        return HttpResponse(template.render(profile_data, request))
        
    except User.DoesNotExist:
        return HttpResponseRedirect('/login.html')
    except CandidateProfile.DoesNotExist:
        # If profile doesn't exist, create one
        profile = CandidateProfile.objects.create(user=user)
        profile_data = {
            'user': user,
            'profile': profile
        }
        template = loader.get_template('cpreview.html')
        return HttpResponse(template.render(profile_data, request))

def empLog(request):
  template = loader.get_template('emp_signin.html')
  return HttpResponse(template.render())

def empReg(request):
  template = loader.get_template('emp_signup.html')
  return HttpResponse(template.render())  

def empAbout(request):
  template = loader.get_template('emp_aboutUs.html')
  return HttpResponse(template.render())

def empCon(request):
  template = loader.get_template('emp_contactUs.html')
  return HttpResponse(template.render()) 

def empDash(request):
    # Get the logged-in user's ID from session
    user_id = request.session.get('user_id')
    if not user_id:
        return HttpResponseRedirect('/login.html')
    
    try:
        # Get the HR user
        hr = User.objects.get(id=user_id, role='hr')
        
        # Get companies associated with this HR
        companies = hr.companies.all()
        
        # Prepare company data
        companies_data = []
        for company in companies:
            companies_data.append({
                'id': company.id,
                'name': company.company_name,
                'email': company.company_email,
                'industry': company.industry,
                'size': company.company_size,
                'location': company.location,
                'logo': company.company_logo.url if company.company_logo else None
            })
        
        template = loader.get_template('emp_dash.html')
        context = {
            'companies': companies_data,
            'hr_id': user_id
        }
        return HttpResponse(template.render(context, request))
    except User.DoesNotExist:
        return HttpResponseRedirect('/login.html')

def empCandidateList(request):
    # Get HR user ID from session
    hr_id = request.session.get('user_id')
    if not hr_id:
        return HttpResponseRedirect('/login.html')
    
    try:
        # Get HR user and their associated company
        hr_user = User.objects.get(id=hr_id, role='hr')
        company = hr_user.companies.first()
        if not company:
            return HttpResponseRedirect('/emp_dash.html')
        
        # Get all jobs posted by this HR
        jobs = JobPosting.objects.filter(hr_id=hr_user)
        
        # Get all applications for these jobs
        applications = JobApplication.objects.filter(job__in=jobs).select_related('job', 'applicant')
        
        # Prepare the data for the template
        applications_data = []
        for app in applications:
            applications_data.append({
                'id': app.id,
                'job_title': app.job.title,
                'department': app.job.category,
                'applicant_name': app.applicant.username,
                'applicant_email': app.applicant.email,
                'applied_date': app.applied_date,
                'status': app.status,
                'resume_url': app.resume.url if app.resume else None,
                'cover_letter': app.cover_letter
            })
        
        template = loader.get_template('emp_CandidateList.html')
        context = {
            'applications': applications_data,
            'total_applications': len(applications_data)
        }
        return HttpResponse(template.render(context, request))
    except User.DoesNotExist:
        return HttpResponseRedirect('/login.html')

def empPJ(request):
  template = loader.get_template('emp_postJob.html')
  return HttpResponse(template.render()) 

def comPro(request):
  template = loader.get_template('companyProfile.html')
  return HttpResponse(template.render())

def EJL(request):
  template = loader.get_template('emp_jobList.html')
  return HttpResponse(template.render())


# creating views for Candidate at 9:38 on 24 04 25

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .models import User
from django.core.exceptions import ValidationError

@csrf_exempt
@require_http_methods(["POST"])
def register_user(request):
    try:
        data = json.loads(request.body)

        username = data.get('username')
        email = data.get('email')
        mobile_number = data.get('mobile_number')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        role = data.get('role', 'user')  # Default to 'user' if not provided

        if not all([username, email, mobile_number, password, confirm_password]):
            return JsonResponse({'error': 'All fields are required.'}, status=400)

        if password != confirm_password:
            return JsonResponse({'error': 'Passwords do not match.'}, status=400)

        if len(password) < 8:
            return JsonResponse({'error': 'Password must be at least 8 characters long.'}, status=400)

        # Validate role
        valid_roles = [choice[0] for choice in User.ROLE_CHOICES]
        if role not in valid_roles:
            return JsonResponse({'error': f'Invalid role. Must be one of: {", ".join(valid_roles)}'}, status=400)

        user = User(
            username=username,
            email=email,
            mobile_number=mobile_number,
            is_verified=False,
            role=role
        )
        user.set_password(password)
        user.full_clean()
        user.save()

        return JsonResponse({'message': 'User registered successfully.', 'is_verified': user.is_verified, 'role': user.role}, status=201)

    except ValidationError as ve:
        return JsonResponse({'error': str(ve)}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def login_user(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                return JsonResponse({'error': 'Email and password are required'}, status=400)
            
            try:
                user = User.objects.get(email=email)
                if user.check_password(password):  # Using check_password method
                    if user.is_verified:
                        # Store user ID in session
                        request.session['user_id'] = user.id
                        
                        # User is verified, handle based on role
                        if user.role == 'admin':
                            # Admin users are redirected to admin dashboard
                            return JsonResponse({
                                'message': 'Login successful',
                                'is_verified': True,
                                'role': user.role,
                                'user_id': user.id,
                                'redirect_url': '/dashboard/'
                            }, status=200)
                        elif user.role == 'hr':
                            # Check if HR is already associated with a company
                            existing_companies = user.companies.all()
                            if existing_companies.exists():
                                # HR is already associated with a company, redirect to employer dashboard
                                return JsonResponse({
                                    'message': 'Login successful',
                                    'is_verified': True,
                                    'role': user.role,
                                    'user_id': user.id,
                                    'redirect_url': '/emp_dash.html'
                                }, status=200)
                            else:
                                # HR is not associated with any company, redirect to company selection
                                return JsonResponse({
                                    'message': 'Login successful',
                                    'is_verified': True,
                                    'role': user.role,
                                    'user_id': user.id,
                                    'redirect_url': '/company_selection.html'
                                }, status=200)
                        elif user.role == 'user':
                            # For regular users, redirect to candidate dashboard
                            return JsonResponse({
                                'message': 'Login successful',
                                'is_verified': True,
                                'role': user.role,
                                'redirect_url': '/cdashboard.html'
                            }, status=200)
                        else:
                            # For any other role, return error
                            return JsonResponse({
                                'error': 'Invalid user role'
                            }, status=403)
                    else:
                        # Store email in session for OTP verification
                        request.session['email'] = email
                        return JsonResponse({
                            'message': 'Please verify your email',
                            'is_verified': False,
                            'redirect_url': '/verify_otp.html'
                        }, status=200)
                else:
                    return JsonResponse({'error': 'Invalid password'}, status=401)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User not found'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)
    


#GET by ID
@csrf_exempt
@require_http_methods(["GET"])
def get_user(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "mobile_number": user.mobile_number,
            "is_verified": user.is_verified,
            "role": user.role
        }
        return JsonResponse(data, status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found.'}, status=404)

@csrf_exempt
@require_http_methods(["GET"])
def list_users(request):
    users = User.objects.all()
    data = [{
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'mobile_number': u.mobile_number,
        'is_verified': u.is_verified,
        'role': u.role
    } for u in users]
    return JsonResponse({'users': data}, status=200)



@csrf_exempt
@require_http_methods(["PUT"])
def update_user(request, user_id):
    try:
        data = json.loads(request.body)
        user = User.objects.get(id=user_id)

        user.username = data.get('username', user.username)
        user.email = data.get('email', user.email)
        user.mobile_number = data.get('mobile_number', user.mobile_number)

        # Optional: handle password update
        if 'password' in data:
            new_password = data['password']
            if len(new_password) < 8:
                return JsonResponse({'error': 'Password must be at least 8 characters long.'}, status=400)
            user.set_password(new_password)

        # Optional: handle is_verified update
        if 'is_verified' in data:
            user.is_verified = data['is_verified']

        # Optional: handle role update
        if 'role' in data:
            if data['role'] not in [choice[0] for choice in User.ROLE_CHOICES]:
                return JsonResponse({'error': 'Invalid role.'}, status=400)
            user.role = data['role']

        user.full_clean()
        user.save()
        return JsonResponse({'message': 'User updated successfully.', 'is_verified': user.is_verified, 'role': user.role}, status=200)

    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found.'}, status=404)
    except ValidationError as ve:
        return JsonResponse({'error': str(ve)}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_user(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        user.delete()
        return JsonResponse({'message': 'User deleted successfully.'}, status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found.'}, status=404) 


# creating views for HR at 01:44 am on 25 04 25

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password
from .models import Company
import json

@csrf_exempt
@require_http_methods(["POST"])
def admin_create_company(request):
    try:
        # Get form data
        company_name = request.POST.get('company_name')
        company_email = request.POST.get('company_email')
        industry = request.POST.get('industry')
        company_size = request.POST.get('company_size')
        location = request.POST.get('location')
        company_logo = request.FILES.get('company_logo')

        # Validate required fields
        required_fields = [company_name, company_email, industry, company_size, location]
        if not all(required_fields):
            return JsonResponse({'error': 'All fields are required.'}, status=400)

        # Validate industry choice
        valid_industries = [choice[0] for choice in Company.INDUSTRY_CHOICES]
        if industry not in valid_industries:
            return JsonResponse({'error': f'Invalid industry. Must be one of: {", ".join(valid_industries)}'}, status=400)

        # Validate company size choice
        valid_sizes = [choice[0] for choice in Company.COMPANY_SIZE_CHOICES]
        if company_size not in valid_sizes:
            return JsonResponse({'error': f'Invalid company size. Must be one of: {", ".join(valid_sizes)}'}, status=400)

        # Create Company instance
        company = Company(
            company_name=company_name,
            company_email=company_email,
            industry=industry,
            company_size=company_size,
            location=location,
            company_logo=company_logo
        )

        company.full_clean()
        company.save()

        return JsonResponse({
            'message': 'Company created successfully.',
            'company_name': company.company_name,
            'company_email': company.company_email,
            'industry': company.industry,
            'company_size': company.company_size,
            'location': company.location
        }, status=201)

    except ValidationError as ve:
        return JsonResponse({'error': str(ve)}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.hashers import check_password
from .models import Company
import json

@csrf_exempt
@require_http_methods(["POST"])
def login_company(request):
    try:
        data = json.loads(request.body)
        company_email = data.get('company_email')
        password = data.get('password')

        if not company_email or not password:
            return JsonResponse({'error': 'Email and password are required.'}, status=400)

        try:
            company = Company.objects.get(company_email=company_email)
        except Company.DoesNotExist:
            return JsonResponse({'error': 'Invalid email or password.'}, status=401)

        if not check_password(password, company.password):
            return JsonResponse({'error': 'Invalid email or password.'}, status=401)
         
        # Login successful
        return JsonResponse({
            'message': 'Login successful.',
            'company_name': company.company_name,
            'company_email': company.company_email,
            'location': company.location,
            'industry': company.industry
        }, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)























# Creating views for job posting at 02:03 am on 23 04 15

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_date, parse_datetime
from .models import JobPosting


def job_to_dict(job):
    return {
        "id": job.id,
        "title": job.title,
        "category": job.category,
        "job_type": job.job_type,
        "experience_level": job.experience_level,
        "workplace_type": job.workplace_type,
        "location": job.location,
        "country": job.country,
        "salary": float(job.salary),
        "hide_salary": job.hide_salary,
        "company_overview": job.company_overview,
        "job_description": job.job_description,
        "requirements": job.requirements,
        "benefits": job.benefits,
        "required_skills": job.required_skills,
        "preferred_skills": job.preferred_skills,
        "education_level": job.education_level,
        "languages": job.languages,
        "application_deadline": job.application_deadline.isoformat() if job.application_deadline else None,
        "require_resume": job.require_resume,
        "require_cover_letter": job.require_cover_letter,
        "require_portfolio": job.require_portfolio,
        "require_references": job.require_references,
        "visibility": job.visibility,
        "featured_job": job.featured_job,
        "urgent_job": job.urgent_job,
        "publish_option": job.publish_option,
        "schedule_date": job.schedule_date.isoformat() if job.schedule_date else None,
        # Add company details
        "company": {
            "id": job.company_id.id if job.company_id else None,
            "name": job.company_id.company_name if job.company_id else None,
            "email": job.company_id.company_email if job.company_id else None,
            "industry": job.company_id.industry if job.company_id else None,
            "size": job.company_id.company_size if job.company_id else None,
            "location": job.company_id.location if job.company_id else None,
            "logo": job.company_id.company_logo.url if job.company_id and job.company_id.company_logo else None
        } if job.company_id else None,
        # Add HR details
        "hr": {
            "id": job.hr_id.id if job.hr_id else None,
            "username": job.hr_id.username if job.hr_id else None,
            "email": job.hr_id.email if job.hr_id else None,
            "mobile_number": job.hr_id.mobile_number if job.hr_id else None
        } if job.hr_id else None,
    }


@csrf_exempt
def create_job_posting(request):
    if request.method == 'POST':
        try:
            # Get HR user ID from session
            hr_id = request.session.get('user_id')
            if not hr_id:
                return JsonResponse({"error": "User not authenticated"}, status=401)

            # Get HR user and their associated company
            try:
                hr_user = User.objects.get(id=hr_id, role='hr')
                company = hr_user.companies.first()  # Get the first company associated with the HR
                if not company:
                    return JsonResponse({"error": "HR user is not associated with any company"}, status=400)
            except User.DoesNotExist:
                return JsonResponse({"error": "HR user not found"}, status=404)

            data = json.loads(request.body)

            job = JobPosting.objects.create(
                title=data['title'],
                category=data['category'],
                job_type=data['job_type'],
                experience_level=data['experience_level'],
                workplace_type=data['workplace_type'],
                location=data['location'],
                country=data['country'],
                salary=data['salary'],
                hide_salary=data.get('hide_salary', False),
                company_overview=data['company_overview'],
                job_description=data['job_description'],
                requirements=data['requirements'],
                benefits=data['benefits'],
                required_skills=data['required_skills'],
                preferred_skills=data['preferred_skills'],
                education_level=data['education_level'],
                languages=data['languages'],
                application_deadline=parse_date(data.get('application_deadline')) if data.get('application_deadline') else None,
                require_resume=data.get('require_resume', True),
                require_cover_letter=data.get('require_cover_letter', False),
                require_portfolio=data.get('require_portfolio', False),
                require_references=data.get('require_references', False),
                visibility=data['visibility'],
                featured_job=data.get('featured_job', False),
                urgent_job=data.get('urgent_job', False),
                publish_option=data['publish_option'],
                schedule_date=parse_datetime(data.get('schedule_date')) if data.get('schedule_date') else None,
                hr_id=hr_user,  # Set the HR user
                company_id=company  # Set the company
            )

            return JsonResponse({"message": "Job created successfully", "id": job.id}, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid HTTP method"}, status=405)


@csrf_exempt
def get_job_posting(request, job_id):
    try:
        job = JobPosting.objects.get(pk=job_id)
        return JsonResponse(job_to_dict(job))
    except JobPosting.DoesNotExist:
        return JsonResponse({"error": "Job not found"}, status=404)


@csrf_exempt
def update_job_posting(request, job_id):
    if request.method == 'PUT':
        try:
            job = JobPosting.objects.get(pk=job_id)
            data = json.loads(request.body)

            for field, value in data.items():
                if field == "application_deadline":
                    setattr(job, field, parse_date(value))
                elif field == "schedule_date":
                    setattr(job, field, parse_datetime(value))
                elif field == "salary":
                    setattr(job, field, float(value))
                else:
                    setattr(job, field, value)

            job.save()
            return JsonResponse({"message": "Job updated successfully"})

        except JobPosting.DoesNotExist:
            return JsonResponse({"error": "Job not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid HTTP method"}, status=405)


@csrf_exempt
def delete_job_posting(request, job_id):
    if request.method == 'DELETE':
        try:
            job = JobPosting.objects.get(pk=job_id)
            job.delete()
            return JsonResponse({"message": "Job deleted successfully"})
        except JobPosting.DoesNotExist:
            return JsonResponse({"error": "Job not found"}, status=404)

    return JsonResponse({"error": "Invalid HTTP method"}, status=405)




# OTP 
# import random
# from sendgrid import SendGridAPIClient
# from sendgrid.helpers.mail import Mail
# from django.conf import settings


def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(email, otp):
    message = Mail(
        from_email=settings.FROM_EMAIL,
        to_emails=email,
        subject='Your OTP Code',
        plain_text_content=f'Your OTP code is: {otp}',
    )
    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        return response.status_code
    except Exception as e:
        print(f"SendGrid Error: {e}")
        return None



@csrf_exempt
def send_otp(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            
            if not email:
                return JsonResponse({'error': 'Email is required'}, status=400)
            
            # Generate OTP
            otp = generate_otp()
            
            # Store OTP in session
            request.session['otp'] = otp
            request.session['email_for_verification'] = email
            
            # Send OTP via email
            send_otp_email(email, otp)
            
            return JsonResponse({
                'message': 'OTP sent successfully',
                'redirect_url': '/verify_otp.html'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid request data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def verify_otp(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            otp = data.get('otp')
            email = request.session.get('email_for_verification')
            
            if not email or not otp:
                return JsonResponse({'error': 'Email and OTP are required'}, status=400)
            
            # Get the stored OTP from session
            stored_otp = request.session.get('otp')
            if not stored_otp:
                return JsonResponse({'error': 'OTP expired. Please request a new one'}, status=400)
            
            if otp != stored_otp:
                return JsonResponse({'error': 'Invalid OTP'}, status=400)
            
            # Clear the OTP from session
            del request.session['otp']
            del request.session['email_for_verification']
            
            # Update user verification status
            try:
                user = User.objects.get(email=email)
                user.is_verified = True
                user.save()
            except User.DoesNotExist:
                return JsonResponse({'error': 'User not found'}, status=404)
            
            return JsonResponse({
                'message': 'Email verified successfully',
                'redirect_url': '/cdashboard.html'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid request data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def verify_otp_page(request):
    email = request.session.get('email_for_verification')
    if not email:
        return HttpResponseRedirect('/login.html')
    
    template = loader.get_template('verify_otp.html')
    return HttpResponse(template.render({}, request))













# at 16:13 on 02 05 25
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from .models import CandidateProfile
# import json





# Admin views
# @login_required(login_url='/login/')
def admin_dashboard(request):
    # Check if user is logged in and is an admin
    if not request.session.get('user_id'):
        return HttpResponseRedirect('/login.html')
    
    try:
        user = User.objects.get(id=request.session['user_id'])
        if user.role != 'admin':
            return HttpResponseRedirect('/login.html')
    except User.DoesNotExist:
        return HttpResponseRedirect('/login.html')
    
    template = loader.get_template('admin_dashboard.html')
    return HttpResponse(template.render({}, request))

@csrf_exempt
@require_http_methods(["GET"])
def admin_list_companies(request):
    try:
        # Get filter parameters
        search = request.GET.get('search', '')
        industry = request.GET.get('industry', '')
        size = request.GET.get('size', '')

        # Start with all companies
        companies = Company.objects.all()

        # Apply filters
        if search:
            companies = companies.filter(company_name__icontains=search)
        if industry:
            companies = companies.filter(industry=industry)
        if size:
            companies = companies.filter(company_size=size)

        # Convert to list of dictionaries
        companies_data = [{
            'id': company.id,
            'company_name': company.company_name,
            'company_email': company.company_email,
            'industry': company.industry,
            'company_size': company.company_size,
            'location': company.location,
            'company_logo': company.company_logo.name if company.company_logo else None
        } for company in companies]

        return JsonResponse({'companies': companies_data}, status=200)
    except Exception as e:
        print(f"Error in admin_list_companies: {str(e)}")  # Add logging
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def admin_list_hr(request):
    try:
        # Get filter parameters
        search = request.GET.get('search', '')
        company = request.GET.get('company', '')

        # Start with all users with HR role
        hr_users = User.objects.filter(role='hr')

        # Apply filters
        if search:
            hr_users = hr_users.filter(username__icontains=search)
        if company:
            hr_users = hr_users.filter(email__icontains=company)

        # Convert to list of dictionaries
        hr_data = [{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'mobile_number': user.mobile_number,
            'is_verified': user.is_verified
        } for user in hr_users]

        return JsonResponse({'hr': hr_data}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def admin_list_users(request):
    try:
        # Get filter parameters
        search = request.GET.get('search', '')
        role = request.GET.get('role', 'user')  # Default to 'user' role
        status = request.GET.get('status', '')

        # Start with all users with 'user' role by default
        users = User.objects.filter(role='user')

        # Apply filters
        if search:
            users = users.filter(username__icontains=search)
        if role and role != 'user':  # If a different role is selected, override the default
            users = User.objects.filter(role=role)
        if status:
            if status == 'verified':
                users = users.filter(is_verified=True)
            elif status == 'unverified':
                users = users.filter(is_verified=False)

        # Convert to list of dictionaries
        users_data = [{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'is_verified': user.is_verified
        } for user in users]

        return JsonResponse({'users': users_data}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def admin_delete_company(request, company_id):
    try:
        company = Company.objects.get(id=company_id)
        company.delete()
        return JsonResponse({'message': 'Company deleted successfully.'}, status=200)
    except Company.DoesNotExist:
        return JsonResponse({'error': 'Company not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def admin_delete_user(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        user.delete()
        return JsonResponse({'message': 'User deleted successfully.'}, status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)









def forgot_password_page(request):
    template = loader.get_template('forgot_password.html')
    return HttpResponse(template.render())

def reset_password_page(request):
    token = request.GET.get('token')
    if not token:
        return HttpResponseRedirect('/forgot-password.html')
    
    try:
        user = User.objects.get(reset_password_token=token)
        # Check if token is expired (24 hours)
        token_age = datetime.datetime.now(datetime.timezone.utc) - user.reset_password_token_created_at
        if token_age > datetime.timedelta(hours=24):
            return HttpResponseRedirect('/forgot-password.html')
    except User.DoesNotExist:
        return HttpResponseRedirect('/forgot-password.html')
    
    template = loader.get_template('reset_password.html')
    return HttpResponse(template.render({'token': token}))

@csrf_exempt
@require_http_methods(["POST"])
def forgot_password(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        
        if not email:
            return JsonResponse({'error': 'Email is required'}, status=400)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({'error': 'No user found with this email address'}, status=404)
        
        # Generate a unique token
        token = get_random_string(length=32)
        user.reset_password_token = token
        user.reset_password_token_created_at = datetime.datetime.now(datetime.timezone.utc)
        user.save()
        
        # Create reset password URL
        reset_url = request.build_absolute_uri(
            f'/reset-password.html?token={token}'
        )
        
        # Send email with reset link using SendGrid
        try:
            from_email = getattr(settings, 'FROM_EMAIL', 'noreply@talenthive.com')
            message = Mail(
                from_email=from_email,
                to_emails=email,
                subject='Reset Your Password',
                plain_text_content=f'Click the following link to reset your password: {reset_url}',
                html_content=f'''
                    <h2>Reset Your Password</h2>
                    <p>Click the button below to reset your password:</p>
                    <a href="{reset_url}" style="background-color: #4CAF50; color: white; padding: 12px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">
                        Reset Password
                    </a>
                    <p>If the button doesn't work, copy and paste this link into your browser:</p>
                    <p>{reset_url}</p>
                    <p>This link will expire in 24 hours.</p>
                '''
            )
            
            # Get SendGrid API key from settings
            api_key = getattr(settings, 'SENDGRID_API_KEY', None)
            if not api_key:
                raise ValueError("SendGrid API key not configured")
                
            sg = SendGridAPIClient(api_key)
            response = sg.send(message)
            
            if response.status_code == 202:  # SendGrid success status code
                return JsonResponse({'message': 'Password reset link has been sent to your email'})
            else:
                print(f"SendGrid Error: Status code {response.status_code}")
                return JsonResponse({'error': 'Failed to send email'}, status=500)
                
        except Exception as e:
            print(f"SendGrid Error: {str(e)}")
            return JsonResponse({'error': 'Failed to send email. Please try again later.'}, status=500)
        
    except Exception as e:
        print(f"Server Error: {str(e)}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def reset_password(request):
    try:
        data = json.loads(request.body)
        token = data.get('token')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        
        if not all([token, password, confirm_password]):
            return JsonResponse({'error': 'All fields are required'}, status=400)
        
        if password != confirm_password:
            return JsonResponse({'error': 'Passwords do not match'}, status=400)
        
        try:
            user = User.objects.get(reset_password_token=token)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Invalid or expired reset token'}, status=400)
        
        # Check if token is expired (24 hours)
        token_age = datetime.datetime.now(datetime.timezone.utc) - user.reset_password_token_created_at
        if token_age > datetime.timedelta(hours=24):
            return JsonResponse({'error': 'Reset token has expired'}, status=400)
        
        # Update password and clear reset token
        user.set_password(password)
        user.reset_password_token = None
        user.reset_password_token_created_at = None
        user.save()
        
        return JsonResponse({'message': 'Password has been reset successfully'})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def hr_join_company(request):
    try:
        data = json.loads(request.body)
        hr_id = data.get('hr_id')
        company_id = data.get('company_id')

        if not hr_id or not company_id:
            return JsonResponse({'error': 'HR ID and Company ID are required.'}, status=400)

        try:
            hr = User.objects.get(id=hr_id, role='hr')
            company = Company.objects.get(id=company_id)
        except User.DoesNotExist:
            return JsonResponse({'error': 'HR user not found.'}, status=404)
        except Company.DoesNotExist:
            return JsonResponse({'error': 'Company not found.'}, status=404)

        # Check if HR is already associated with any company
        existing_companies = hr.companies.all()
        if existing_companies.exists():
            existing_company = existing_companies.first()
            return JsonResponse({
                'error': f'You are already associated with {existing_company.company_name}. Please leave your current company before joining a new one.',
                'status': 'already_associated',
                'current_company': existing_company.get_company_details()
            }, status=400)

        # Check if HR is already associated with the target company
        if company.hr_users.filter(id=hr_id).exists():
            existing_hr = company.hr_users.get(id=hr_id)
            return JsonResponse({
                'error': f'You have already joined this company as {existing_hr.username}.',
                'status': 'already_joined'
            }, status=400)

        # Add HR to company
        company.hr_users.add(hr)

        return JsonResponse({
            'message': 'HR successfully joined the company.',
            'company': company.get_company_details()
        }, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_company_details(request, company_id):
    try:
        company = Company.objects.get(id=company_id)
        return JsonResponse(company.get_company_details(), status=200)
    except Company.DoesNotExist:
        return JsonResponse({'error': 'Company not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_hr_companies(request, hr_id):
    try:
        hr = User.objects.get(id=hr_id, role='hr')
        companies = hr.companies.all()
        return JsonResponse({
            'companies': [company.get_company_details() for company in companies]
        }, status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'HR user not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def hr_leave_company(request):
    try:
        data = json.loads(request.body)
        hr_id = data.get('hr_id')
        company_id = data.get('company_id')

        if not hr_id or not company_id:
            return JsonResponse({'error': 'HR ID and Company ID are required.'}, status=400)

        try:
            hr = User.objects.get(id=hr_id, role='hr')
            company = Company.objects.get(id=company_id)
        except User.DoesNotExist:
            return JsonResponse({'error': 'HR user not found.'}, status=404)
        except Company.DoesNotExist:
            return JsonResponse({'error': 'Company not found.'}, status=404)

        # Remove HR from company
        company.hr_users.remove(hr)

        return JsonResponse({
            'message': 'HR successfully left the company.',
            'company': company.get_company_details()
        }, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_all_companies(request):
    try:
        # Get filter parameters
        search = request.GET.get('search', '')
        industry = request.GET.get('industry', '')
        size = request.GET.get('size', '')

        # Start with all companies
        companies = Company.objects.all()

        # Apply filters if provided
        if search:
            companies = companies.filter(company_name__icontains=search)
        if industry:
            companies = companies.filter(industry=industry)
        if size:
            companies = companies.filter(company_size=size)

        # Get company details including HR users
        companies_data = [company.get_company_details() for company in companies]

        return JsonResponse({
            'companies': companies_data,
            'total': len(companies_data)
        }, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def company_selection(request):
    template = loader.get_template('company_selection.html')
    return HttpResponse(template.render())

@csrf_exempt
def logout_user(request):
    if request.method == 'POST':
        try:
            # Clear any session data
            request.session.flush()
            
            return JsonResponse({
                'message': 'Logout successful',
                'redirect_url': '/login.html'
            }, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
@require_http_methods(["GET"])
def get_admin_details(request):
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'Not authenticated'}, status=401)
        
        user = User.objects.get(id=user_id)
        if user.role != 'admin':
            return JsonResponse({'error': 'Not authorized'}, status=403)
        
        data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'mobile_number': user.mobile_number,
            'role': user.role,
            'is_verified': user.is_verified
        }
        return JsonResponse(data, status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def list_all_jobs(request):
    try:
        # Get filter parameters
        search = request.GET.get('search', '')
        category = request.GET.get('category', '')
        job_type = request.GET.get('job_type', '')
        company = request.GET.get('company', '')
        location = request.GET.get('location', '')

        # Start with all jobs
        jobs = JobPosting.objects.all()

        # Apply filters if provided
        if search:
            jobs = jobs.filter(title__icontains=search)
        if category:
            jobs = jobs.filter(category=category)
        if job_type:
            jobs = jobs.filter(job_type=job_type)
        if company:
            jobs = jobs.filter(company_id__company_name__icontains=company)
        if location:
            jobs = jobs.filter(location__icontains=location)

        # Convert jobs to list of dictionaries with company and HR details
        jobs_data = []
        for job in jobs:
            job_dict = job_to_dict(job)
            jobs_data.append(job_dict)

        return JsonResponse({
            'jobs': jobs_data,
            'total': len(jobs_data),
            'filters': {
                'search': search,
                'category': category,
                'job_type': job_type,
                'company': company,
                'location': location
            }
        }, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_company_jobs(request):
    try:
        # Get HR user ID from session
        hr_id = request.session.get('user_id')
        if not hr_id:
            return JsonResponse({"error": "User not authenticated"}, status=401)

        # Get HR user and their associated company
        try:
            hr_user = User.objects.get(id=hr_id, role='hr')
            company = hr_user.companies.first()
            if not company:
                return JsonResponse({"error": "HR user is not associated with any company"}, status=400)
        except User.DoesNotExist:
            return JsonResponse({"error": "HR user not found"}, status=404)

        # Get filter parameters
        search = request.GET.get('search', '')
        category = request.GET.get('category', '')
        job_type = request.GET.get('job_type', '')
        status = request.GET.get('status', '')  # For filtering by publish_option

        # Start with company's jobs
        jobs = JobPosting.objects.filter(company_id=company)

        # Calculate job statistics
        total_jobs = jobs.count()
        active_jobs = jobs.filter(publish_option='publish_now').count()
        expired_jobs = jobs.filter(publish_option='save_draft').count()

        # Apply filters if provided
        if search:
            jobs = jobs.filter(title__icontains=search)
        if category:
            jobs = jobs.filter(category=category)
        if job_type:
            jobs = jobs.filter(job_type=job_type)
        if status:
            jobs = jobs.filter(publish_option=status)

        # Convert jobs to list of dictionaries with additional company info
        jobs_data = []
        for job in jobs:
            job_dict = job_to_dict(job)
            jobs_data.append(job_dict)

        return JsonResponse({
            'jobs': jobs_data,
            'total': len(jobs_data),
            'company': {
                'id': company.id,
                'name': company.company_name,
                'logo': company.company_logo.url if company.company_logo else None
            },
            'statistics': {
                'total_jobs': total_jobs,
                'active_jobs': active_jobs,
                'expired_jobs': expired_jobs
            }
        }, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def jobs_list(request):
    template = loader.get_template('jobs_list.html')
    return HttpResponse(template.render())

@csrf_exempt
@require_http_methods(["POST"])
def apply_for_job(request, job_id):
    try:
        # Get user ID from session
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'User not authenticated'}, status=401)

        # Get job posting
        job = JobPosting.objects.get(id=job_id)
        
        # Check if user has already applied
        if JobApplication.objects.filter(job=job, applicant_id=user_id).exists():
            return JsonResponse({'error': 'You have already applied for this job'}, status=400)

        # Create application
        application = JobApplication.objects.create(
            job=job,
            applicant_id=user_id,
            cover_letter=request.POST.get('cover_letter'),
            resume=request.FILES.get('resume')
        )

        return JsonResponse({
            'message': 'Application submitted successfully',
            'application_id': application.id
        })

    except JobPosting.DoesNotExist:
        return JsonResponse({'error': 'Job not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_user_applications(request):
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'User not authenticated'}, status=401)

        applications = JobApplication.objects.filter(applicant_id=user_id)
        applications_data = [{
            'id': app.id,
            'status': app.status,
            'applied_date': app.applied_date,
            'cover_letter': app.cover_letter,
            'resume_url': app.resume.url if app.resume else None,
            'notes': app.notes,
            'job': {
                'title': app.job.title,
                'company_name': app.job.company_id.company_name,
                'company_logo': app.job.company_id.company_logo.url if app.job.company_id.company_logo else None,
                'location': app.job.location,
                'job_type': app.job.job_type,
                'salary': app.job.salary,
                'hide_salary': app.job.hide_salary
            }
        } for app in applications]

        return JsonResponse({'applications': applications_data})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_job_applications(request, job_id):
    try:
        # Get HR user ID from session
        hr_id = request.session.get('hr_id')
        if not hr_id:
            return JsonResponse({'error': 'HR not authenticated'}, status=401)

        # Verify HR is associated with the job's company
        job = JobPosting.objects.get(id=job_id)
        if job.hr_id != hr_id:
            return JsonResponse({'error': 'Unauthorized access'}, status=403)

        applications = JobApplication.objects.filter(job=job)
        applications_data = [{
            'id': app.id,
            'applicant_name': app.applicant.username,
            'applicant_email': app.applicant.email,
            'applied_date': app.applied_date,
            'status': app.status,
            'cover_letter': app.cover_letter,
            'resume_url': app.resume.url if app.resume else None,
            'notes': app.notes
        } for app in applications]

        return JsonResponse({'applications': applications_data})

    except JobPosting.DoesNotExist:
        return JsonResponse({'error': 'Job not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["PUT"])
def update_application_status(request, application_id):
    try:
        # Get HR user ID from session
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'Not authenticated'}, status=401)

        # Get HR user
        try:
            hr_user = User.objects.get(id=user_id, role='hr')
        except User.DoesNotExist:
            return JsonResponse({'error': 'HR user not found'}, status=404)

        data = json.loads(request.body)
        new_status = data.get('status')
        notes = data.get('notes')

        if not new_status:
            return JsonResponse({'error': 'Status is required'}, status=400)

        # Get application and verify HR has access
        application = JobApplication.objects.get(id=application_id)
        if application.job.hr_id != hr_user:
            return JsonResponse({'error': 'Unauthorized access'}, status=403)

        # Update application
        application.status = new_status
        if notes:
            application.notes = notes
        application.save()

        # Send email notification if application is accepted
        if new_status == 'accepted':
            try:
                # Get applicant's email
                applicant_email = application.applicant.email
                job_title = application.job.title
                company_name = application.job.company_id.company_name

                # Create email message
                message = Mail(
                    from_email=settings.FROM_EMAIL,
                    to_emails=applicant_email,
                    subject=f'Congratulations! Your application for {job_title} has been accepted',
                    html_content=f'''
                        <h2>Congratulations!</h2>
                        <p>Your application for the position of <strong>{job_title}</strong> at <strong>{company_name}</strong> has been accepted!</p>
                        <p>We were impressed with your qualifications and experience, and we believe you would be a great addition to our team.</p>
                        <p>Our HR team will contact you shortly to discuss the next steps in the hiring process.</p>
                        <p>Best regards,<br>The {company_name} Team</p>
                    '''
                )

                # Send email using SendGrid
                sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
                response = sg.send(message)
                
                if response.status_code != 202:
                    print(f"Failed to send acceptance email. Status code: {response.status_code}")
            except Exception as e:
                print(f"Error sending acceptance email: {str(e)}")
                # Continue with the response even if email fails

        return JsonResponse({
            'message': 'Application status updated successfully',
            'status': application.status
        })

    except JobApplication.DoesNotExist:
        return JsonResponse({'error': 'Application not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def apply_job_form(request):
    """Render the job application form page."""
    template = loader.get_template('apply_job.html')
    return HttpResponse(template.render())

def applied_jobs(request):
    """Render the applied jobs page."""
    # Check if user is authenticated
    user_id = request.session.get('user_id')
    if not user_id:
        return HttpResponseRedirect('/login.html')
        
    template = loader.get_template('applied_jobs.html')
    context = {
        'user_id': user_id
    }
    return HttpResponse(template.render(context, request))

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_job_application(request, application_id):
    try:
        # Get user ID from session
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'User not authenticated'}, status=401)

        # Get the application
        try:
            application = JobApplication.objects.get(id=application_id)
        except JobApplication.DoesNotExist:
            return JsonResponse({'error': 'Application not found'}, status=404)

        # Check if user is authorized to delete the application
        # User can delete if they are either the applicant or the HR of the job
        user = User.objects.get(id=user_id)
        is_applicant = application.applicant_id == user_id
        is_hr = user.role == 'hr' and application.job.hr_id == user

        if not (is_applicant or is_hr):
            return JsonResponse({'error': 'Unauthorized to delete this application'}, status=403)

        # Delete the application
        application.delete()

        return JsonResponse({
            'message': 'Application deleted successfully'
        }, status=200)

    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def admin_get_user(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'is_verified': user.is_verified
        }
        return JsonResponse(data, status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["PUT"])
def admin_update_user(request, user_id):
    try:
        data = json.loads(request.body)
        user = User.objects.get(id=user_id)

        # Update user fields
        if 'username' in data:
            user.username = data['username']
        if 'email' in data:
            user.email = data['email']
        if 'role' in data:
            user.role = data['role']
        if 'is_verified' in data:
            user.is_verified = data['is_verified']

        user.full_clean()
        user.save()

        return JsonResponse({
            'message': 'User updated successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'is_verified': user.is_verified
            }
        }, status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found.'}, status=404)
    except ValidationError as ve:
        return JsonResponse({'error': str(ve)}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def admin_get_hr(request, hr_id):
    try:
        hr = User.objects.get(id=hr_id, role='hr')
        data = {
            'id': hr.id,
            'username': hr.username,
            'email': hr.email,
            'mobile_number': hr.mobile_number,
            'is_verified': hr.is_verified,
            'companies': [{
                'id': company.id,
                'name': company.company_name,
                'email': company.company_email
            } for company in hr.companies.all()]
        }
        return JsonResponse(data, status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'HR user not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["PUT"])
def admin_update_hr(request, hr_id):
    try:
        data = json.loads(request.body)
        hr = User.objects.get(id=hr_id, role='hr')

        # Update HR fields
        if 'username' in data:
            hr.username = data['username']
        if 'email' in data:
            hr.email = data['email']
        if 'mobile_number' in data:
            hr.mobile_number = data['mobile_number']
        if 'is_verified' in data:
            hr.is_verified = data['is_verified']

        hr.full_clean()
        hr.save()

        return JsonResponse({
            'message': 'HR updated successfully',
            'hr': {
                'id': hr.id,
                'username': hr.username,
                'email': hr.email,
                'mobile_number': hr.mobile_number,
                'is_verified': hr.is_verified,
                'companies': [{
                    'id': company.id,
                    'name': company.company_name,
                    'email': company.company_email
                } for company in hr.companies.all()]
            }
        }, status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'HR user not found.'}, status=404)
    except ValidationError as ve:
        return JsonResponse({'error': str(ve)}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def admin_delete_hr(request, hr_id):
    try:
        hr = User.objects.get(id=hr_id, role='hr')
        
        # Check if HR is associated with any companies
        if hr.companies.exists():
            return JsonResponse({
                'error': 'Cannot delete HR user who is associated with companies. Please remove company associations first.'
            }, status=400)
        
        hr.delete()
        return JsonResponse({'message': 'HR deleted successfully.'}, status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'HR user not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["PUT"])
def update_admin_details(request):
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'Not authenticated'}, status=401)
        
        user = User.objects.get(id=user_id)
        if user.role != 'admin':
            return JsonResponse({'error': 'Not authorized'}, status=403)
        
        data = json.loads(request.body)
        
        # Update user fields
        if 'username' in data:
            user.username = data['username']
        if 'email' in data:
            user.email = data['email']
        if 'mobile_number' in data:
            user.mobile_number = data['mobile_number']
        if 'password' in data:
            user.set_password(data['password'])
        
        user.full_clean()
        user.save()
        
        return JsonResponse({
            'message': 'Profile updated successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'mobile_number': user.mobile_number,
                'role': user.role,
                'is_verified': user.is_verified
            }
        }, status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except ValidationError as ve:
        return JsonResponse({'error': str(ve)}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET", "POST", "PUT"])
def candidate_profile_api(request):
    """
    API endpoint for managing candidate profile
    GET: Retrieve profile data
    POST: Create new profile
    PUT: Update existing profile
    """
    print(f"Session data: {request.session.items()}")  # Debug log
    print(f"User ID from session: {request.session.get('user_id')}")  # Debug log
    
    if not request.session.get('user_id'):
        print("No user_id in session")  # Debug log
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    try:
        user = User.objects.get(id=request.session['user_id'])
        print(f"Found user: {user.username}")  # Debug log
        profile = CandidateProfile.objects.get(user=user)
        
        if request.method == "GET":
            try:
                return JsonResponse({
                    'profile': {
                        'first_name': profile.first_name,
                        'last_name': profile.last_name,
                        'job_title': profile.job_title,
                        'location': profile.location,
                        'phone': profile.phone,
                        'website': profile.website,
                        'languages': profile.languages,
                        'avatar_url': profile.avatar.url if profile.avatar else None,
                        'professional_summary': profile.professional_summary,
                        'career_objective': profile.career_objective,
                        'work_experience': profile.work_experience,
                        'education': profile.education,
                        'certifications': profile.certifications,
                        'skills': profile.skills,
                        'social_media': profile.social_media,
                        'created_at': profile.created_at,
                        'updated_at': profile.updated_at
                    }
                })
            except CandidateProfile.DoesNotExist:
                logger.warning(f"Profile not found for user {user.id}")
                return JsonResponse({'error': 'Profile not found'}, status=404)
        
        elif request.method == "POST":
            try:
                data = json.loads(request.body)
                profile = CandidateProfile.objects.create(
                    user=user,
                    first_name=data.get('first_name', ''),
                    last_name=data.get('last_name', ''),
                    job_title=data.get('job_title', ''),
                    location=data.get('location', ''),
                    phone=data.get('phone', ''),
                    website=data.get('website', ''),
                    languages=data.get('languages', ''),
                    professional_summary=data.get('professional_summary', ''),
                    career_objective=data.get('career_objective', ''),
                    work_experience=data.get('work_experience', []),
                    education=data.get('education', []),
                    certifications=data.get('certifications', []),
                    skills=data.get('skills', []),
                    social_media=data.get('social_media', {})
                )
                return JsonResponse({
                    'message': 'Profile created successfully',
                    'profile_id': profile.id
                }, status=201)
            except json.JSONDecodeError:
                logger.error("Invalid JSON data received")
                return JsonResponse({'error': 'Invalid JSON data'}, status=400)
            except ValidationError as e:
                logger.error(f"Validation error: {str(e)}")
                return JsonResponse({'error': str(e)}, status=400)
        
        elif request.method == "PUT":
            try:
                data = json.loads(request.body)
                profile = CandidateProfile.objects.get(user=user)
                
                # Update basic info
                profile.first_name = data.get('first_name', profile.first_name)
                profile.last_name = data.get('last_name', profile.last_name)
                profile.job_title = data.get('job_title', profile.job_title)
                profile.location = data.get('location', profile.location)
                profile.phone = data.get('phone', profile.phone)
                profile.website = data.get('website', profile.website)
                profile.languages = data.get('languages', profile.languages)
                profile.professional_summary = data.get('professional_summary', profile.professional_summary)
                profile.career_objective = data.get('career_objective', profile.career_objective)
                
                # Update JSON fields
                if 'work_experience' in data:
                    profile.work_experience = data['work_experience']
                if 'education' in data:
                    profile.education = data['education']
                if 'certifications' in data:
                    profile.certifications = data['certifications']
                if 'skills' in data:
                    profile.skills = data['skills']
                if 'social_media' in data:
                    profile.social_media = data['social_media']
                
                profile.save()
                return JsonResponse({'message': 'Profile updated successfully'})
            except CandidateProfile.DoesNotExist:
                logger.warning(f"Profile not found for user {user.id}")
                return JsonResponse({'error': 'Profile not found'}, status=404)
            except json.JSONDecodeError:
                logger.error("Invalid JSON data received")
                return JsonResponse({'error': 'Invalid JSON data'}, status=400)
            except ValidationError as e:
                logger.error(f"Validation error: {str(e)}")
                return JsonResponse({'error': str(e)}, status=400)
    
    except User.DoesNotExist:
        logger.error(f"User not found with ID {request.session.get('user_id')}")
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def submit_contact(request):
    try:
        data = json.loads(request.body)
        name = data.get('name')
        email = data.get('email')
        message = data.get('message')

        if not all([name, email, message]):
            return JsonResponse({'error': 'All fields are required'}, status=400)

        # Create new contact message
        contact_message = ContactMessage.objects.create(
            name=name,
            email=email,
            message=message
        )

        return JsonResponse({
            'message': 'Message sent successfully',
            'id': contact_message.id
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def get_contact_messages(request):
    try:
        # Check if user is authenticated and is admin
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'Not authenticated'}, status=401)
        
        user = User.objects.get(id=user_id)
        if user.role != 'admin':
            return JsonResponse({'error': 'Not authorized'}, status=403)

        messages = ContactMessage.objects.all().order_by('-created_at')
        messages_data = [{
            'id': msg.id,
            'name': msg.name,
            'email': msg.email,
            'message': msg.message,
            'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M'),
            'is_read': msg.is_read
        } for msg in messages]

        return JsonResponse({'messages': messages_data})

    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def mark_message_read(request, message_id):
    try:
        # Check if user is authenticated and is admin
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'Not authenticated'}, status=401)
        
        user = User.objects.get(id=user_id)
        if user.role != 'admin':
            return JsonResponse({'error': 'Not authorized'}, status=403)

        message = ContactMessage.objects.get(id=message_id)
        message.is_read = True
        message.save()

        return JsonResponse({'message': 'Message marked as read'})

    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except ContactMessage.DoesNotExist:
        return JsonResponse({'error': 'Message not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["PUT"])
def update_company(request, company_id):
    try:
        company = Company.objects.get(id=company_id)
        
        # Update company details
        company.company_name = request.POST.get('company_name', company.company_name)
        company.company_email = request.POST.get('company_email', company.company_email)
        company.industry = request.POST.get('industry', company.industry)
        company.company_size = request.POST.get('company_size', company.company_size)
        company.location = request.POST.get('location', company.location)
        
        # Handle company logo update if provided
        if 'company_logo' in request.FILES:
            company.company_logo = request.FILES['company_logo']
        
        company.save()
        
        return JsonResponse({
            'message': 'Company updated successfully',
            'company': {
                'id': company.id,
                'company_name': company.company_name,
                'company_email': company.company_email,
                'industry': company.industry,
                'company_size': company.company_size,
                'location': company.location,
                'company_logo': company.company_logo.url if company.company_logo else None
            }
        })
    except Company.DoesNotExist:
        return JsonResponse({'error': 'Company not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_company(request, company_id):
    try:
        company = Company.objects.get(id=company_id)
        company.delete()
        return JsonResponse({'message': 'Company deleted successfully'})
    except Company.DoesNotExist:
        return JsonResponse({'error': 'Company not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

