#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Collect static files
python project/manage.py collectstatic --no-input

# Run migrations
python project/manage.py migrate 