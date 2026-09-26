#!/bin/bash
# Launches both SleepLens Backend (port 8000) and Frontend (port 3000)
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

echo "========================================================"
echo " Starting SleepLens Decision Support System"
echo " Backend:  http://127.0.0.1:8000"
echo " Frontend: http://127.0.0.1:3000"
echo " Admin:    http://127.0.0.1:8000/admin/ (admin / admin123)"
echo "========================================================"

# Start backend in background
cd "$DIR"
"$DIR/.venv/bin/python" manage.py runserver 127.0.0.1:8000 &
BACKEND_PID=$!

# Trap signals to cleanly terminate both upon Ctrl+C
trap "echo -e '\nStopping SleepLens services...'; kill $BACKEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM EXIT

# Give backend a moment to spin up
sleep 1.5

# Start frontend in foreground
cd "$DIR/frontend"
npm run dev -- --port 3000 --host 127.0.0.1
