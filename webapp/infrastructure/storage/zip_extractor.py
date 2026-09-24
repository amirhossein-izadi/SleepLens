"""
Safe ZIP Archive Extractor for SleepLens.
Protects against zip-bombs and directory traversal attacks.
Extracts and catalogs patient study files into structured DTOs.
Adheres to backend_coding_guidelines (no Django dependencies in core adapter).
"""

import os
import re
import json
import zipfile
import hashlib
from pathlib import Path
from typing import List

from lib.contracts.study_dto import ExtractedFileDTO

MAX_UNCOMPRESSED_BYTES = 500 * 1024 * 1024  # 500 MB max
MAX_FILE_COUNT = 2500  # Cap on extracted files (e.g. up to 1500 30-sec epochs)

class SecurityException(Exception):
    """Raised when an uploaded archive violates security boundaries."""
    pass

class ZipExtractor:
    """Safe extraction utility for patient study ZIP archives."""

    def __init__(self, max_size_bytes: int = MAX_UNCOMPRESSED_BYTES, max_files: int = MAX_FILE_COUNT):
        self.max_size_bytes = max_size_bytes
        self.max_files = max_files

    def extract_and_catalog(self, zip_path: Path, destination_dir: Path) -> List[ExtractedFileDTO]:
        """
        Safely unpacks a study ZIP file and returns an indexed list of ExtractedFileDTOs.
        """
        zip_path = Path(zip_path)
        destination_dir = Path(destination_dir)
        destination_dir.mkdir(parents=True, exist_ok=True)

        if not zip_path.exists():
            raise FileNotFoundError(f"Archive not found: {zip_path}")

        extracted_files: List[ExtractedFileDTO] = []
        total_extracted_size = 0

        try:
            zf_context = zipfile.ZipFile(zip_path, "r")
        except zipfile.BadZipFile:
            raise ValueError(
                "Invalid Archive: The uploaded file is not a valid ZIP file. "
                "Please upload a standard .zip archive containing 30-second epoch reports or PSG recordings."
            )

        with zf_context as zf:
            infolist = zf.infolist()

            if len(infolist) > self.max_files:
                raise SecurityException(
                    f"Archive contains {len(infolist)} files, exceeding safety threshold of {self.max_files}"
                )

            for member in infolist:
                # 1. Skip directory entries
                if member.is_dir():
                    continue

                # 2. Check total uncompressed size (Zip Bomb guard)
                total_extracted_size += member.file_size
                if total_extracted_size > self.max_size_bytes:
                    raise SecurityException(
                        f"Uncompressed archive size exceeds limit of {self.max_size_bytes / (1024 * 1024):.1f} MB"
                    )

                # 3. Path Traversal Guard (prevent extraction outside destination_dir)
                target_path = (destination_dir / member.filename).resolve()
                if not str(target_path).startswith(str(destination_dir.resolve())):
                    raise SecurityException(
                        f"Path traversal detected in archive entry: {member.filename}"
                    )

                # 4. Extract member file
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(member) as source_file, open(target_path, "wb") as target_file:
                    target_file.write(source_file.read())

                # 5. Calculate SHA-256 hash for forensic traceability
                file_hash = self._calculate_sha256(target_path)

                # 6. Classify file type and parse epoch index if applicable
                file_type, epoch_idx = self._classify_file(member.filename, target_path)

                # 7. Generate lightweight preview data
                preview = self._generate_preview(target_path, file_type)

                rel_path = str(target_path.relative_to(destination_dir))
                extracted_files.append(
                    ExtractedFileDTO(
                        file_name=Path(member.filename).name,
                        relative_path=rel_path,
                        file_type=file_type,
                        file_size_bytes=target_path.stat().st_size,
                        file_hash_sha256=file_hash,
                        epoch_index=epoch_idx,
                        preview_data=preview
                    )
                )

        return extracted_files

    def _calculate_sha256(self, file_path: Path) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _classify_file(self, filename: str, path: Path) -> tuple[str, int | None]:
        lower_name = filename.lower()
        epoch_idx = None

        # Check for epoch index pattern (e.g. epoch_0142.json, ep_142.edf, 142_epoch.npz)
        epoch_match = re.search(r"(?:epoch|ep)[_-]?(\d+)", lower_name)
        if epoch_match:
            epoch_idx = int(epoch_match.group(1))

        if epoch_idx is not None or lower_name.endswith(".json") and "epoch" in lower_name:
            return "epoch_report", epoch_idx

        if "hypnogram" in lower_name or "annotation" in lower_name:
            return "annotation_edf", None

        if lower_name.endswith((".edf", ".epf")):
            return "raw_edf", None

        if lower_name.endswith((".xls", ".xlsx", ".csv")):
            return "metadata_excel", None

        if lower_name.endswith(".npz"):
            return "numpy_array", None

        return "other", None

    def _generate_preview(self, path: Path, file_type: str) -> dict:
        """Extracts lightweight summary preview for rapid frontend display."""
        preview = {}
        try:
            if file_type == "epoch_report" and path.suffix.lower() == ".json":
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    preview = {
                        "stage": data.get("stage"),
                        "duration_sec": data.get("duration", 30),
                        "channels": list(data.get("signals", {}).keys()) if isinstance(data.get("signals"), dict) else []
                    }
            elif path.suffix.lower() == ".csv":
                with open(path, "r", encoding="utf-8") as f:
                    lines = [f.readline().strip() for _ in range(3)]
                    preview = {"sample_header": lines[0] if lines else ""}
        except Exception as e:
            preview = {"preview_error": str(e)}

        return preview
