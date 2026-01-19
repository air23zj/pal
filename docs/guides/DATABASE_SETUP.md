# Database Setup Guide

## Quick Start

The easiest way to get the database running is with Docker:

```bash
# Start database
docker-compose up -d postgres redis

# Initialize database (create tables)
make db-init

# Or manually:
cd backend
python scripts/init_db.py
```

## Database Schema

Morning Brief uses PostgreSQL with the following tables:

### Core Tables

**users**
- User profiles and settings
- Timezone preferences
- Last brief timestamp tracking

**brief_bundles**
- Stored brief JSON bundles
- Indexed by user_id and date

**brief_runs**
- Brief generation run tracking
- Status and performance metrics

**items**
- Content items (emails, posts, papers, etc.)
- Deduplicated by stable hash
- Indexed for fast lookups

**item_states**
- User-specific item state (seen, saved, ignored)
- Feedback scores
- Open counts

**feedback_events**
- User interaction events
- Used for personalization learning

## Database Migrations with Alembic

### Create a Migration

After modifying models in `backend/packages/database/models.py`:

```bash
# Using make
make db-migrate

# Or directly
cd backend
alembic revision --autogenerate -m "add new column to users"
```

### Apply Migrations

```bash
# Using make
make db-upgrade

# Or directly
cd backend
alembic upgrade head
```

### Rollback Migration

```bash
# Using make
make db-downgrade

# Or directly
cd backend
alembic downgrade -1
```

### View Migration History

```bash
cd backend
alembic history
alembic current
```

## Local Development (Without Docker)

### Install PostgreSQL

```bash
# macOS
brew install postgresql@16
brew services start postgresql@16

# Ubuntu/Debian
sudo apt install postgresql-16
sudo systemctl start postgresql
```

### Create Database

```bash
# Connect as postgres user
psql postgres

# Create user and database
CREATE USER morning_brief WITH PASSWORD 'dev_password';
CREATE DATABASE morning_brief OWNER morning_brief;
\q
```

### Set Environment Variable

```bash
export DATABASE_URL="postgresql://morning_brief:dev_password@localhost:5432/morning_brief"
```

### Initialize

```bash
cd backend
python scripts/init_db.py
```

## Database Management

### Connect to Database

```bash
# Via Docker
make db-shell

# Or directly
docker-compose exec postgres psql -U morning_brief -d morning_brief

# Local
psql postgresql://morning_brief:dev_password@localhost:5432/morning_brief
```

### Useful SQL Queries

```sql
-- View all users
SELECT id, timezone, created_at, last_brief_timestamp_utc FROM users;

-- View recent briefs
SELECT id, user_id, brief_date_local, generated_at_utc 
FROM brief_bundles 
ORDER BY generated_at_utc DESC 
LIMIT 10;

-- View feedback events
SELECT user_id, item_id, event_type, created_at_utc 
FROM feedback_events 
ORDER BY created_at_utc DESC 
LIMIT 20;

-- Count items by source
SELECT source, COUNT(*) 
FROM items 
GROUP BY source;

-- View item states
SELECT state, COUNT(*) 
FROM item_states 
GROUP BY state;
```

### Backup and Restore

```bash
# Backup
docker-compose exec postgres pg_dump -U morning_brief morning_brief > backup.sql

# Restore
cat backup.sql | docker-compose exec -T postgres psql -U morning_brief morning_brief
```

### Reset Database (Clean Slate)

```bash
# WARNING: This deletes all data!
make reset-db

# Then reinitialize
make db-init
```

## Troubleshooting

### Connection refused

```bash
# Check if postgres is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Restart
docker-compose restart postgres
```

### Migration conflicts

```bash
# View current version
cd backend
alembic current

# View history
alembic history

# Force to specific version (careful!)
alembic stamp head
```

### Database locked / stale connections

```sql
-- View active connections
SELECT * FROM pg_stat_activity WHERE datname = 'morning_brief';

-- Terminate connections (PostgreSQL 9.2+)
SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
WHERE datname = 'morning_brief' AND pid <> pg_backend_pid();
```

## Performance Tips

### Indexing

Key indexes are already created on:
- `user_id` columns (for filtering by user)
- `timestamp_utc` columns (for time-based queries)
- `brief_date_local` (for date range queries)
- `source` and `type` (for filtering items)

### Query Optimization

```sql
-- Use EXPLAIN ANALYZE to check query performance
EXPLAIN ANALYZE SELECT * FROM items WHERE user_id = 'u_dev';

-- Add indexes if needed
CREATE INDEX idx_items_entity_keys ON items USING GIN (entity_keys_json);
```

## Production Considerations

1. **Use managed PostgreSQL** (AWS RDS, Google Cloud SQL, Supabase)
2. **Enable connection pooling** (PgBouncer)
3. **Regular backups** (automated daily)
4. **Monitoring** (pg_stat_statements, slow query log)
5. **Read replicas** for scaling reads
6. **Partitioning** for large tables (future)

## Schema Version

Current schema version: `1.0`  
Alembic migration: `initial`

See `backend/migrations/versions/` for migration history.
