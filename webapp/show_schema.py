#!/usr/bin/env python3
"""
SleepLens Database Schema Viewer.
Inspects and displays the physical schema of all SleepLens domain tables.
Usage: python show_schema.py [optional_table_name]
"""

import os
import sys
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "db.sqlite3"

BLUE = "\033[94m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"

DOMAIN_TABLES = [
    "patients_patient",
    "studies_sleepstudy",
    "studies_studyfile",
    "hypnograms_sleepepoch",
    "metrics_studymetricssummary",
    "metrics_metricdefinition",
    "metrics_metricoverride",
    "reports_clinicalreport",
    "assistant_chatsession",
    "assistant_chatmessage",
]

def main():
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}. Please run migrations first.")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    target_table = sys.argv[1] if len(sys.argv) > 1 else None

    print(f"\n{BOLD}{CYAN}=================================================================={RESET}")
    print(f"{BOLD}{CYAN}             SleepLens Database Schema Inspector                 {RESET}")
    print(f"{BOLD}{CYAN}=================================================================={RESET}\n")

    tables_to_show = [target_table] if target_table else DOMAIN_TABLES

    for table in tables_to_show:
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table,))
        if not cursor.fetchone():
            if target_table:
                print(f"Table '{table}' does not exist.")
            continue

        print(f"{BOLD}{BLUE}TABLE: {YELLOW}{table}{RESET}")
        print(f"{BOLD}{'Column Name':<28} {'Type':<16} {'Nullable':<10} {'PK':<5}{RESET}")
        print("-" * 65)

        cursor.execute(f"PRAGMA table_info({table});")
        columns = cursor.fetchall()
        # column tuple: (cid, name, type, notnull, dflt_value, pk)
        for col in columns:
            cid, name, col_type, notnull, default_val, pk = col
            nullable = "NO" if notnull else "YES"
            is_pk = "PK" if pk else ""
            col_color = GREEN if pk else RESET
            print(f"{col_color}{name:<28}{RESET} {col_type:<16} {nullable:<10} {YELLOW}{is_pk:<5}{RESET}")

        # Foreign keys
        cursor.execute(f"PRAGMA foreign_key_list({table});")
        fks = cursor.fetchall()
        if fks:
            print(f"\n  {BOLD}Foreign Keys:{RESET}")
            for fk in fks:
                # (id, seq, table, from, to, on_update, on_delete, match)
                print(f"   ↳ {fk[3]} ──▶ {fk[2]}.{fk[4]} (ON DELETE: {fk[6]})")

        print("\n" + "=" * 65 + "\n")

    conn.close()

if __name__ == "__main__":
    main()
