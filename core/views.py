import uuid
from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count
from django.utils.timezone import now
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.utils import timezone
from datetime import datetime
from .models import User, PatientProfile, Appointment, StaffProfile, InpatientRecord, OutpatientRecord
from .forms import PatientRegisterForm, LoginForm, AppointmentForm, StaffRegistrationForm,InpatientForm,OutpatientForm
from django.contrib.auth.decorators import user_passes_test
from .predictor import train_predict_model 
def generate_admission_number():
    hospital_code="HOSP01"
    current_year = datetime.now().year
    year_str = str(current_year)

    # Step 1: Filter existing admission numbers for the hospital and current year
    existing_numbers = PatientProfile.objects.filter(
        admission_number__startswith=f"{hospital_code}{year_str}"
    ).values_list('admission_number', flat=True)

    # Step 2: Extract and find the highest serial number
    last_serial = 0
    for adm_num in existing_numbers:
        try:
            serial = int(adm_num[-6:])  # last 6 digits
            if serial > last_serial:
                last_serial = serial
        except ValueError:
            continue  # skip malformed ones

    # Step 3: Increment and format
    new_serial = last_serial + 1
    serial_str = str(new_serial).zfill(6)

    # Step 4: Return new admission number
    return f"{hospital_code}{year_str}{serial_str}"


def get_next_token(is_priority):
    if is_priority:
        max_priority = Appointment.objects.filter(is_priority=True).aggregate(Max('token_number'))['token_number__max']
        return (max_priority or 0) + 1 if (max_priority or 0) < 10 else get_next_token(False)
    else:
        max_normal = Appointment.objects.filter(is_priority=False).aggregate(Max('token_number'))['token_number__max'] or 10
        return max_normal + 1


def calculate_age(dob):
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def patient_register(request):
    if request.method == 'POST':
        form = PatientRegisterForm(request.POST)
        if form.is_valid():
            # Step 1: Create the user
            dob = form.cleaned_data['date_of_birth']
            password = dob.strftime('%d%m%Y')
            user = User.objects.create_user(
                mobile=form.cleaned_data['contact'],  # assuming this maps to mobile
                password=password,  # use a secure password system later
                role='patient'
            )

            # Step 2: Create the PatientProfile instance
            patient_profile = form.save(commit=False)
            patient_profile.user = user
            
            patient_profile.admission_number = generate_admission_number()
            # Optional but good: calculate and assign age
            

            # Save the profile
            patient_profile.save()

            return redirect('login')
    else:
        form = PatientRegisterForm()

    return render(request, 'register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            mobile = form.cleaned_data['mobile']
            password = form.cleaned_data['password']
            user = authenticate(request, mobile=mobile, password=password)
            if user:
                login(request, user)
                if user.role == 'patient':
                    return redirect('patient_home')
                elif user.role == 'staff':
                    return redirect('staff_dashboard')
                elif user.role == 'admin':
                    return redirect('admin_dashboard')
            else:
                messages.error(request, "Invalid login credentials")
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


@login_required
def patient_home(request):
    if not request.user.is_authenticated:
        return render(request, 'welcome')

    profile = PatientProfile.objects.get(user=request.user)
    age = calculate_age(profile.date_of_birth)
    appointments = Appointment.objects.filter(patient=profile).order_by('-appointment_date')
    today = timezone.now().date()
    for appointment in appointments:
        if appointment.appointment_date < today:
            if appointment.status != 'Completed':  # Check if status is already 'Completed'
                appointment.status = 'Completed'
                appointment.save()
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            today = timezone.now().date()
            already_booked = Appointment.objects.filter(patient=profile, appointment_date=today).exists()
        
            if already_booked:
                messages.warning(request, "You already have an appointment for today.")
                
                return redirect('patient_home')
           
            appointment = form.save(commit=False)
            appointment.patient = profile
            appointment.appointment_date = timezone.now().date()
            appointment.admission_number = profile.admission_number
            is_pregnant = form.cleaned_data.get('is_pregnant', False)
            is_differently_abled = form.cleaned_data.get('is_differently_abled', False)
            is_priority = age >= 60 or is_pregnant or is_differently_abled

            appointment.age = age
            appointment.is_priority = is_priority
            appointment.token_number = get_next_token(is_priority)
            appointment.status = 'Booked'
            appointment.save()

            messages.success(request, f"Appointment booked! Your token number is {appointment.token_number}")
            return redirect('patient_home')
        else:
            # Debugging the form errors
            print(form.errors)
    else:
        
        form = AppointmentForm()

    return render(request, 'patient_home.html', {
        'profile': profile,
        'form': form,
        'appointments': appointments,
        'age': age,
        'today': date.today() 
    })

# Only allow admin users to access
def is_admin(user):
    return user.role == 'admin'

@user_passes_test(is_admin)
def register_staff(request):
    if request.method == 'POST':
        form = StaffRegistrationForm(request.POST)
        if form.is_valid():
            # Step 1: Create user from staff contact as mobile
            dob = form.cleaned_data['date_of_birth']
            password = dob.strftime('%d%m%Y')
            mobile = form.cleaned_data['contact']

            user = User.objects.create_user(
                mobile=mobile,
                password=password,
                role='staff'
            )

            # Step 2: Create staff profile and link user
            staff = form.save(commit=False)
            staff.user = user
            staff.save()

            return redirect('admin_dashboard')
    else:
        form = StaffRegistrationForm()
    return render(request, 'register_staff.html', {'form': form})

@login_required
@login_required
def view_patient_records(request):
    staff = StaffProfile.objects.get(user=request.user)
    query = request.GET.get('admission_number', '')
    
    inpatients = outpatients = []
    patients = PatientProfile.objects.all()
    all_inpatients=InpatientRecord.objects.all()
    all_outpatients=OutpatientRecord.objects.all()
    # age = calculate_age(patients.date_of_birth)
    if query:
        inpatients = InpatientRecord.objects.filter(patient__admission_number=query, created_by=staff).order_by('-admitted_date')
        outpatients = OutpatientRecord.objects.filter(patient__admission_number=query, created_by=staff).order_by('-visit_date')
        
    return render(request, 'patient_records.html', {
        'staff': staff,
        'patients': patients,
        'inpatients': inpatients,
        'outpatients': outpatients,
        'all_inpatients': all_inpatients,
        'all_outpatients': all_outpatients
        
    })

def add_patient_record(request):
    admission_number = request.GET.get('admission_number')
    patient = None

    if admission_number:
        try:
            patient = PatientProfile.objects.get(admission_number=admission_number)
        except PatientProfile.DoesNotExist:
            patient = None

    return render(request, 'add_patient_record.html', {'patient': patient})   
@login_required
def staff_home(request):
    staff = StaffProfile.objects.get(user=request.user)
    inpatients = InpatientRecord.objects.all()
    outpatients = OutpatientRecord.objects.all()
    return render(request, 'staff_home.html', {
        'staff': staff,
        'inpatients': inpatients,
        'outpatients': outpatients
    })

@login_required
def add_inpatient(request, patient_id):
    staff = StaffProfile.objects.get(user=request.user)
    patient = get_object_or_404(PatientProfile, id=patient_id)

    if request.method == 'POST':
        form = InpatientForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.patient = patient
            record.created_by = staff
            record.save()
            return redirect('patient_records')
    else:
        form = InpatientForm()

    return render(request, 'add_inpatient.html', {'form': form, 'patient': patient})

@login_required
def add_outpatient(request, patient_id):
    staff = StaffProfile.objects.get(user=request.user)
    patient = get_object_or_404(PatientProfile, id=patient_id)

    if request.method == 'POST':
        form = OutpatientForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.patient = patient
            record.created_by = staff
            record.save()
            return redirect('patient_records')
    else:
        form = OutpatientForm()

    return render(request, 'add_outpatient.html', {'form': form, 'patient': patient})

@login_required
def edit_outpatient(request, id):
    outpatient = get_object_or_404(OutpatientRecord, id=id)
    form = OutpatientForm(instance=outpatient)

    if request.method == 'POST':
        form = OutpatientForm(request.POST, instance=outpatient)
        if form.is_valid():
            form.save()
            return redirect('patient_records')  # or wherever you want to redirect
    return render(request, 'edit_outpatient.html', {'form': form, 'outpatient': outpatient})
# For deleting outpatient record
@login_required
def delete_outpatient(request, id):
    outpatient = get_object_or_404(OutpatientRecord, id=id)
    outpatient.delete()
    return redirect('patient_records')


# For editing inpatient record
@login_required
def edit_inpatient(request, id):
    inpatient = get_object_or_404(InpatientRecord, id=id)
    form = InpatientForm(instance=inpatient)
    if request.method == 'POST':
        form = InpatientForm(request.POST, instance=inpatient)
        if form.is_valid():
            form.save()
            return redirect('patient_records')
    return render(request, 'edit_inpatient.html', {'form': form, 'inpatient': inpatient})


# For deleting inpatient record
@login_required
def delete_inpatient(request, id):
    inpatient = get_object_or_404(InpatientRecord, id=id)
    inpatient.delete()
    return redirect('patient_records')
@login_required
def today_appointments(request):
    today = date.today()
    appointments = Appointment.objects.filter(appointment_date=today).order_by('token_number')

    return render(request, 'today_appointments.html', {
        'appointments': appointments,
        'today': today,
    })

def get_inpatient_bed_prediction():
    today = date.today()

    # Count new admissions per day
    last_14_days = InpatientRecord.objects.filter(admitted_date__gte=today - timedelta(days=14))
    daily_counts = last_14_days.values('admitted_date').annotate(count=Count('id')).order_by('admitted_date')

    # Calculate moving average
    count_list = [entry['count'] for entry in daily_counts]
    if count_list:
        predicted_inpatients = sum(count_list) // len(count_list)
    else:
        predicted_inpatients = 2  # default/fallback

    return predicted_inpatients

def get_outpatient_prediction():
    today = date.today()

    last_14_days = OutpatientRecord.objects.filter(visit_date__gte=today - timedelta(days=14))
    daily_counts = last_14_days.values('visit_date').annotate(count=Count('id')).order_by('visit_date')

    count_list = [entry['count'] for entry in daily_counts]
    if count_list:
        predicted_outpatients = sum(count_list) // len(count_list)
    else:
        predicted_outpatients = 5  # fallback

    return predicted_outpatients

@login_required
def admin_dashboard(request):
    total_patients = PatientProfile.objects.count()
    total_inpatients = InpatientRecord.objects.count()
    total_outpatients = OutpatientRecord.objects.count()
    total_staff = StaffProfile.objects.count()
    total_doctors = StaffProfile.objects.filter(role='doctor').count()
    
    total_beds = 50  # Example total beds
    occupied_beds = total_inpatients
    available_beds = total_beds - occupied_beds
    
    predicted_inpatients = train_predict_model('D:/niral/HMS\hospital_system/core/data/Book1.csv')
    predicted_outpatients = train_predict_model('D:/niral/HMS\hospital_system/core/data/Book2.csv')

    extra_beds_needed = max(0, predicted_inpatients - available_beds)
    bed_status_message = (
        f"Predicted inpatients tomorrow: {predicted_inpatients}. "
        f"{'Sufficient beds available.' if extra_beds_needed == 0 else f'Not enough beds! Please arrange {extra_beds_needed} more.'}"
    )

    
    context = {
        'total_patients': total_patients,
        'total_inpatients': total_inpatients,
        'total_outpatients': total_outpatients,
        'total_staff': total_staff,
        'total_doctors': total_doctors,
        'available_beds': available_beds,
        'occupied_beds': occupied_beds,
        'total_beds':total_beds,
        # Add AI prediction result if available here
        'predicted_bed_status': bed_status_message,
        'predicted_inpatients': predicted_inpatients,
        'predicted_outpatients': predicted_outpatients,
    }

    return render(request, 'admin_dashboard.html', context)


def user_logout(request):
    logout(request)
    return redirect('home')

def home(request):
    return render(request, 'welcome.html')  # or 'welcome.html' if you named it that
