from django import forms
from .models import User, PatientProfile, Appointment, StaffProfile, InpatientRecord, OutpatientRecord
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
# Gender Choices
GENDER_CHOICES = [
    ('male', 'Male'),
    ('female', 'Female'),
    ('other', 'Other')
]

# -------------------------
# Login Form
# -------------------------
class LoginForm(forms.Form):
    mobile = forms.CharField(
        max_length=15,
        label="Mobile Number",
        widget=forms.TextInput(attrs={'placeholder': 'Enter your mobile number'})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password'})
    )


# -------------------------
# Patient Register Form (User + Profile)
# -------------------------
class PatientRegisterForm(forms.ModelForm):
    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_of_birth = forms.DateField(
        widget=forms.SelectDateWidget(
            years=range(1920, timezone.now().year + 1),
            attrs={'class': 'form-select'}
        )
    )

    class Meta:
        model = PatientProfile
        fields = [
            'name', 'date_of_birth', 'contact', 'gender',
            'is_differently_abled', 'aadhaar_number', 'address'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact': forms.TextInput(attrs={'class': 'form-control'}),
            'is_differently_abled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'aadhaar_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# -------------------------
# Appointment Form
# -------------------------
class AppointmentForm(forms.ModelForm):
    
    symptom_or_disease = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Describe your symptoms or disease'}),
        label="Symptoms / Disease Description"
    )
    is_pregnant = forms.BooleanField(required=False, widget=forms.CheckboxInput())
    is_differently_abled = forms.BooleanField(required=False, widget=forms.CheckboxInput())

    class Meta:
        model = Appointment
        fields = ['symptom_or_disease','is_pregnant', 'is_differently_abled',]
class StaffRegistrationForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        widget=forms.SelectDateWidget(
            years=range(1920, timezone.now().year + 1),
            attrs={'class': 'form-select'}
        )
    )
    
    class Meta:
        model = StaffProfile
        fields = ['name', 'date_of_birth', 'gender', 'role', 'qualification', 'contact', 'address']

class InpatientForm(forms.ModelForm):
    class Meta:
        model = InpatientRecord
        fields = ['bed_number', 'case_type', 'admitted_date', 'discharged_date', 'treatment_plan']
        widgets = {
            'admitted_date': forms.SelectDateWidget(),
            'discharged_date': forms.SelectDateWidget(),
            'treatment_plan': forms.Textarea(attrs={'rows': 3}),
        }
class OutpatientForm(forms.ModelForm):
    class Meta:
        model = OutpatientRecord
        fields = ['visit_date', 'symptoms', 'diagnosis', 'prescription', 'next_visit_date']
        widgets = {
            'visit_date': forms.SelectDateWidget(),
            'next_visit_date': forms.SelectDateWidget(),
            'symptoms': forms.Textarea(attrs={'rows': 2}),
            'diagnosis': forms.Textarea(attrs={'rows': 2}),
            'prescription': forms.Textarea(attrs={'rows': 2}),
        }
