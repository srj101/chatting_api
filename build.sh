#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Initialize the database (if needed)
python -c "from app.database import init_db; init_db()"