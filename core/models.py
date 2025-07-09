from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone

USER_ROLE_CHOICES = [
    ('patient', 'Patient'),
    ('staff', 'Staff'),
    ('admin', 'Admin'),
]

class UserManager(BaseUserManager):
    def create_user(self, mobile, role='patient', password=None, **extra_fields):
        if not mobile:
            raise ValueError('The Mobile number must be set')
        user = self.model(mobile=mobile, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, mobile, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(mobile, role='admin', password=password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    mobile = models.CharField(max_length=15, unique=True)
    role = models.CharField(max_length=10, choices=USER_ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'mobile'
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.mobile} ({self.role})"

class PatientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10)
    contact = models.CharField(max_length=15)
    is_differently_abled = models.BooleanField(default=False)
    aadhaar_number = models.CharField(max_length=20, unique=True)
    address = models.TextField()
    admission_number = models.CharField(max_length=20, unique=True, blank=True, null=True)  # <-- Add this line

    def __str__(self):
        return self.name

    def get_age(self):
        return timezone.now().year - self.date_of_birth.year

class Appointment(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE)
    appointment_date = models.DateField()
    symptom_or_disease = models.CharField(max_length=255)
    admission_number = models.CharField(max_length=20, unique=True)
    token_number = models.IntegerField()
    token_reset_date = models.DateTimeField(null=True, blank=True)
    is_priority = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=[('Booked', 'Booked'), ('Completed', 'Completed')], default='Booked')
    submitted_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('admission_number', 'appointment_date')
    def __str__(self):
        return f"{self.patient.name} - Token {self.token_number}"
class StaffProfile(models.Model):
    ROLE_CHOICES = [
        ('staff', 'Staff'),
        ('doctor', 'Doctor'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    qualification = models.CharField(max_length=100)
    contact = models.CharField(max_length=15)
    address = models.TextField()

class InpatientRecord(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE)
    bed_number = models.IntegerField()
    case_type = models.CharField(max_length=100)
    admitted_date = models.DateField()
    discharged_date = models.DateField(null=True, blank=True)
    treatment_plan = models.TextField()
    created_by = models.ForeignKey(StaffProfile, on_delete=models.CASCADE)

    def __str__(self):
        return f"Inpatient: {self.patient.name}"

class OutpatientRecord(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE)
    visit_date = models.DateField()
    symptoms = models.TextField()
    diagnosis = models.TextField()
    prescription = models.TextField()
    next_visit_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(StaffProfile, on_delete=models.CASCADE)

    def __str__(self):
        return f"Outpatient: {self.patient.name}"



    def __str__(self):
        return self.name