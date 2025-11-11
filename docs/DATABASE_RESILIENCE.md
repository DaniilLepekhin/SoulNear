# Database Resilience & Deployment Guide

## Overview

Your bot was crashing due to PostgreSQL connection issues and missing tables. This document explains the fixes and how to deploy safely.

## What Was Fixed

### 1. **Automatic Migrations** 
Previously: SQL migration files existed but were never executed
Now: Migrations run automatically on bot startup and are tracked

**How it works:**
- New `migration_runner.py` executes `.sql` files from `database/migrations/`
- Tracks applied migrations in `schema_migrations` table
- Runs on every bot startup (idempotent - safe to run multiple times)

### 2. **Connection Resilience**
Previously: One connection drop = dead bot
Now: Automatic retries with exponential backoff

**Features:**
- `@with_db_retry` decorator on all database operations
- Retries up to 3 times with smart backoff (0.5s, 1s, 2s)
- Only retries connection errors, not data errors
- All critical operations (aiogram_state, etc.) now use retry logic

### 3. **Health Monitoring**
New: Background task monitors database health every 60s
- Detects connection issues before they cause crashes
- Automatic recovery attempts when database becomes unhealthy
- Logs all health checks for debugging

### 4. **Better Connection Pool Settings**
- Connection timeouts: 10s connect, 30s command execution
- Pool pre-ping: Tests connections before using them
- TCP keepalives: Detects dead connections faster
- Connection recycling: Prevents stale connections

### 5. **Improved Init Script**
`docker/init-db.sh` now:
- Sets PostgreSQL connection limits (200 max connections)
- Configures TCP keepalives for stability
- Sets reasonable timeouts
- Better logging for debugging

### 6. **Safer Deployment Script**
`scripts/safe_redeploy.sh` improvements:
- Automatic database backup before redeployment
- Waits for PostgreSQL health check before declaring success
- Checks bot logs for errors after startup
- Confirmation prompt for `--clean` mode

## How Database Initialization Works

### Fresh Start (Clean Deploy)

```
1. PostgreSQL container starts
   └─> docker/init-db.sh runs (ONLY on first start)
       └─> Creates database 'soul_bot'
       └─> Configures PostgreSQL settings

2. Bot container starts
   └─> wait_for_db() - waits up to 30s for PostgreSQL
   └─> create_tables() - creates all tables via SQLAlchemy
   └─> run_migrations() - runs any pending SQL migrations
   └─> health monitor starts - monitors database every 60s
   └─> Bot starts polling
```

### Regular Restart (Database Preserved)

```
1. PostgreSQL container starts with existing volume
   └─> init-db.sh does NOT run (volume not empty)
   └─> Tables and data preserved

2. Bot container starts
   └─> wait_for_db() - connects to existing database
   └─> create_tables() - verifies tables exist (doesn't recreate)
   └─> run_migrations() - runs ONLY new migrations (tracked)
   └─> health monitor starts
   └─> Bot starts polling
```

## Deployment Scenarios

### Scenario 1: Safe Redeploy (Keep Database)

```bash
./scripts/safe_redeploy.sh
```

**What happens:**
- ✅ Backs up database automatically
- ✅ Stops containers gracefully
- ✅ Rebuilds code
- ✅ Starts containers
- ✅ Database and user data preserved
- ✅ Migrations run automatically

**Use when:**
- Deploying code changes
- Updating dependencies
- Regular updates

### Scenario 2: Clean Deploy (Fresh Database)

```bash
./scripts/safe_redeploy.sh --clean
```

**What happens:**
- ⚠️  Requires confirmation
- 🗑️  Deletes database volume
- 🆕 Creates fresh database
- ✅ Runs all migrations from scratch

**Use when:**
- Testing fresh install
- Database is corrupted beyond repair
- Starting from scratch

### Scenario 3: Quick Restart (No Rebuild)

```bash
make restart-bot
```

**What happens:**
- ♻️  Restarts bot container only
- ✅ Database untouched
- ✅ Fast (no rebuild)

**Use when:**
- Bot crashed but database is fine
- Testing configuration changes
- Quick recovery

## Incident Response Playbook

When the bot fails with `relation "aiogram_states" does not exist` or similar missing-table errors:

1. **Redeploy with recovery-aware scripts**
   ```bash
   git pull origin dev
   ./scripts/safe_redeploy.sh
   ```
   The redeploy script recreates missing tables, runs migrations, and starts the health monitor.
2. **Confirm startup messages**
   ```bash
   make logs-bot | head -50
   ```
   Ensure all four success markers appear:
   - `✅ Database connection successful!`
   - `✅ Database tables created/verified`
   - `✅ Applied X new migration(s)` (or `All migrations up to date`)
   - `✅ Database health monitor started`
3. **Smoke-test the bot** in Telegram. If responses are back and logs stay clean, recovery succeeded.

## Diagnostics Checklist (Run After Recovery)

Once the bot is back online, investigate the root cause so the failure does not repeat:

| Area | Commands | What to look for |
|------|----------|------------------|
| PostgreSQL logs | `make logs-db \| tail -200` | `FATAL`, `PANIC`, `no space left on device`, `recovery` loops |
| Container stability | `docker ps -a \| grep postgres`<br>`docker inspect soulnear_postgres \| grep RestartCount` | Unexpected restarts or high restart count |
| Volume health | `docker volume ls \| grep postgres`<br>`docker volume inspect soulnear_postgres_data` | Missing volume or invalid mountpoint |
| Disk space | `df -h` | `/var/lib/docker` or root partition &gt; 90% |
| Memory pressure | `dmesg \| grep -i oom \| tail -20`<br>`free -h`<br>`docker stats --no-stream` | OOM killer events or exhausted memory |
| System events | `journalctl -xe \| tail -100`<br>`journalctl -u docker \| tail -50` | Host or Docker daemon restarts |

If any category shows anomalies, resolve them (cleanup disk, adjust memory limits, recreate corrupted volume, etc.) and document the fix.

## Monitoring & Debugging

### Check if services are running

```bash
make ps
# or
docker-compose ps
```

### Watch bot logs

```bash
make logs-bot
```

Look for these success messages:
```
✅ Database connection successful!
✅ Database tables created/verified
✅ Applied X new migration(s)
✅ Database health monitor started
```

### Watch database logs

```bash
make logs-db
```

### Check database health

```bash
make health
```

### Connect to database directly

```bash
make shell-db
# Then run SQL:
\dt  # List tables
SELECT * FROM schema_migrations;  # Check applied migrations
SELECT * FROM aiogram_states;  # Check bot state
```

## Troubleshooting

### Error: "relation 'aiogram_states' does not exist"

**Old problem - should be fixed now!**

If you still see this:
1. Check bot logs: `make logs-bot`
2. Look for "✅ Database tables created/verified"
3. If missing, bot failed to initialize
4. Check database logs: `make logs-db`
5. Try clean redeploy: `./scripts/safe_redeploy.sh --clean`

### Error: "connection refused" / "connection timeout"

**Now handled automatically with retries**

If bot still crashes:
1. Check PostgreSQL is running: `make ps`
2. Check database health: `make health`
3. Check database logs: `make logs-db`
4. Restart PostgreSQL: `make restart`

### Bot keeps restarting

1. Check for errors: `make logs-bot`
2. Check database: `make logs-db`
3. Check disk space: `df -h`
4. Check memory: `docker stats`

### Database is slow

1. Check connection pool: Look for "pool timeout" in logs
2. Check disk I/O: `docker stats`
3. Increase pool size in `database/database.py` if needed
4. Check for long-running queries in PostgreSQL logs

### Healthcheck regression (November 2025)

**Symptom:** PostgreSQL logs spammed `FATAL: role "root" does not exist`, healthcheck reported `unhealthy`, and the database restarted every few hours.

**Root cause:** The Docker healthcheck used `pg_isready -d soul_bot` without specifying `-U postgres`, so Docker probed as `root` every 10 seconds and exhausted PostgreSQL.

**Fix (already merged):**

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U postgres -d soul_bot"]
```

**Verify after deploying the fix:**

1. `make logs-db` — ensure the `FATAL: role "root" does not exist` messages disappear.
2. `docker ps | grep postgres` — status should read `Up … (healthy)`.
3. Monitor for 24 hours: `make logs-bot | grep -i "database.*does not exist"` should stay empty.

## Advanced: Manual Migration

If you need to run a migration manually:

```python
# Connect to database
make shell-db

# Inside psql:
\i /path/to/migration.sql
```

Or via bot container:
```bash
docker exec -it soulnear_bot python -c "
import asyncio
from database.database import db
from database.migration_runner import run_migrations
asyncio.run(run_migrations(db.engine))
"
```

## Health Monitor Details

The health monitor runs in background and:
- Checks database every 60s with `SELECT 1`
- Logs warnings if check fails
- After 2 consecutive failures, attempts recovery
- Recovery = `db.ensure_ready()` which can recreate connections

To adjust monitoring:
```python
# In bot.py, line ~60
health_monitor = DatabaseHealthMonitor(db, check_interval=30)  # Check every 30s
```

## Connection Pool Tuning

Current settings in `database/database.py`:
```python
pool_size=20          # 20 connections in pool
max_overflow=10       # +10 overflow = 30 total max
pool_recycle=3600     # Recycle after 1 hour
pool_timeout=30       # Wait 30s for connection
pool_pre_ping=True    # Test before use
```

Adjust if needed:
- **High traffic bot**: Increase `pool_size`
- **Many connection errors**: Decrease `pool_recycle`
- **Slow queries**: Increase `command_timeout` in query args

## Backup & Recovery

### Automatic Backups

Backups are created automatically during redeploy:
```bash
./scripts/safe_redeploy.sh  # Creates backup before deploy
```

Stored in: `backups/backup_YYYYMMDD_HHMMSS.sql`

### Manual Backup

```bash
make backup
```

### Restore from Backup

```bash
make restore  # Restores latest backup
```

Or specific backup:
```bash
docker exec -i soulnear_postgres psql -U postgres soul_bot < backups/backup_20251105_120000.sql
```

## Configuration

All database settings in `.env.prod`:
```bash
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=soul_bot
```

**Important:** Never commit `.env.prod` to git!

## Summary of Changes Made

| File | Change |
|------|--------|
| `database/migration_runner.py` | ✨ NEW - Automatic migration execution |
| `database/resilience.py` | ✨ NEW - Connection retry logic & health monitoring |
| `database/repository/aiogram_state.py` | ✅ Added `@with_db_retry` decorators |
| `database/database.py` | ✅ Improved connection pool settings |
| `bot.py` | ✅ Added migration runner & health monitor |
| `docker/init-db.sh` | ✅ Better PostgreSQL configuration |
| `scripts/safe_redeploy.sh` | ✅ Automatic backups & better error checking |

## Next Steps

1. **Deploy the changes:**
   ```bash
   ./scripts/safe_redeploy.sh
   ```

2. **Verify everything works:**
   ```bash
   make logs-bot  # Should see ✅ messages
   ```

3. **Monitor for a day** to ensure stability

4. **Optional: Add more monitoring**
   - Set up external monitoring (UptimeRobot, etc.)
   - Add Prometheus metrics (future enhancement)
   - Set up alerts for crashes

## Why This Fixes Your Problem

**Before:**
- PostgreSQL crash → Tables lost → Bot crashes on next request
- Connection timeout → No retry → Bot stops responding
- Migrations never run → Manual SQL execution required
- No health monitoring → Problems discovered too late

**After:**
- PostgreSQL crash → Bot recreates tables automatically
- Connection timeout → Automatic retry (3x) → Request succeeds
- Migrations run automatically → Always up to date
- Health monitor → Problems detected early, automatic recovery

**Result:** Bot should be nearly bulletproof against database issues.

## Long-Term Monitoring Recommendations

- Enable PostgreSQL query logging via `POSTGRES_INITDB_ARGS` and ship logs to `./postgres_logs`.
- Add hourly disk and memory snapshots with cron (`df -h`, `free -h`) so spikes are spotted early.
- Configure external uptime monitoring (UptimeRobot, Better Uptime) against `/health`.
- Rotate logs (`logrotate`) so recovery history stays available for at least a week.
- Schedule daily backups: `0 2 * * * cd /path/to/SoulNear && make backup`.

