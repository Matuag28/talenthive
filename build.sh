#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Create a new file to store the gunicorn configuration
echo "bind = '0.0.0.0:10000'
workers = 4
timeout = 120" > gunicorn.conf.py

# Collect static files
python project/manage.py collectstatic --no-input

# Run migrations
python project/manage.py migrate 