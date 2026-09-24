"""
Management command to populate the MetricDefinition catalog from SQI_METRICS.md.
Usage: python manage.py seed_metrics
"""

from django.core.management.base import BaseCommand
from apps.metrics.models.metric_definition import MetricDefinition, MetricCategory

DEFAULT_METRICS = [
    # Continuity
    {
        "key": "tib_min",
        "display_name": "Time in Bed",
        "category": MetricCategory.CONTINUITY,
        "unit": "min",
        "normal_min": 420.0,
        "normal_max": 540.0,
        "description": "Total recording duration within the lights-off window.",
        "display_order": 1,
    },
    {
        "key": "tst_min",
        "display_name": "Total Sleep Time",
        "category": MetricCategory.CONTINUITY,
        "unit": "min",
        "normal_min": 360.0,
        "normal_max": 480.0,
        "description": "Total duration spent in N1, N2, N3, or REM sleep.",
        "display_order": 2,
    },
    {
        "key": "se_pct",
        "display_name": "Sleep Efficiency",
        "category": MetricCategory.CONTINUITY,
        "unit": "%",
        "normal_min": 85.0,
        "normal_max": 100.0,
        "description": "Percentage of time in bed spent asleep (TST / Scored TIB).",
        "display_order": 3,
    },
    {
        "key": "sol_min",
        "display_name": "Sleep Onset Latency",
        "category": MetricCategory.CONTINUITY,
        "unit": "min",
        "normal_min": 5.0,
        "normal_max": 20.0,
        "description": "Time elapsed from lights off until the first epoch of sleep.",
        "display_order": 4,
    },
    {
        "key": "waso_min",
        "display_name": "Wake After Sleep Onset",
        "category": MetricCategory.CONTINUITY,
        "unit": "min",
        "normal_min": 0.0,
        "normal_max": 30.0,
        "description": "Total wake duration occurring after initial sleep onset.",
        "display_order": 5,
    },
    {
        "key": "rem_lat_min",
        "display_name": "REM Latency",
        "category": MetricCategory.CONTINUITY,
        "unit": "min",
        "normal_min": 70.0,
        "normal_max": 120.0,
        "description": "Time elapsed from sleep onset to the first REM epoch.",
        "display_order": 6,
    },

    # Fragmentation
    {
        "key": "n_awakenings",
        "display_name": "Number of Awakenings",
        "category": MetricCategory.FRAGMENTATION,
        "unit": "count",
        "normal_min": 0.0,
        "normal_max": 10.0,
        "description": "Total count of transitions from sleep to wake post-onset.",
        "display_order": 10,
    },
    {
        "key": "awakening_index",
        "display_name": "Awakening Index",
        "category": MetricCategory.FRAGMENTATION,
        "unit": "events/hr",
        "normal_min": 0.0,
        "normal_max": 2.0,
        "description": "Frequency of awakenings normalized per hour of sleep.",
        "display_order": 11,
    },
    {
        "key": "sfi",
        "display_name": "Sleep Fragmentation Index",
        "category": MetricCategory.FRAGMENTATION,
        "unit": "events/hr",
        "normal_min": 0.0,
        "normal_max": 15.0,
        "description": "Combined awakenings and stage shifts per hour of sleep.",
        "display_order": 12,
    },
    {
        "key": "longest_sleep_bout_min",
        "display_name": "Longest Sleep Bout",
        "category": MetricCategory.FRAGMENTATION,
        "unit": "min",
        "normal_min": 90.0,
        "normal_max": 240.0,
        "description": "Duration of longest continuous run of uninterrupted sleep.",
        "display_order": 13,
    },

    # Architecture
    {
        "key": "n1_pct_tst",
        "display_name": "N1 Stage Percentage",
        "category": MetricCategory.ARCHITECTURE,
        "unit": "%",
        "normal_min": 2.0,
        "normal_max": 5.0,
        "description": "Proportion of total sleep time spent in light transitional sleep (N1).",
        "display_order": 20,
    },
    {
        "key": "n2_pct_tst",
        "display_name": "N2 Stage Percentage",
        "category": MetricCategory.ARCHITECTURE,
        "unit": "%",
        "normal_min": 45.0,
        "normal_max": 55.0,
        "description": "Proportion of total sleep time spent in stable core sleep (N2).",
        "display_order": 21,
    },
    {
        "key": "n3_pct_tst",
        "display_name": "N3 Deep Sleep Percentage",
        "category": MetricCategory.ARCHITECTURE,
        "unit": "%",
        "normal_min": 15.0,
        "normal_max": 25.0,
        "description": "Proportion of total sleep time spent in slow-wave deep sleep (N3).",
        "display_order": 22,
    },
    {
        "key": "rem_pct_tst",
        "display_name": "REM Sleep Percentage",
        "category": MetricCategory.ARCHITECTURE,
        "unit": "%",
        "normal_min": 20.0,
        "normal_max": 25.0,
        "description": "Proportion of total sleep time spent in rapid eye movement dream sleep (REM).",
        "display_order": 23,
    },

    # EEG Spectral & Band Power
    {
        "key": "swa_sum",
        "display_name": "Slow-Wave Activity Sum",
        "category": MetricCategory.SPECTRAL,
        "unit": "µV²",
        "normal_min": 1000.0,
        "normal_max": None,
        "description": "Sum of delta power accumulated over all NREM epochs.",
        "display_order": 30,
    },
    {
        "key": "rel_delta_mean",
        "display_name": "Relative Delta Power",
        "category": MetricCategory.SPECTRAL,
        "unit": "ratio",
        "normal_min": 0.20,
        "normal_max": 0.60,
        "description": "Proportion of total EEG spectral power in delta band (0.5 - 4 Hz).",
        "display_order": 31,
    },

    # Microstructure
    {
        "key": "spindle_density_n2",
        "display_name": "N2 Spindle Density",
        "category": MetricCategory.MICROSTRUCTURE,
        "unit": "spindles/min",
        "normal_min": 1.0,
        "normal_max": 4.0,
        "description": "Sleep spindle rate per minute of stage N2 sleep.",
        "display_order": 40,
    },
    {
        "key": "arousal_index",
        "display_name": "Micro-Arousal Index",
        "category": MetricCategory.MICROSTRUCTURE,
        "unit": "events/hr",
        "normal_min": 0.0,
        "normal_max": 10.0,
        "description": "Transient EEG frequency arousals (>3s) per hour of sleep.",
        "display_order": 41,
    },

    # Respiration & Muscle
    {
        "key": "apnea_index",
        "display_name": "Apnea Index (AHI Proxy)",
        "category": MetricCategory.RESPIRATORY,
        "unit": "events/hr",
        "normal_min": 0.0,
        "normal_max": 5.0,
        "description": "Breathing pause events per hour of sleep (AHI proxy).",
        "display_order": 50,
    },
    {
        "key": "rem_atonia_ratio",
        "display_name": "REM Atonia Ratio",
        "category": MetricCategory.RESPIRATORY,
        "unit": "ratio",
        "normal_min": 1.3,
        "normal_max": None,
        "description": "Ratio of NREM muscle tone to REM muscle tone (> 1 indicates healthy REM paralysis).",
        "display_order": 51,
    },
]

class Command(BaseCommand):
    help = "Seeds initial MetricDefinition catalog from SQI_METRICS.md"

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0
        
        for item in DEFAULT_METRICS:
            obj, created = MetricDefinition.objects.update_or_create(
                key=item["key"],
                defaults=item
            )
            if created:
                created_count += 1
            else:
                updated_count += 1
                
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded MetricDefinition catalog: {created_count} created, {updated_count} updated."
            )
        )
