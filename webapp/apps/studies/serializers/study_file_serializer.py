"""
StudyFile serializers for SleepLens API.
Provides catalog information for every extracted patient file.
"""

from rest_framework import serializers
from apps.studies.models.study_file import StudyFile

class StudyFileSerializer(serializers.ModelSerializer):
    file_type_display = serializers.CharField(source="get_file_type_display", read_only=True)

    class Meta:
        model = StudyFile
        fields = [
            "id",
            "study_id",
            "file_name",
            "relative_path",
            "file_type",
            "file_type_display",
            "file_size_bytes",
            "file_hash_sha256",
            "epoch_index",
            "preview_data",
            "created_at",
        ]
        read_only_fields = fields
