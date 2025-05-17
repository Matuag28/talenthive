from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('talenthive.urls')),  # Include all URLs from the talenthive app
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# # Custom admin dashboard URLs (using 'dashboard' instead of 'admin' to avoid conflict)
# path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
# path('dashboard/create-company/', views.admin_create_company, name='admin_create_company'),
# path('dashboard/companies/', views.admin_list_companies, name='admin_list_companies'),
# path('dashboard/hr/', views.admin_list_hr, name='admin_list_hr'),
# path('dashboard/users/', views.admin_list_users, name='admin_list_users'),
# path('dashboard/companies/<int:company_id>/', views.admin_delete_company, name='admin_delete_company'),
# path('dashboard/users/<int:user_id>/', views.admin_delete_user, name='admin_delete_user'),

# Admin dashboard URLs
    