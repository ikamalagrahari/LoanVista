#!/bin/bash

# Wait for Redis to be ready
echo "Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 1
done
echo "Redis is ready!"

# Wait for database to be ready (if using external DB)
if [ -n "$DATABASE_URL" ]; then
    echo "Using external database: $DATABASE_URL"
    # For PostgreSQL, we can try a simple connection test
    python -c "
import os
import dj_database_url
import psycopg2
import time

db_config = dj_database_url.config(default=os.getenv('DATABASE_URL'))
for i in range(30):
    try:
        conn = psycopg2.connect(**db_config)
        conn.close()
        print('Database is ready!')
        break
    except Exception as e:
        print(f'Waiting for database... ({i+1}/30)')
        time.sleep(2)
else:
    echo 'Database connection timeout'
    exit 1
"
fi

python manage.py migrate
python manage.py createsuperuser --noinput
python manage.py ingest_data
python manage.py runserver 0.0.0.0:8000