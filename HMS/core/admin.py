from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (('Extra', {'fields': ('role', 'phone', 'avatar')}),)
    list_display = ('username', 'get_full_name', 'role', 'email')

admin.site.register(Patient)
admin.site.register(Doctor)
admin.site.register(Department)
admin.site.register(Schedule)
admin.site.register(Appointment)
admin.site.register(MedicalRecord)
admin.site.register(Invoice)
admin.site.register(InvoiceItem)
admin.site.register(Medicine)
admin.site.register(LabTest)
admin.site.register(CallLog)
admin.site.register(CallbackRequest)