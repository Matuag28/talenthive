from django.urls import path
from . import views  # Import your views

urlpatterns = [
    # Main pages
    path('', views.home, name='index.html'),
    path('index.html', views.home, name='index.html'),
    path('aboutus.html', views.about, name='aboutus.html'),
    path('contact.html', views.contact, name='contact.html'),
    
    # Candidate related URLs
    path('login.html', views.candLogin, name='login.html'),
    path('sign-up.html', views.candSignup, name='sign-up.html'),
    path('cdashboard.html', views.cdash, name='cdashboard.html'),
    path('cprofile.html', views.cprofile, name='cprofile.html'),
    path('ceditprofile.html', views.ceditprofile, name='ceditprofile.html'),
    path('cpreview.html', views.cpreview, name='cpreview.html'),
    path('api/profile/avatar/', views.update_profile_avatar, name='update_profile_avatar'),
    
    # Employer related URLs
    path('emp_aboutUs.html', views.empAbout, name='emp_aboutUs.html'),
    path('emp_contactUs.html', views.empCon, name='emp_contactUs.html'),
    path('emp_dash.html', views.empDash, name='emp_dash.html'),
    path('emp_postJob.html', views.empPJ, name='emp_postJob.html'),
    path('emp_jobList.html', views.EJL, name='emp_jobList.html'),
    path('emp_CandidateList.html', views.empCandidateList, name='emp_CandidateList.html'),
    path('companyProfile.html', views.comPro, name='companyProfile.html'),
    path('company_selection.html', views.company_selection, name='company_selection.html'),
    
    # Urls for Job Posting
    path('api/jobs/<int:job_id>/', views.get_job_posting, name='get_job_posting'),
    path('job/', views.create_job_posting),
    path('job/<int:job_id>/update/', views.update_job_posting),
    path('job/<int:job_id>/delete/', views.delete_job_posting),
    path('jobs/', views.list_all_jobs, name='list_all_jobs'),
    path('jobs-list/', views.jobs_list, name='jobs_list'),
    path('company/jobs/', views.get_company_jobs, name='get_company_jobs'),
    
    # Candidate API URLs
    path('api/candidate/profile/', views.candidate_profile_api, name='candidate_profile_api'),
    path('api/profile/avatar/', views.update_profile_avatar, name='update_profile_avatar'),
    
    # OTP URL
    path('send_otp/', views.send_otp),
    path('verify_otp/', views.verify_otp),
    path('verify_otp.html', views.verify_otp_page),
    
    # Company URLs
    path('logcompany/', views.login_company, name='login_company'),
    path('deletecom/<int:company_id>/',views.admin_delete_company, name='deletecom'),
    path('dashboard/companies/<int:company_id>/update/', views.update_company, name='update_company'),
    path('dashboard/companies/<int:company_id>/delete/', views.delete_company, name='delete_company'),
    
    # Admin Dashboard URLs
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/companies/', views.admin_list_companies, name='admin_list_companies'),
    path('dashboard/companies/create/', views.admin_create_company, name='admin_create_company'),
    path('dashboard/companies/list/', views.admin_list_hr, name='admin_list_companies'),
    path('dashboard/users/', views.admin_list_users, name='admin_list_users'),
    path('dashboard/users/<int:user_id>/', views.admin_get_user, name='admin_get_user'),
    path('dashboard/users/<int:user_id>/update/', views.admin_update_user, name='admin_update_user'),
    path('dashboard/companies/<int:company_id>/', views.admin_delete_company, name='admin_delete_company'),
    path('dashboard/users/<int:user_id>/delete/', views.admin_delete_user, name='admin_delete_user'),
    path('dashboard/admin-details/', views.get_admin_details, name='get_admin_details'),
    path('dashboard/admin-details/update/', views.update_admin_details, name='update_admin_details'),
    path('dashboard/hr/<int:hr_id>/', views.admin_get_hr, name='admin_get_hr'),
    path('dashboard/hr/<int:hr_id>/update/', views.admin_update_hr, name='admin_update_hr'),
    path('dashboard/hr/<int:hr_id>/delete/', views.admin_delete_hr, name='admin_delete_hr'),
    
    # User API URLs
    path('register/', views.register_user, name='register_user'),
    path('login/', views.login_user, name='login_user'),
    path('logout/', views.logout_user, name='logout_user'),
    path('users/<int:user_id>/', views.get_user, name='get_user'),
    path('listusers/', views.list_users, name='list_users'),
    path('users/<int:user_id>/update/', views.update_user, name='update_user'),
    path('delusers/<int:user_id>/', views.delete_user, name='delete_candidate'),
    
    # Forgot Password URLs
    path('forgot-password.html', views.forgot_password_page, name='forgot_password.html'),
    path('reset-password.html', views.reset_password_page, name='reset_password.html'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password, name='reset_password'),
    
    # HR-Company relationship URLs
    path('api/hr/join-company/', views.hr_join_company, name='hr_join_company'),
    path('api/hr/leave-company/', views.hr_leave_company, name='hr_leave_company'),
    path('api/company/<int:company_id>/details/', views.get_company_details, name='get_company_details'),
    # path('api/hr/<int:hr_id>/companies/', views.get_hr_companies, name='get_hr_companies'),
    path('api/companies/', views.get_all_companies, name='get_all_companies'),
    
    # Job Application URLs
    path('api/jobs/<int:job_id>/apply/', views.apply_for_job, name='apply_for_job'),
    path('api/applications/', views.get_user_applications, name='get_user_applications'),
    path('api/jobs/<int:job_id>/applications/', views.get_job_applications, name='get_job_applications'),
    path('api/applications/<int:application_id>/status/', views.update_application_status, name='update_application_status'),
    path('api/applications/<int:application_id>/delete/', views.delete_job_application, name='delete_job_application'),
    path('apply-job/', views.apply_job_form, name='apply_job_form'),
    path('applied_jobs.html', views.applied_jobs, name='applied_jobs'),
    path('api/contact/', views.submit_contact, name='submit_contact'),
    path('api/contact/messages/', views.get_contact_messages, name='get_contact_messages'),
    path('api/contact/messages/<int:message_id>/read/', views.mark_message_read, name='mark_message_read'),
]