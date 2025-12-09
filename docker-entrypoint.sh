#!/bin/bash
set -e

# Data Seeding
# If /app/data is mounted as volume (empty), we need to populate defaults
if [ -d "/app/defaults_seed" ]; then
    if [ ! -d "/app/data/defaults" ]; then
        echo "Initializing data volume with defaults..."
        # Create defaults directory
        mkdir -p /app/data/defaults
        # Copy contents from seed
        cp -r /app/defaults_seed/* /app/data/defaults/
    else
        echo "Defaults already exist in data volume. Skipping seed."
    fi
fi

# Ensure basic data file structure exists if not present
mkdir -p /app/data/organizations

echo "Starting Accordant (Docker Mode)..."
# Exec uvicorn/python directly
exec python -m backend.main
