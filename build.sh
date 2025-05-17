#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Change to project directory
cd project

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate

# Create a new file to store the gunicorn configuration
echo "bind = '0.0.0.0:10000'
workers = 4
timeout = 120" > gunicorn.conf.py 