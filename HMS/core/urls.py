from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/',  auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', views.home_redirect, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('users/', views.user_list, name='user_list'),
    path('doctors/', views.doctor_list, name='doctor_list'),
    path('users/new/', views.user_create, name='user_create'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),

    path('patients/', views.patient_list, name='patient_list'),
    path('patients/new/', views.patient_create, name='patient_create'),
    path('patients/<int:pk>/', views.patient_detail, name='patient_detail'),
    path('patients/<int:pk>/edit/', views.patient_edit, name='patient_edit'),

    path('appointments/', views.appointment_list, name='appointment_list'),
    path('appointments/new/', views.appointment_create, name='appointment_create'),
    path('appointments/<int:pk>/<str:status>/', views.appointment_update_status, name='appointment_status'),

    path('calls/', views.call_center, name='call_center'),
    path('calls/callback/<int:pk>/done/', views.callback_done, name='callback_done'),

   path('pharmacy/', views.pharmacy_view, name='pharmacy_view'),
    path('laboratory/', views.lab_view, name='lab_view'),

    path('invoices/', views.billing_view, name='invoice_list'),
    path('invoices/<int:pk>/pay/', views.invoice_pay, name='invoice_pay'),
]