from django.db import models
from django.core.validators import RegexValidator, MinLengthValidator
from django.core.exceptions import ValidationError
import os
from django.conf import settings

#create model for candiadate at 9:23 pm on 24 04 25

from django.db import models
from django.core.validators import RegexValidator, MinLengthValidator
from django.contrib.auth.hashers import make_password, check_password

class User(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('hr', 'HR'),
        ('admin', 'Admin'),
    ]
    
    username = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    mobile_number = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex=r'^\+?\d{10,15}$', message="Enter a valid mobile number.")]
    )
    password = models.CharField(
        max_length=128,
        validators=[MinLengthValidator(8)]
    )
    is_verified = models.BooleanField(default=False)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    reset_password_token = models.CharField(max_length=100, null=True, blank=True)
    reset_password_token_created_at = models.DateTimeField(null=True, blank=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.username


# create model for employer at 01:33 am on 25 04 25

class Company(models.Model):
    INDUSTRY_CHOICES = [
        ('it', 'Information Technology'),
        ('finance', 'Finance'),
        ('healthcare', 'Healthcare'),
        ('education', 'Education'),
        ('manufacturing', 'Manufacturing'),
        ('retail', 'Retail'),
        ('other', 'Other'),
    ]

    COMPANY_SIZE_CHOICES = [
        ('1-10', '1-10 employees'),
        ('11-50', '11-50 employees'),
        ('51-200', '51-200 employees'),
        ('201-500', '201-500 employees'),
        ('501-1000', '501-1000 employees'),
        ('1000+', '1000+ employees'),
    ]

    def company_logo_path(instance, filename):
        # Create the directory if it doesn't exist
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'company_logos')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        # Return the path where the file should be saved
        return os.path.join('company_logos', filename)

    company_name = models.CharField(max_length=255)
    company_email = models.EmailField(unique=True)
    industry = models.CharField(max_length=100, choices=INDUSTRY_CHOICES)
    company_size = models.CharField(max_length=50, choices=COMPANY_SIZE_CHOICES)
    location = models.CharField(max_length=255)
    company_logo = models.ImageField(upload_to=company_logo_path, null=True, blank=True)
    hr_users = models.ManyToManyField(User, related_name='companies', limit_choices_to={'role': 'hr'})

    def __str__(self):
        return self.company_name

    def get_company_details(self):
        return {
            'id': self.id,
            'company_name': self.company_name,
            'company_email': self.company_email,
            'industry': self.industry,
            'company_size': self.company_size,
            'location': self.location,
            'company_logo': self.company_logo.url if self.company_logo else None,
            'hr_users': [{
                'id': hr.id,
                'username': hr.username,
                'email': hr.email,
                'mobile_number': hr.mobile_number,
                'is_verified': hr.is_verified
            } for hr in self.hr_users.all()]
        }









# Job Posting model for job seeker at 01:54 am on 23 04 15

from django.db import models

class JobPosting(models.Model):
    EDUCATION_LEVEL_CHOICES = [
        ('high_school', 'High School Diploma/GED'),
        ('associate', "Associate's Degree"),
        ('bachelor', "Bachelor's Degree"),
        ('master', "Master's Degree"),
        ('doctorate', 'Doctorate/PhD'),
        ('professional', 'Professional Degree (MD, JD, etc.)'),
        ('certification', 'Professional Certification'),
        ('none', 'No Specific Requirement'),
    ]

    VISIBILITY_CHOICES = [
        ('public', 'Public - Visible to everyone'),
        ('private', 'Private - Only visible with direct link'),
        ('company', 'Company - Only visible to your company employees'),
    ]

    PUBLISH_OPTION_CHOICES = [
        ('publish_now', 'Publish immediately'),
        ('save_draft', 'Save as draft'),
        ('schedule', 'Schedule publishing'),
    ]

    title = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    job_type = models.CharField(max_length=50)  # No choices
    experience_level = models.CharField(max_length=50)  # No choices
    workplace_type = models.CharField(max_length=50)  # No choices
    location = models.CharField(max_length=255)
    country = models.CharField(max_length=100)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    hide_salary = models.BooleanField(default=False)
    company_overview = models.TextField()
    job_description = models.TextField()
    requirements = models.TextField()
    benefits = models.TextField()
    required_skills = models.TextField()
    preferred_skills = models.TextField()
    education_level = models.CharField(max_length=50, choices=EDUCATION_LEVEL_CHOICES)  # With choices
    languages = models.TextField()
    application_deadline = models.DateField(null=True, blank=True)
    require_resume = models.BooleanField(default=True)
    require_cover_letter = models.BooleanField(default=False)
    require_portfolio = models.BooleanField(default=False)
    require_references = models.BooleanField(default=False)
    visibility = models.CharField(max_length=50, choices=VISIBILITY_CHOICES)  # With choices
    featured_job = models.BooleanField(default=False)
    urgent_job = models.BooleanField(default=False)
    publish_option = models.CharField(max_length=50, choices=PUBLISH_OPTION_CHOICES)  # With choices
    schedule_date = models.DateTimeField(null=True, blank=True)
    hr_id = models.ForeignKey('User', on_delete=models.CASCADE, related_name='posted_jobs', null=True)
    company_id = models.ForeignKey('Company', on_delete=models.CASCADE, related_name='job_postings', null=True)

    def __str__(self):
        return self.title



# model for candidateProfile

class JobApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewing', 'Reviewing'),
        ('shortlisted', 'Shortlisted'),
        ('rejected', 'Rejected'),
        ('accepted', 'Accepted')
    ]

    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_applications')
    applied_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    cover_letter = models.TextField(blank=True, null=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('job', 'applicant')
        ordering = ['-applied_date']

    def __str__(self):
        return f"{self.applicant.username} - {self.job.title}"


class CandidateProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    job_title = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    website = models.URLField(blank=True)
    languages = models.CharField(max_length=200, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    professional_summary = models.TextField(blank=True)
    career_objective = models.TextField(blank=True)
    work_experience = models.JSONField(default=list, blank=True)
    education = models.JSONField(default=list, blank=True)
    certifications = models.JSONField(default=list, blank=True)
    skills = models.JSONField(default=list, blank=True)
    social_media = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}'s Profile"

    class Meta:
        ordering = ['-updated_at']


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Message from {self.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

