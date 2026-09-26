#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

PORT=${1:-3000}

echo "Starting OpenCode Web Client on port $PORT..."
python3 server.py --port "$PORT"
