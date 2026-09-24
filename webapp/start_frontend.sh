#!/bin/bash
# Starts SleepLens Vite Frontend on port 3000
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR/frontend"

echo "Starting SleepLens Frontend on http://127.0.0.1:3000 ..."
npm run dev -- --port 3000 --host 127.0.0.1
