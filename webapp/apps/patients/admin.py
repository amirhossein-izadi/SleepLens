from django.contrib import admin
from apps.patients.models.patient import Patient

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("mrn", "last_name", "first_name", "biological_sex", "birth_date", "created_at")
    search_fields = ("mrn", "last_name", "first_name")
    list_filter = ("biological_sex", "created_at")
    readonly_fields = ("id", "created_at", "updated_at")
