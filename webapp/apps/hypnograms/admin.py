from django.contrib import admin
from apps.hypnograms.models.epoch import SleepEpoch

@admin.register(SleepEpoch)
class SleepEpochAdmin(admin.ModelAdmin):
    list_display = ("epoch_index", "study", "stage", "ai_predicted_stage", "confidence", "is_manually_corrected", "is_lights_off", "metrics")
    list_filter = ("stage", "ai_predicted_stage", "is_manually_corrected", "is_lights_off")
    search_fields = ("study__id", "epoch_index")
    readonly_fields = ("id",)
