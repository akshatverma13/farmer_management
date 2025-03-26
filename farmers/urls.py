from django.urls import path
from . import views

urlpatterns = [
    # UI Views (Frontend)
    path('', views.login_view, name='login'),
    path('home/', views.home_view, name='home'),
    path('logout/', views.logout_view, name='logout'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('supervisor/', views.supervisor_dashboard, name='supervisor_dashboard'),
    path('surveyor/', views.surveyor_dashboard, name='surveyor_dashboard'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:id>/update/', views.user_update, name='user_update'),
    path('users/<int:id>/delete/', views.user_delete, name='user_delete'),
    path('blocks/create/', views.block_create, name='block_create'),
    path('blocks/<int:id>/update/', views.block_update, name='block_update'),
    path('blocks/<int:id>/delete/', views.block_delete, name='block_delete'),
    path('farmers/create/', views.farmer_create, name='farmer_create'),
    path('farmers/<int:id>/update/', views.farmer_update, name='farmer_update'),
    path('farmers/<int:id>/delete/', views.farmer_delete, name='farmer_delete'),
    path('users/<int:id>/profile/', views.user_profile, name='user_profile'),
    path('farmers/<int:id>/profile/', views.farmer_profile, name='farmer_profile'),
    path('download-farmers-csv/', views.download_farmers_csv, name='download_farmers_csv'),
    path('download-monthly-report/<int:report_id>/', views.download_monthly_report, name='download_monthly_report'),
    
    # API Views
    # path('api/login/', views.api_login, name='api_login'),
    # path('api/logout/', views.api_logout, name='api_logout'), comment this both for drf
    path('api/users/', views.api_users, name='api_users'),
    path('api/users/<int:id>/', views.api_users_detail, name='api_users_detail'),
    path('api/blocks/', views.api_blocks, name='api_blocks'),
    path('api/blocks/<int:id>/', views.api_blocks_detail, name='api_blocks_detail'),
    # path('api/farmers/', views.api_farmers, name='api_farmers'), I comment this  for drf
    path('api/farmers/<int:id>/', views.api_farmers_detail, name='api_farmers_detail'),
    path('api/legacy-farmers/', views.api_farmers, name='api_legacy_farmers'), # I add this for drf
]