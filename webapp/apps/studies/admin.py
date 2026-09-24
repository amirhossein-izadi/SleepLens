from django.contrib import admin
from apps.studies.models.study import SleepStudy
from apps.studies.models.study_file import StudyFile

@admin.register(SleepStudy)
class SleepStudyAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "study_date", "study_type", "status", "total_epochs", "created_at")
    list_filter = ("status", "study_type", "study_date")
    search_fields = ("patient__first_name", "patient__last_name", "patient__mrn")
    readonly_fields = ("id", "created_at", "updated_at")

@admin.register(StudyFile)
class StudyFileAdmin(admin.ModelAdmin):
    list_display = ("file_name", "study", "file_type", "epoch_index", "file_size_bytes", "created_at")
    list_filter = ("file_type", "created_at")
    search_fields = ("file_name", "study__id")
