from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from .models import *
from .forms import PatientForm, AppointmentForm, StaffUserForm, HospitalSettingsForm, AppointmentConfigurationForm, NotificationSettingsForm, SystemPreferencesForm, InvoiceForm
from django.core.exceptions import PermissionDenied
from functools import wraps

# --- SECURITY DECORATOR ---
def role_required(allowed_roles):
    """Checks if the logged-in user has the correct role before showing a page."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.role not in allowed_roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
# --------------------------

ROLE_TEMPLATES = {
    'admin':      'dashboards/admin.html',
    'doctor':     'dashboards/doctor.html',
    'reception':  'dashboards/reception.html',
    'nurse':      'dashboards/nurse.html',
    'pharmacist': 'dashboards/pharmacy.html',
    'lab':        'dashboards/lab.html',
    'patient':    'dashboards/patient.html',
}
ROLE_TITLES = {
    'admin': 'Admin Dashboard', 'doctor': 'Doctor Dashboard', 'reception': 'Receptionist Dashboard',
    'nurse': 'Nurse Dashboard', 'pharmacist': 'Pharmacy Dashboard', 'lab': 'Laboratory Dashboard', 'patient': 'Patient Portal',
}

def home_redirect(request):
    return redirect('dashboard' if request.user.is_authenticated else 'login')

@login_required
def dashboard(request):
    role = getattr(request.user, 'role', None)
    if role not in ROLE_TEMPLATES:
        raise PermissionDenied(
            'Your account does not have a supported dashboard role.'
        )
    template = ROLE_TEMPLATES[role]
    today = timezone.now().date()

    ctx = {'page_title': ROLE_TITLES[role], 'active_nav': 'dashboard', 'today': today}

    if role == 'admin':
        ctx.update({
            'total_patients': Patient.objects.count(),
            'appointments_today': Appointment.objects.filter(date=today).count(),
            'pending_invoices': Invoice.objects.filter(status='unpaid').count(),
            'total_staff': User.objects.exclude(role='patient').count(),
            'low_stock_medicines': Medicine.objects.filter(stock__lt=20).count(),
            'pending_callbacks': CallbackRequest.objects.filter(status='pending').count(),
            'pending_lab_tests': LabTest.objects.exclude(status__in=['ready', 'cancelled']).count(),
            'recent_appointments': Appointment.objects.select_related('patient', 'doctor__user').order_by('-created_at')[:6],
        })
    elif role == 'reception':
        today_qs = Appointment.objects.filter(date=today).select_related('patient', 'doctor__user').order_by('time')
        active_today = today_qs.exclude(status__in=['completed', 'cancelled', 'no_show'])
        checked_in_today = today_qs.filter(status='checked_in')
        with_doctor_today = today_qs.filter(status='in_progress')
        completed_today = today_qs.filter(status='completed')
        callbacks = CallbackRequest.objects.filter(status='pending').select_related('patient').order_by('-requested_at')
        kanban_columns = []
        for s, title in [('checked_in', 'Checked In'), ('in_progress', 'With Doctor'), ('completed', 'Completed')]:
            kanban_columns.append({'title': title, 'items': today_qs.filter(status=s)[:6]})
        ctx.update({
            'today_appointments': today_qs[:12],
            'today_appointment_count': today_qs.count(),
            'checked_in_count': checked_in_today.count(),
            'with_doctor_count': with_doctor_today.count(),
            'completed_today_count': completed_today.count(),
            'active_today': active_today[:8],
            'callbacks': callbacks[:6],
            'pending_callback_count': callbacks.count(),
            'doctors': Doctor.objects.select_related('user', 'department').all()[:8],
            'available_doctor_count': Doctor.objects.filter(is_available=True).count(),
            'kanban_columns': kanban_columns,
        })
    elif role == 'doctor':
        doctor = Doctor.objects.select_related('department', 'user').filter(user=request.user).first()
        if doctor:
            doctor_appointments = Appointment.objects.filter(doctor=doctor)
            today_appointments = doctor_appointments.filter(date=today).select_related('patient').order_by('time')
            completed_today_appointments = today_appointments.filter(status='completed')
            upcoming_appointments = doctor_appointments.filter(
                date__gte=today
            ).exclude(status__in=['completed', 'cancelled', 'no_show']).select_related('patient').order_by('date', 'time')[:8]
            pending_labs = LabTest.objects.filter(
                doctor=doctor
            ).exclude(status__in=['ready', 'cancelled']).select_related('patient').order_by('-created_at')[:5]
            ready_labs = LabTest.objects.filter(
                doctor=doctor, status='ready'
            ).select_related('patient').order_by('-completed_at', '-created_at')[:6]
            recent_records = MedicalRecord.objects.filter(
                doctor=doctor
            ).select_related('patient').order_by('-created_at')[:5]
            patient_search = request.GET.get('q', '').strip()
            my_patients = Patient.objects.filter(
                appointments__doctor=doctor
            ).distinct()
            if patient_search:
                my_patients = my_patients.filter(
                    Q(full_name__icontains=patient_search) |
                    Q(code__icontains=patient_search) |
                    Q(phone__icontains=patient_search) |
                    Q(email__icontains=patient_search)
                )
            ctx.update({
                'doctor_profile': doctor,
                'my_appointments': today_appointments,
                'completed_today_appointments': completed_today_appointments,
                'upcoming_appointments': upcoming_appointments,
                'upcoming_count': doctor_appointments.filter(date__gte=today).exclude(status__in=['completed', 'cancelled', 'no_show']).count(),
                'pending_labs': pending_labs,
                'ready_labs': ready_labs,
                'recent_records': recent_records,
                'patient_search': patient_search,
                'patient_search_results': my_patients.order_by('full_name')[:8] if patient_search else Patient.objects.none(),
                'patient_count': my_patients.count() if not patient_search else Patient.objects.filter(appointments__doctor=doctor).distinct().count(),
                'completed_count': today_appointments.filter(status='completed').count(),
                'pending_count': today_appointments.filter(
                    status__in=['pending', 'confirmed', 'checked_in', 'in_progress']
                ).count(),
                'today_appointment_count': today_appointments.count(),
                'pending_lab_count': LabTest.objects.filter(
                    doctor=doctor
                ).exclude(status__in=['ready', 'cancelled']).count(),
                'ready_lab_count': LabTest.objects.filter(doctor=doctor, status='ready').count(),
                'clinical_record_count': MedicalRecord.objects.filter(doctor=doctor).count(),
            })
        else:
            ctx.update({
                'doctor_profile': None,
                'my_appointments': Appointment.objects.none(),
                'completed_today_appointments': Appointment.objects.none(),
                'upcoming_appointments': Appointment.objects.none(),
                'upcoming_count': 0,
                'pending_labs': LabTest.objects.none(),
                'ready_labs': LabTest.objects.none(),
                'recent_records': MedicalRecord.objects.none(),
                'patient_search': '',
                'patient_search_results': Patient.objects.none(),
                'patient_count': 0,
                'completed_count': 0,
                'pending_count': 0,
                'today_appointment_count': 0,
                'pending_lab_count': 0,
                'ready_lab_count': 0,
                'clinical_record_count': 0,
            })
    elif role == 'patient':
        patient = getattr(request.user, 'patient', None)
        if patient:
            patient_appointments = Appointment.objects.filter(
                patient=patient
            ).select_related('doctor__user', 'doctor__department').order_by('-date', '-time')
            ready_results = LabTest.objects.filter(
                patient=patient, status='ready'
            ).select_related('doctor__user').order_by('-completed_at', '-created_at')
            patient_records = MedicalRecord.objects.filter(
                patient=patient
            ).select_related('doctor__user').order_by('-created_at')
            patient_invoices = Invoice.objects.filter(
                patient=patient
            ).order_by('-created_at')
            ctx.update({
                'patient': patient,
                'appointments': patient_appointments.filter(
                    date__gte=today
                ).exclude(status__in=['cancelled', 'no_show'])[:5],
                'appointment_history': patient_appointments[:8],
                'recent_results': ready_results[:5],
                'ready_result_count': ready_results.count(),
                'medical_records': patient_records[:5],
                'prescription_records': patient_records.exclude(prescription='')[:5],
                'recent_invoices': patient_invoices[:5],
                'unpaid_invoice_count': patient_invoices.filter(status='unpaid').count(),
                'upcoming_appointment_count': patient_appointments.filter(
                    date__gte=today
                ).exclude(status__in=['cancelled', 'no_show', 'completed']).count(),
            })
        else:
            ctx.update({
                'patient': None,
                'appointments': Appointment.objects.none(),
                'appointment_history': Appointment.objects.none(),
                'recent_results': LabTest.objects.none(),
                'ready_result_count': 0,
                'medical_records': MedicalRecord.objects.none(),
                'prescription_records': MedicalRecord.objects.none(),
                'recent_invoices': Invoice.objects.none(),
                'unpaid_invoice_count': 0,
                'upcoming_appointment_count': 0,
            })
    elif role == 'pharmacist':
        ctx.update({'medicines': Medicine.objects.order_by('name'), 'low_stock': Medicine.objects.filter(stock__lt=20)})
    elif role == 'lab':
        ctx.update({'lab_tests': LabTest.objects.select_related('patient', 'doctor__user').order_by('-created_at')[:50], 'pending_tests': LabTest.objects.exclude(status='ready').count()})
    elif role == 'nurse':
        ctx.update({'today_appointments': Appointment.objects.filter(date=today, status__in=['checked_in', 'in_progress']).select_related('patient', 'doctor__user')[:20]})

    return render(request, template, ctx)


# --- PATIENTS ---
@login_required
@role_required(['admin', 'reception'])
def patient_list(request):
    q = request.GET.get('q', '').strip()
    patients = Patient.objects.all().order_by('-created_at')
    if q:
        patients = patients.filter(Q(full_name__icontains=q) | Q(code__icontains=q) | Q(phone__icontains=q))
    return render(request, 'patients/list.html', {'patients': patients, 'q': q, 'page_title': 'Patients', 'active_nav': 'patients'})

@login_required
@role_required(['admin', 'reception'])
def patient_create(request):
    form = PatientForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        p = form.save()
        messages.success(request, f'Patient {p.full_name} registered.')
        return redirect('patient_detail', pk=p.pk)
    return render(request, 'patients/form.html', {'form': form, 'page_title': 'Register New Patient', 'active_nav': 'patients'})

@login_required
@role_required(['admin', 'reception'])
def patient_edit(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    form = PatientForm(request.POST or None, instance=patient)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Patient updated.')
        return redirect('patient_detail', pk=pk)
    return render(request, 'patients/form.html', {'form': form, 'patient': patient, 'page_title': f'Edit {patient.full_name}', 'active_nav': 'patients'})

@login_required
@role_required(['admin', 'reception', 'doctor', 'nurse'])
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    return render(request, 'patients/detail.html', {
        'patient': patient, 'appointments': patient.appointments.order_by('-date')[:10],
        'records': patient.records.order_by('-created_at')[:10], 'invoices': patient.invoices.order_by('-created_at')[:10],
        'page_title': patient.full_name, 'active_nav': 'patients'
    })


# --- APPOINTMENTS ---
@login_required
@role_required(['admin', 'reception', 'doctor'])
def appointment_list(request):
    appointments = Appointment.objects.select_related('patient', 'doctor__user')
    if request.user.role == 'doctor':
        doctor = Doctor.objects.filter(user=request.user).first()
        appointments = appointments.filter(doctor=doctor) if doctor else appointments.none()
    appointments = appointments.order_by('-date', 'time')
    return render(request, 'appointments/list.html', {'appointments': appointments, 'today': timezone.now().date(), 'page_title': 'Appointments', 'active_nav': 'appointments'})

@login_required
@role_required(['admin', 'reception'])
def appointment_create(request):
    form = AppointmentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        appt = form.save(commit=False)
        appt.created_by = request.user
        appt.save()
        messages.success(request, 'Appointment booked.')
        return redirect('appointment_list')
    return render(request, 'appointments/form.html', {'form': form, 'page_title': 'Book Appointment', 'active_nav': 'appointments'})

@login_required
@role_required(['admin', 'reception', 'doctor', 'nurse'])
def appointment_update_status(request, pk, status):
    appt = get_object_or_404(Appointment, pk=pk)
    if request.user.role == 'doctor':
        doctor = Doctor.objects.filter(user=request.user).first()
        if not doctor or appt.doctor_id != doctor.pk:
            raise PermissionDenied
    if status in dict(Appointment.STATUS):
        appt.status = status
        appt.save()
        messages.success(request, f'Status updated to {appt.get_status_display()}.')
    return redirect('appointment_list')


# --- CALL CENTER ---
@login_required
@role_required(['admin', 'reception'])
def call_center(request):
    return render(request, 'dashboards/call_center.html', {
        'page_title': 'Call Center', 'active_nav': 'calls',
        'calls': CallLog.objects.select_related('patient').order_by('-started_at')[:50],
        'callbacks': CallbackRequest.objects.filter(status='pending').select_related('patient'),
    })

@login_required
@role_required(['admin', 'reception'])
def callback_done(request, pk):
    cb = get_object_or_404(CallbackRequest, pk=pk)
    cb.status = 'done'
    cb.handled_by = request.user
    cb.handled_at = timezone.now()
    cb.save()
    messages.success(request, 'Callback marked as done.')
    return redirect('call_center')


# --- BILLING ---
@login_required
@role_required(['admin', 'reception'])
def invoice_create(request):
    form = InvoiceForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        invoice = form.save()
        messages.success(request, f'Invoice INV-{invoice.id:04d} created for {invoice.patient.full_name}.')
        return redirect('invoice_list')
    preferences, _ = SystemPreferences.objects.get_or_create(pk=1)
    return render(request, 'invoices/form.html', {
        'form': form,
        'currency_code': preferences.currency,
        'page_title': 'Create Invoice',
        'active_nav': 'billing',
    })



@login_required
@role_required(['admin', 'reception'])
def billing_view(request):
    preferences, _ = SystemPreferences.objects.get_or_create(pk=1)
    return render(request, 'invoices/list.html', {
        'invoices': Invoice.objects.select_related('patient').order_by('-created_at'),
        'currency_code': preferences.currency,
        'page_title': 'Billing & Invoices', 'active_nav': 'billing',
    })

@login_required
@role_required(['admin', 'reception'])
def invoice_pay(request, pk):
    inv = get_object_or_404(Invoice, pk=pk)
    inv.status = 'paid'
    inv.paid_at = timezone.now()
    inv.save()
    messages.success(request, f'Invoice #{inv.id} marked as paid.')
    return redirect('billing_view')


# --- PHARMACY & LAB ---
@login_required
@role_required(['admin', 'pharmacist'])
def pharmacy_view(request):
    return render(request, 'dashboards/pharmacy.html', {
        'medicines': Medicine.objects.order_by('name'),
        'low_stock': Medicine.objects.filter(stock__lt=20),
        'page_title': 'Pharmacy',
        'active_nav': 'pharmacy',
    })

@login_required
@role_required(['admin', 'lab'])
def lab_view(request):
    return render(request, 'dashboards/lab.html', {
        'lab_tests': LabTest.objects.select_related('patient', 'doctor__user').order_by('-created_at')[:50],
        'pending_tests': LabTest.objects.exclude(status='ready').count(),
        'page_title': 'Laboratory',
        'active_nav': 'lab',
    })
 
# --- ADMIN USER MANAGEMENT ---
@login_required
@role_required(['admin'])
def user_list(request):
    q = request.GET.get('q', '').strip()
    users = User.objects.all().order_by('role', 'username')
    if q:
        users = users.filter(
            Q(username__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(email__icontains=q)
        )
    return render(request, 'users/list.html', {
        'users': users, 'q': q,
        'page_title': 'User & Role Management', 'active_nav': 'users',
    })


@login_required
@role_required(['admin'])
def user_create(request):
    form = StaffUserForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        messages.success(request, f'Account for {user.username} created.')
        return redirect('user_list')
    return render(request, 'users/form.html', {
        'form': form, 'page_title': 'Create User Account', 'active_nav': 'users',
    })


@login_required
@role_required(['admin'])
def user_edit(request, pk):
    account = get_object_or_404(User, pk=pk)
    form = StaffUserForm(request.POST or None, instance=account)
    if request.method == 'POST' and form.is_valid():
        new_role = form.cleaned_data['role']
        new_active = form.cleaned_data['is_active']
        if account.pk == request.user.pk and (new_role != 'admin' or not new_active):
            form.add_error(None, 'You cannot remove administrator access or deactivate your own account.')
        elif account.role == 'admin' and account.is_active and (new_role != 'admin' or not new_active) and User.objects.filter(role='admin', is_active=True).count() <= 1:
            form.add_error(None, 'You cannot remove or deactivate the last active administrator.')
        else:
            user = form.save()
            messages.success(request, f'Account for {user.username} updated.')
            return redirect('user_list')
    return render(request, 'users/form.html', {
        'form': form, 'account': account,
        'page_title': f'Edit Account: {account.username}', 'active_nav': 'users',
    })


# --- DOCTOR DIRECTORY ---
@login_required
@role_required(['admin', 'doctor', 'reception', 'nurse', 'pharmacist', 'lab', 'patient'])
def doctor_list(request):
    # Backfill missing profiles for existing accounts assigned the Doctor role.
    # get_or_create is safe to repeat and never overwrites existing doctor details.
    doctor_users = User.objects.filter(role='doctor')
    for doctor_user in doctor_users.iterator():
        Doctor.objects.get_or_create(user=doctor_user)
    doctors = Doctor.objects.select_related('user', 'department').order_by('user__last_name', 'user__first_name')
    return render(request, 'doctors/list.html', {
        'doctors': doctors,
        'page_title': 'Doctor Directory',
        'active_nav': 'doctors',
    })


@login_required
@role_required(['admin'])
def hospital_settings(request):
    profile, _ = HospitalSettings.objects.get_or_create(pk=1)
    appointment_config, _ = AppointmentConfiguration.objects.get_or_create(pk=1)
    notification_settings, _ = NotificationSettings.objects.get_or_create(pk=1)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'save_notifications':
            notification_form = NotificationSettingsForm(request.POST, instance=notification_settings)
            if notification_form.is_valid():
                notification_form.save()
                messages.success(request, 'Notification preferences saved successfully.')
                return redirect('hospital_settings')
            messages.error(request, 'Please review the notification preferences.')
        if action == 'save_appointment_config':
            appointment_form = AppointmentConfigurationForm(request.POST, instance=appointment_config)
            if appointment_form.is_valid():
                appointment_form.save()
                messages.success(request, 'Appointment configuration saved successfully.')
                return redirect('hospital_settings')
            messages.error(request, 'Please review the appointment configuration fields.')
        if action == 'save_profile':
            profile_form = HospitalSettingsForm(request.POST, instance=profile)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Hospital profile saved successfully.')
                return redirect('hospital_settings')
            messages.error(request, 'Please correct the highlighted profile fields.')
        if action == 'add_department':
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            if not name:
                messages.error(request, 'Please enter a department name.')
            elif Department.objects.filter(name__iexact=name).exists():
                messages.error(request, 'A department with that name already exists.')
            else:
                Department.objects.create(name=name, description=description)
                messages.success(request, f'{name} department added successfully.')
            return redirect('hospital_settings')
        if action == 'delete_department':
            department = get_object_or_404(Department, pk=request.POST.get('department_id'))
            if Doctor.objects.filter(department=department).exists():
                messages.error(request, 'This department is assigned to a doctor and cannot be deleted yet.')
            else:
                department_name = department.name
                department.delete()
                messages.success(request, f'{department_name} department deleted.')
            return redirect('hospital_settings')
    if request.method != 'POST' or request.POST.get('action') != 'save_profile':
        profile_form = HospitalSettingsForm(instance=profile)
    if request.method != 'POST' or request.POST.get('action') != 'save_appointment_config':
        appointment_form = AppointmentConfigurationForm(instance=appointment_config)
    if request.method != 'POST' or request.POST.get('action') != 'save_notifications':
        notification_form = NotificationSettingsForm(instance=notification_settings)

    return render(request, 'settings/index.html', {
        'departments': Department.objects.order_by('name'),
        'doctor_count': Doctor.objects.count(),
        'profile': profile,
        'profile_form': profile_form,
        'appointment_config': appointment_config,
        'appointment_form': appointment_form,
        'notification_settings': notification_settings,
        'notification_form': notification_form,
        'page_title': 'Hospital Settings',
        'active_nav': 'settings',
    })


# --- SECURITY & ACCESS ---
@login_required
@role_required(['admin'])
def security_access(request):
    staff_users = User.objects.exclude(role='patient')

    if request.method == 'POST' and request.POST.get('action') == 'toggle_staff_status':
        account = get_object_or_404(User, pk=request.POST.get('account_id'))
        if account.role == 'patient':
            messages.error(request, 'Patient accounts cannot be managed from staff security.')
        elif account.pk == request.user.pk and account.is_active:
            messages.error(request, 'You cannot deactivate your own administrator account.')
        elif account.role == 'admin' and account.is_active and User.objects.filter(role='admin', is_active=True).count() <= 1:
            messages.error(request, 'The last active administrator cannot be deactivated.')
        else:
            account.is_active = not account.is_active
            account.save(update_fields=['is_active'])
            status_label = 'activated' if account.is_active else 'deactivated'
            messages.success(request, f'{account.username} has been {status_label}.')
        return redirect('security_access')

    q = request.GET.get('q', '').strip()
    selected_role = request.GET.get('role', '').strip()
    selected_status = request.GET.get('status', '').strip()
    account_users = staff_users.order_by('role', 'username')
    if q:
        account_users = account_users.filter(
            Q(username__icontains=q) | Q(first_name__icontains=q) |
            Q(last_name__icontains=q) | Q(email__icontains=q)
        )
    valid_roles = {value for value, label in User.ROLE_CHOICES if value != 'patient'}
    if selected_role in valid_roles:
        account_users = account_users.filter(role=selected_role)
    else:
        selected_role = ''
    if selected_status == 'active':
        account_users = account_users.filter(is_active=True)
    elif selected_status == 'inactive':
        account_users = account_users.filter(is_active=False)
    else:
        selected_status = ''

    role_summary = []
    for role_value, role_label in User.ROLE_CHOICES:
        if role_value == 'patient':
            continue
        role_summary.append({
            'label': role_label,
            'total': staff_users.filter(role=role_value).count(),
            'active': staff_users.filter(role=role_value, is_active=True).count(),
        })
    context = {
        'page_title': 'Security & Access',
        'active_nav': 'settings',
        'total_staff': staff_users.count(),
        'active_staff': staff_users.filter(is_active=True).count(),
        'inactive_staff': staff_users.filter(is_active=False).count(),
        'active_admins': User.objects.filter(role='admin', is_active=True).count(),
        'recent_accounts': staff_users.order_by('-date_joined')[:8],
        'role_summary': role_summary,
        'account_users': account_users,
        'q': q,
        'selected_role': selected_role,
        'selected_status': selected_status,
        'role_choices': [(value, label) for value, label in User.ROLE_CHOICES if value != 'patient'],
    }
    return render(request, 'settings/security_access.html', context)


@login_required
@role_required(['admin'])
def system_preferences(request):
    preferences, _ = SystemPreferences.objects.get_or_create(pk=1)
    if request.method == 'POST' and request.POST.get('action') == 'save_system_preferences':
        preferences_form = SystemPreferencesForm(request.POST, instance=preferences)
        if preferences_form.is_valid():
            preferences_form.save()
            messages.success(request, 'System preferences saved successfully.')
            return redirect('system_preferences')
        messages.error(request, 'Please review the highlighted system preference fields.')
    else:
        preferences_form = SystemPreferencesForm(instance=preferences)

    return render(request, 'settings/system_preferences.html', {
        'page_title': 'System Preferences',
        'active_nav': 'settings',
        'preferences': preferences,
        'preferences_form': preferences_form,
    })
