from django import forms
from .models import Patient, Appointment, HospitalSettings, AppointmentConfiguration, NotificationSettings, SystemPreferences

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['full_name', 'dob', 'gender', 'blood_group', 'phone', 'email', 'address', 'emergency_contact', 'allergies']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter patient full name', 'required': 'required'}),
            'dob': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'blood_group': forms.Select(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 07XX XXX XXX', 'required': 'required'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'patient@example.com'}),
            'address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Residential address'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Name and phone number'}),
            'allergies': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Record known allergies, or leave blank if none'}),
        }

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['patient', 'doctor', 'date', 'time', 'reason', 'notes']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'doctor': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'required': 'required'}),
            'time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control', 'required': 'required'}),
            'reason': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. General consultation'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Additional information (optional)'}),
        }

class StaffUserForm(forms.ModelForm):
    from .models import Department
    specialization = forms.CharField(required=False, max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. General Practitioner'}))
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    license_no = forms.CharField(required=False, max_length=50, label='Medical licence number', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Professional registration number'}))
    consultation_fee = forms.DecimalField(required=False, min_value=0, max_digits=10, decimal_places=2, initial=0, widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01', 'placeholder': '0.00'}))
    password1 = forms.CharField(label='Password', required=False, widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control', 'placeholder': 'At least 8 characters'}))
    password2 = forms.CharField(label='Confirm password', required=False, widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control', 'placeholder': 'Re-enter password'}))

    class Meta:
        from .models import User
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'role', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. jdoe', 'required': 'required'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name', 'required': 'required'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name', 'required': 'required'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@hospital.org', 'required': 'required'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 07XX XXX XXX', 'required': 'required'}),
            'role': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for required_name in ('first_name', 'last_name', 'email', 'phone'):
            self.fields[required_name].required = True
        if self.instance is None or not self.instance.pk:
            self.fields['password1'].required = True
            self.fields['password2'].required = True
        if self.instance and self.instance.pk and self.instance.role == 'doctor':
            from .models import Doctor
            profile = Doctor.objects.filter(user=self.instance).first()
            if profile:
                self.fields['specialization'].initial = profile.specialization
                self.fields['department'].initial = profile.department_id
                self.fields['license_no'].initial = profile.license_no
                self.fields['consultation_fee'].initial = profile.consultation_fee

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get('password1')
        password2 = cleaned.get('password2')
        if self.instance.pk is None and not password1:
            self.add_error('password1', 'A password is required for a new account.')
        if password1 or password2:
            if password1 != password2:
                self.add_error('password2', 'The passwords do not match.')
            elif len(password1 or '') < 8:
                self.add_error('password1', 'Password must contain at least 8 characters.')
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password1')
        if password:
            user.set_password(password)
        if commit:
            user.save()
            if user.role == 'doctor':
                from .models import Doctor
                Doctor.objects.update_or_create(
                    user=user,
                    defaults={
                        'specialization': self.cleaned_data.get('specialization') or '',
                        'department': self.cleaned_data.get('department'),
                        'license_no': self.cleaned_data.get('license_no') or '',
                        'consultation_fee': self.cleaned_data.get('consultation_fee') or 0,
                    },
                )
        return user


class HospitalSettingsForm(forms.ModelForm):
    class Meta:
        model = HospitalSettings
        fields = ['hospital_name', 'logo_url', 'address', 'telephone', 'email', 'operating_hours']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'logo_url': forms.URLInput(attrs={'placeholder': 'https://example.com/hospital-logo.png'}),
            'operating_hours': forms.TextInput(attrs={'placeholder': 'e.g. Monday–Sunday, 24 hours'}),
        }


class AppointmentConfigurationForm(forms.ModelForm):
    class Meta:
        model = AppointmentConfiguration
        fields = [
            'appointment_duration', 'monday', 'tuesday', 'wednesday',
            'thursday', 'friday', 'saturday', 'sunday', 'opening_time',
            'closing_time', 'max_appointments_per_doctor', 'online_booking_enabled',
        ]
        widgets = {
            'appointment_duration': forms.Select(),
            'opening_time': forms.TimeInput(attrs={'type': 'time'}),
            'closing_time': forms.TimeInput(attrs={'type': 'time'}),
            'max_appointments_per_doctor': forms.NumberInput(attrs={'min': 1, 'max': 100}),
        }

    def clean(self):
        cleaned = super().clean()
        opening = cleaned.get('opening_time')
        closing = cleaned.get('closing_time')
        if opening and closing and closing <= opening:
            self.add_error('closing_time', 'Closing time must be later than opening time.')
        if not any(cleaned.get(day) for day in ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')):
            raise forms.ValidationError('Select at least one working day.')
        return cleaned


class NotificationSettingsForm(forms.ModelForm):
    class Meta:
        model = NotificationSettings
        fields = [
            'appointment_reminders', 'payment_alerts', 'lab_result_alerts',
            'low_stock_alerts', 'email_notifications', 'sms_notifications',
            'reminder_hours_before',
        ]
        widgets = {
            'reminder_hours_before': forms.Select(),
        }


class InvoiceForm(forms.ModelForm):
    class Meta:
        from .models import Invoice
        model = Invoice
        fields = ['patient', 'appointment', 'total']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'appointment': forms.Select(attrs={'class': 'form-control'}),
            'total': forms.NumberInput(attrs={'class': 'form-control', 'min': '0.01', 'step': '0.01', 'placeholder': 'Enter invoice total', 'required': 'required'}),
        }

    def clean_total(self):
        total = self.cleaned_data.get('total')
        if total is not None and total <= 0:
            raise forms.ValidationError('Invoice total must be greater than zero.')
        return total

    def clean(self):
        cleaned = super().clean()
        patient = cleaned.get('patient')
        appointment = cleaned.get('appointment')
        if patient and appointment and appointment.patient_id != patient.pk:
            self.add_error('appointment', 'Choose an appointment belonging to the selected patient.')
        return cleaned


class SystemPreferencesForm(forms.ModelForm):
    class Meta:
        model = SystemPreferences
        fields = ['currency', 'date_format', 'time_zone', 'time_format']
        widgets = {
            'currency': forms.Select(),
            'date_format': forms.Select(),
            'time_zone': forms.Select(),
            'time_format': forms.RadioSelect(),
        }

class CallLogForm(forms.ModelForm):
    class Meta:
        from .models import CallLog
        model = CallLog
        fields = ['patient', 'status', 'reason', 'duration_sec']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'reason': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Reason for the call'}),
            'duration_sec': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'Duration in seconds'}),
        }

class CallbackRequestForm(forms.ModelForm):
    class Meta:
        from .models import CallbackRequest
        model = CallbackRequest
        fields = ['patient', 'phone', 'reason']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'reason': forms.TextInput(attrs={'class': 'form-control', 'required': 'required', 'placeholder': 'Reason for follow-up'}),
        }
