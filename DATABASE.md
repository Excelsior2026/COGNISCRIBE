# COGNISCRIBE Database & Redis Guide

## Architecture

Phase 3 implements:
- **PostgreSQL**: Persistent storage for users, jobs, audit logs, usage statistics
- **Redis**: Fast cache for task progress, real-time data, rate limiting

```
┌─────────────────────────────────────────┐
│         COGNISCRIBE API (FastAPI)       │
├─────────────────────────────────────────┤
│  Redis (Cache/Queue)  │  PostgreSQL     │
│  - Task progress      │  - Users        │
│  - Rate limits        │  - Jobs         │
│  - Sessions           │  - Audit logs   │
│  - Counters           │  - Statistics   │
└─────────────────────────────────────────┘
```

## Database Schema

### Users Table
```sql
- id (UUID, primary key)
- username (unique)
- email (unique)
- hashed_password
- is_active
- created_at
- updated_at
```

### TranscriptionJob Table
```sql
- id (UUID, primary key)
- user_id (foreign key)
- filename
- file_size_bytes
- status (pending/processing/completed/failed)
- transcript_text
- summary_text
- created_at
```

### AuditLog Table
```sql
- id (UUID, primary key)
- user_id
- action (login, upload, download, etc)
- status (success/failure)
- ip_address
- created_at (indexed)
```

### UsageStatistics Table
```sql
- id (UUID, primary key)
- user_id (unique per month)
- month (YYYY-MM)
- total_files_processed
- total_bytes_processed
- successful_jobs
- failed_jobs
```

## Setup Instructions

### Docker Compose (Recommended)

```bash
# Start all services
docker-compose -f docker-compose-phase3.yml up -d

# Initialize database
python scripts/init_db.py --all

# Check logs
docker-compose -f docker-compose-phase3.yml logs -f api
```

### Manual Setup

#### PostgreSQL

```bash
# Install PostgreSQL
brew install postgresql  # macOS
apt-get install postgresql  # Ubuntu

# Create database
createdb cogniscribe
createuser -P cogniscribe  # Set password to 'cogniscribe'

# Initialize schema
python scripts/init_db.py --init
```

#### Redis

```bash
# Install Redis
brew install redis  # macOS
apt-get install redis-server  # Ubuntu

# Start Redis
redis-server

# Test connection
redis-cli ping
```

## Environment Variables

```
DATABASE_URL=postgresql://cogniscribe:cogniscribe@localhost:5432/cogniscribe
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=your-secret-key
JWT_EXPIRE_HOURS=24
```

## Operations

### Initialize Database

```bash
# Create tables
python scripts/init_db.py --init

# Create tables + demo user
python scripts/init_db.py --all

# Drop all tables (WARNING)
python scripts/init_db.py --drop
```

### Query Examples

#### Get user's recent jobs

```python
from src.database.config import SessionLocal
from src.database.models import TranscriptionJob

db = SessionLocal()
jobs = db.query(TranscriptionJob)\
    .filter(TranscriptionJob.user_id == "user-001")\
    .order_by(TranscriptionJob.created_at.desc())\
    .limit(10)\
    .all()
```

#### Get audit logs

```python
from src.database.models import AuditLog

logs = db.query(AuditLog)\
    .filter(AuditLog.user_id == "user-001")\
    .filter(AuditLog.action == "login")\
    .order_by(AuditLog.created_at.desc())\
    .limit(100)\
    .all()
```

#### Get user statistics

```python
from src.database.models import UsageStatistics
from datetime import datetime

now = datetime.utcnow()
month = f"{now.year:04d}-{now.month:02d}"

stats = db.query(UsageStatistics)\
    .filter(UsageStatistics.user_id == "user-001")\
    .filter(UsageStatistics.month == month)\
    .first()
```

## Performance Optimization

### Indexing

Queries are indexed on:
- `users.username`
- `users.email`
- `transcription_jobs.user_id`
- `transcription_jobs.status`
- `transcription_jobs.created_at`
- `audit_logs.user_id`
- `audit_logs.action`
- `audit_logs.created_at`

### Connection Pooling

PostgreSQL uses QueuePool with:
- Pool size: 10
- Max overflow: 20
- Pre-ping: True (verify connections)

### Redis TTLs

- Tasks: 24 hours
- Cache: 1 hour (configurable)
- Rate limits: Per-window expiration
- Sessions: 24 hours

## Monitoring

### Database Health

```bash
# Connect to PostgreSQL
psql -U cogniscribe -d cogniscribe

# Check table sizes
SELECT tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables WHERE schemaname = 'public';

# Check connection count
SELECT count(*) FROM pg_stat_activity;
```

### Redis Health

```bash
# Connect to Redis
redis-cli

# Check memory
INFO memory

# Check key count
DBSIZE

# Check tasks
KEYS task:*
```

## Backup & Restore

### PostgreSQL Backup

```bash
# Full backup
pg_dump cogniscribe > cogniscribe_backup.sql

# Restore
psql cogniscribe < cogniscribe_backup.sql
```

### Redis Backup

```bash
# Redis saves periodically to dump.rdb
# Location: /var/lib/redis/ or configured

# Manual save
redis-cli BGSAVE
```

## Phase 4: Advanced Features

- [ ] Implement database migrations (Alembic)
- [ ] Add query performance monitoring
- [ ] Implement automatic backups
- [ ] Add read replicas for scaling
- [ ] Implement caching layers
- [ ] Add database-level encryption
