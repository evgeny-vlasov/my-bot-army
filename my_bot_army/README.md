# My Bot Army - FastAPI Backend

Multi-bot AI assistant platform for small businesses.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

3. Ensure PostgreSQL is running and create database:
   ```bash
   createdb mybotarmy
   ```

4. Run the application:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. Access the API:
   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc
   - Health check: http://localhost:8000/health

## Development

The application uses:
- FastAPI for the web framework
- PostgreSQL with asyncpg for database
- pgvector for vector similarity search
- SQLAlchemy 2.0 with async support
