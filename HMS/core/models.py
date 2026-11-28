from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import time


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin',      'Administrator'),
        ('doctor',     'Doctor'),
        ('nurse',      'Nurse'),
        ('reception',  'Receptionist'),
        ('pharmacist', 'Pharmacist'),
        ('lab',        'Lab Technician'),
        ('patient',    'Patient'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient')
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    def initials(self):
        f = self.first_name[:1] if self.first_name else self.username[:1]
        l = self.last_name[:1] if self.last_name else ''
        return (f + l).upper()

    def __str__(self):
        return self.get_full_name() or self.username


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Patient(models.Model):
    GENDER = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]
    BLOOD = [('A+','A+'),('A-','A-'),('B+','B+'),('B-','B-'),
             ('AB+','AB+'),('AB-','AB-'),('O+','O+'),('O-','O-')]

    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='patient')
    code = models.CharField(max_length=20, unique=True, blank=True)
    full_name = models.CharField(max_length=200)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER, default='M')
    blood_group = models.CharField(max_length=3, choices=BLOOD, blank=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    allergies = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.code:
            last = Patient.objects.order_by('-id').first()
            n = (last.id + 1) if last else 1
            self.code = f'PT-{n:06d}'
        super().save(*args, **kwargs)

    def age(self):
        if not self.dob:
            return '—'
        today = timezone.now().date()
        return today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))

    def initials(self):
        parts = self.full_name.split()
        return ''.join(p[0] for p in parts[:2]).upper()

    def __str__(self):
        return f'{self.code} — {self.full_name}'


class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    specialization = models.CharField(max_length=100, blank=True)
    license_no = models.CharField(max_length=50, blank=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f'Dr. {self.user.get_full_name() or self.user.username}'


class Schedule(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.IntegerField(choices=[(i, d) for i, d in enumerate(['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])])
    start_time = models.TimeField()
    end_time = models.TimeField()
    max_slots = models.PositiveIntegerField(default=10)

    class Meta:
        unique_together = ('doctor', 'day_of_week')


class Appointment(models.Model):
    STATUS = [
        ('pending','Pending'), ('confirmed','Confirmed'),
        ('checked_in','Checked In'), ('in_progress','In Progress'),
        ('completed','Completed'), ('cancelled','Cancelled'), ('no_show','No Show'),
    ]
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    date = models.DateField()
    time = models.TimeField()
    reason = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_appointments')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'time']


class MedicalRecord(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='records')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True)
    diagnosis = models.TextField(blank=True)
    prescription = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Invoice(models.Model):
    STATUS = [('unpaid','Unpaid'), ('paid','Paid'), ('cancelled','Cancelled')]
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='invoices')
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS, default='unpaid')
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)
    amount = models.DecimalField(max_digits=10, decimal_places=2)


class Medicine(models.Model):
    name = models.CharField(max_length=200)
    batch = models.CharField(max_length=50, blank=True)
    stock = models.PositiveIntegerField(default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    expiry_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.name


class LabTest(models.Model):
    STATUS = [('pending','Pending'), ('sample','Sample Collected'), ('processing','Processing'), ('ready','Ready'), ('cancelled','Cancelled')]
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='lab_tests')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    test_name = models.CharField(max_length=200)
    result = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)


class CallLog(models.Model):
    STATUS = [('completed','Completed'), ('missed','Missed'), ('forwarded','Forwarded to Doctor'), ('callback','Callback Requested')]
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='calls')
    caller = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='calls_made')
    receiver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='calls_received')
    status = models.CharField(max_length=20, choices=STATUS, default='completed')
    reason = models.CharField(max_length=255, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_sec = models.PositiveIntegerField(default=0)


class CallbackRequest(models.Model):
    STATUS = [('pending','Pending'), ('done','Done'), ('cancelled','Cancelled')]
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    reason = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    handled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    handled_at = models.DateTimeField(null=True, blank=True)

class HospitalSettings(models.Model):
    """Single-row configuration for the hospital's public profile."""
    hospital_name = models.CharField(max_length=200, default='MediCare Hospital')
    logo_url = models.URLField(blank=True)
    address = models.TextField(blank=True)
    telephone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    operating_hours = models.CharField(max_length=120, default='Open 24 hours')
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.hospital_name


class AppointmentConfiguration(models.Model):
    """Single-row appointment booking and clinic-hours configuration."""
    DURATION_CHOICES = [(15, '15 minutes'), (30, '30 minutes'), (45, '45 minutes'), (60, '60 minutes')]

    appointment_duration = models.PositiveSmallIntegerField(choices=DURATION_CHOICES, default=30)
    monday = models.BooleanField(default=True)
    tuesday = models.BooleanField(default=True)
    wednesday = models.BooleanField(default=True)
    thursday = models.BooleanField(default=True)
    friday = models.BooleanField(default=True)
    saturday = models.BooleanField(default=False)
    sunday = models.BooleanField(default=False)
    opening_time = models.TimeField(default=time(8, 0))
    closing_time = models.TimeField(default=time(17, 0))
    max_appointments_per_doctor = models.PositiveSmallIntegerField(default=12)
    online_booking_enabled = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return 'Hospital appointment configuration'


class NotificationSettings(models.Model):
    """Single-row notification preferences for hospital operations."""
    REMINDER_CHOICES = [(1, '1 hour before'), (2, '2 hours before'), (24, '24 hours before'), (48, '48 hours before')]

    appointment_reminders = models.BooleanField(default=True)
    payment_alerts = models.BooleanField(default=True)
    lab_result_alerts = models.BooleanField(default=True)
    low_stock_alerts = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    reminder_hours_before = models.PositiveSmallIntegerField(choices=REMINDER_CHOICES, default=24)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return 'Hospital notification preferences'


class SystemPreferences(models.Model):
    """Hospital-wide display and regional preferences."""
    CURRENCY_CHOICES = [
        ('UGX', 'UGX — Ugandan Shilling'),
        ('USD', 'USD — US Dollar'),
        ('KES', 'KES — Kenyan Shilling'),
        ('TZS', 'TZS — Tanzanian Shilling'),
        ('RWF', 'RWF — Rwandan Franc'),
        ('EUR', 'EUR — Euro'),
        ('GBP', 'GBP — British Pound'),
    ]
    DATE_FORMAT_CHOICES = [
        ('d/m/Y', 'DD/MM/YYYY'),
        ('Y-m-d', 'YYYY-MM-DD'),
        ('m/d/Y', 'MM/DD/YYYY'),
    ]
    TIME_ZONE_CHOICES = [
        ('Africa/Kampala', 'Africa/Kampala — East Africa Time'),
        ('Africa/Nairobi', 'Africa/Nairobi — East Africa Time'),
        ('Africa/Dar_es_Salaam', 'Africa/Dar es Salaam — East Africa Time'),
        ('Africa/Kigali', 'Africa/Kigali — Central Africa Time'),
        ('UTC', 'UTC — Coordinated Universal Time'),
    ]
    TIME_FORMAT_CHOICES = [('24', '24-hour clock'), ('12', '12-hour clock')]

    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='UGX')
    date_format = models.CharField(max_length=10, choices=DATE_FORMAT_CHOICES, default='d/m/Y')
    time_zone = models.CharField(max_length=50, choices=TIME_ZONE_CHOICES, default='Africa/Kampala')
    time_format = models.CharField(max_length=2, choices=TIME_FORMAT_CHOICES, default='24')
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return 'Hospital system preferences'
