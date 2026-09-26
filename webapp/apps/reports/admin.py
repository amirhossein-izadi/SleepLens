from django.contrib import admin
from apps.reports.models.report import ClinicalReport

@admin.register(ClinicalReport)
class ClinicalReportAdmin(admin.ModelAdmin):
    list_display = ("study", "llm_model_name", "is_signed_off", "signed_off_at", "created_at")
    list_filter = ("is_signed_off", "llm_model_name", "created_at")
    search_fields = ("study__id", "executive_summary")
    readonly_fields = ("id", "created_at", "updated_at")
