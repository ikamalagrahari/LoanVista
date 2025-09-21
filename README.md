# Credit Approval System

A Django-based credit approval system with background task processing using Celery and Redis.

## Features

- Customer registration with credit limit calculation
- Loan eligibility checking based on credit score
- Loan creation and management
- Background data ingestion from Excel files
- REST API endpoints
- Docker containerization

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

## Quick Start

### 1. Clone the repository
```bash
git clone <repository-url>
cd Credit Approval System
```

### 2. Environment Setup

Copy the example environment file:
```bash
cp example.env .env
```

Edit `.env` to configure:
- `DATABASE_URL`: Your PostgreSQL database URL (Neon, Supabase, etc.)
- `USER_ID` and `GROUP_ID`: Your host user ID and group ID to avoid permission issues

To get your user ID on Linux/Mac:
```bash
id -u  # USER_ID
id -g  # GROUP_ID
```

On Windows with WSL:
```bash
id -u  # USER_ID
id -g  # GROUP_ID
```

### 3. Build and Run with Docker

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

The application will be available at `http://localhost:8000`

### 4. API Endpoints

- `GET /api/` - API home page
- `POST /api/register` - Register a new customer
- `POST /api/check-eligibility` - Check loan eligibility
- `POST /api/create-loan` - Create a new loan
- `GET /api/view-loan/<loan_id>` - View loan details
- `GET /api/view-loans/<customer_id>` - View customer's loans
- `POST /api/upload-data` - Upload customer/loan data from Excel

## Development Setup (without Docker)

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up database
Configure your database in `.env` and run:
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 3. Run Redis (for Celery)
```bash
# Using Docker
docker run -d -p 6379:6379 redis:7-alpine

# Or install Redis locally
```

### 4. Run the application
```bash
# Terminal 1: Django server
python manage.py runserver

# Terminal 2: Celery worker
celery -A credit_approval worker --loglevel=info
```

## Data Ingestion

Upload customer and loan data using the `/api/upload-data` endpoint or run:

```bash
python manage.py ingest_data
```

This will process `customer_data.xlsx` and `loan_data.xlsx` in the background using Celery.

## Credit Score Calculation

The system calculates credit scores based on:
- Past loans paid on time (40% weight)
- Number of loans taken (20% weight)
- Loan activity in current year (20% weight)
- Loan approved volume (20% weight)

Additional checks:
- Current loans > approved limit → score = 0
- Current EMIs > 50% monthly salary → ineligible

## Troubleshooting

### Permission Issues
If you encounter permission errors, ensure `USER_ID` and `GROUP_ID` in `.env` match your host user:
```bash
echo "USER_ID=$(id -u)"
echo "GROUP_ID=$(id -g)"
```

### Database Connection Issues
- Verify `DATABASE_URL` is correct
- Ensure the database is accessible from your network
- Check firewall settings

### Redis Connection Issues
- Ensure Redis container is running: `docker ps | grep redis`
- Check Redis logs: `docker logs <redis-container-id>`

### Services Not Starting
Check service logs:
```bash
docker-compose logs web
docker-compose logs celery
docker-compose logs redis
```

## Project Structure

```
.
├── credit_approval/          # Django project settings
├── loans/                    # Main application
│   ├── models.py            # Database models
│   ├── views.py             # API endpoints
│   ├── serializers.py       # DRF serializers
│   ├── tasks.py             # Celery tasks
│   └── management/commands/ # Management commands
├── templates/               # HTML templates
├── static/                  # Static files
├── docker-compose.yml       # Docker orchestration
├── Dockerfile              # Container build
├── entrypoint.sh           # Container startup script
├── requirements.txt        # Python dependencies
└── .env                    # Environment variables
```

## API Documentation

### Register Customer
```http
POST /api/register
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe",
  "age": 30,
  "monthly_income": 50000,
  "phone_number": "1234567890"
}
```

### Check Eligibility
```http
POST /api/check-eligibility
Content-Type: application/json

{
  "customer_id": 1,
  "loan_amount": 100000,
  "interest_rate": 10,
  "tenure": 12
}
```

## License

This project is part of an internship assignment.