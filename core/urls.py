from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.patient_register, name='patient_register'),
    path('login/', views.user_login, name='login'),
    path('register-staff/', views.register_staff, name='register_staff'),
    path('patient/dashboard/', views.patient_home, name='patient_home'),
    path('staff/dashboard/', views.staff_home, name='staff_dashboard'),
    path('staff/add-record/', views.add_patient_record, name='add_patient_record'),
    path('staff/add-inpatient/<int:patient_id>/', views.add_inpatient, name='add_inpatient'),
    path('staff/add-outpatient/<int:patient_id>/', views.add_outpatient, name='add_outpatient'),
    path('staff/view-record/', views.view_patient_records,name='patient_records'),
   path('staff/edit-outpatient/<int:id>/', views.edit_outpatient, name='edit_outpatient'),
path('staff/delete-outpatient/<int:id>/', views.delete_outpatient, name='delete_outpatient'),

path('staff/edit-inpatient/<int:id>/', views.edit_inpatient, name='edit_inpatient'),
path('staff/delete-inpatient/<int:id>/', views.delete_inpatient, name='delete_inpatient'),
    path('staff/today-appointments/', views.today_appointments, name='today_appointments'),
    
]
