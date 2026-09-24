"""
UUID utilities for SleepLens.
Provides time-sortable UUIDv7 generation with fallback to UUIDv4.
"""

import uuid

try:
    import uuid6
    def get_uuid7() -> uuid.UUID:
        return uuid6.uuid7()
except ImportError:
    def get_uuid7() -> uuid.UUID:
        return uuid.uuid4()
