# Gym Management System API

A comprehensive REST API for managing gym operations, including user authentication, membership packages, and member management.

---

## Tech Stack

- **Framework**: FastAPI 0.115+
- **Server**: Uvicorn
- **Database**: PostgreSQL 16 with AsyncPG
- **ORM**: SQLAlchemy 2.0+
- **Async**: Python 3.10+ async/await
- **Authentication**: JWT with PyJWT and Passlib
- **Database Migrations**: Alembic
- **Configuration**: Pydantic Settings

---

## Environment Requirements

- **Python**: 3.10 or higher
- **PostgreSQL**: 16.x
- **Docker & Docker Compose**: (Optional, for containerized setup)

---

## Project Setup

### 1. Clone and Create Virtual Environment

```bash
# Navigate to project directory
cd python-engineer26_gym-management

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**Key packages installed:**
- `fastapi>=0.115.0` - Web framework
- `uvicorn[standard]>=0.30.0` - ASGI server
- `sqlalchemy>=2.0.0` - ORM
- `asyncpg>=0.30.0` - PostgreSQL async driver
- `alembic>=1.13.0` - Database migrations
- `pydantic>=2.7.0` - Data validation
- `python-jose[cryptography]>=3.3.0` - JWT tokens
- `passlib[argon2]>=1.7.4` - Password hashing

### 3. Environment Configuration

Create a `.env` file in the project root:

```env
# Application
APP_NAME=Gym Management API
APP_VERSION=0.1.0
DEBUG=true
API_V1_PREFIX=/api/v1

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:15433/gymdb

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

**Note**: Update `JWT_SECRET_KEY` and database credentials for production.

### 4. Database Setup

#### Using Docker (Recommended)

```bash
# Start PostgreSQL container
docker-compose up -d

# Verify the container is running
docker-compose ps
```

The database will be available at `localhost:15433` with:
- **User**: postgres
- **Password**: postgres
- **Database**: gymdb

#### Manual PostgreSQL Setup

If you have PostgreSQL installed locally:

```bash
# Create database
createdb -U postgres -p 5432 gymdb

# Update DATABASE_URL in .env if using different port/credentials
```

---

## Database Migrations with Alembic

### Initial Setup (Already Done)

Alembic has been configured to work with async SQLAlchemy and PostgreSQL.

**Configured Models:**
- `User` - Gym staff/admin users
- `Package` - Membership packages
- `Member` - Gym members

### Running Migrations

```bash
# Apply all pending migrations
python -m alembic upgrade head

# Check current database version
python -m alembic current

# View migration history
python -m alembic history
```

### Creating New Migrations

After modifying models in `app/models/`:

```bash
# Generate migration automatically
python -m alembic revision --autogenerate -m "Description of changes"

# Review the generated migration file in alembic/versions/
# Then apply it
python -m alembic upgrade head
```

### Rolling Back Migrations

```bash
# Downgrade to previous migration
python -m alembic downgrade -1

# Downgrade to specific revision
python -m alembic downgrade <revision_id>
```

---

## Running the Application

### Start Development Server

```bash
# Make sure virtual environment is activated
# and database is running

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: **http://localhost:8000**

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Testing the API

```bash
# Example: Get API info
curl http://localhost:8000/api/v1/health

# Check Swagger docs for all available endpoints
```

## Common Tasks

### Create a Migration

```bash
python -m alembic revision --autogenerate -m "Add new table"
```

### Reset Database (Development Only)

```bash
# WARNING: This deletes all data
python -m alembic downgrade base
python -m alembic upgrade head
```

### Stop Development Server

```bash
# Press Ctrl+C in the terminal
```

### Stop Docker Containers

```bash
docker-compose down
```

---

## Troubleshooting

### Port Already in Use

If port 8000 is already in use:
```bash
python -m uvicorn app.main:app --reload --port 8001
```

### Database Connection Error

- Ensure PostgreSQL container is running: `docker-compose ps`
- Check DATABASE_URL in `.env` matches your setup
- Verify credentials are correct

### Migration Issues

- Check Alembic configuration: `alembic current`
- Review migration files in `alembic/versions/`
- Ensure database is running before running migrations

---

## License

This project is part of Python Engineer training program.
