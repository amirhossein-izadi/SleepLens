#!/bin/bash
# Starts SleepLens Django Backend on port 8000
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "Starting SleepLens Backend on http://127.0.0.1:8000 ..."
"$DIR/.venv/bin/python" manage.py runserver 127.0.0.1:8000
