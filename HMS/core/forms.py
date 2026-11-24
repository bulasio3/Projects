from django import forms
from .models import Patient, Appointment

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['full_name', 'dob', 'gender', 'blood_group', 'phone', 'email', 'address', 'emergency_contact', 'allergies']
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 2}),
            'allergies': forms.Textarea(attrs={'rows': 2}),
        }

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['patient', 'doctor', 'date', 'time', 'reason', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

class StaffUserForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', required=False, widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))
    password2 = forms.CharField(label='Confirm password', required=False, widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))

    class Meta:
        from .models import User
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'role', 'is_active']

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
        return user
