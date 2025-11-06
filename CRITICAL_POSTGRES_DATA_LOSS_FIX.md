# 🚨 CRITICAL: PostgreSQL Data Loss Fix

## What Happened

Your bot ran for 14 hours, then crashed with `relation "aiogram_states" does not exist`.

**This means:** PostgreSQL lost all tables. Either:
1. PostgreSQL container crashed/restarted
2. Docker volume got unmounted/corrupted
3. Out of disk space
4. Memory issues causing PostgreSQL crash
5. Server restart

## Immediate Fix (Do This NOW)

```bash
# 1. Pull latest code (auto-recovery fix)
git pull origin dev

# 2. Redeploy (this will recreate tables)
./scripts/safe_redeploy.sh

# Bot should start working again
```

**New behavior:** Bot will now **automatically recreate tables** if they disappear during runtime.

## What I Just Fixed

### Before (Your Current Hell)
```
PostgreSQL crashes → Tables gone → Bot query fails → Bot dies forever
```

### After (From This Deploy)
```
PostgreSQL crashes → Tables gone → Bot detects missing table → Auto-recreates tables → Query succeeds ✅
```

**Changes:**
1. `@with_db_retry` now detects "table does not exist" errors
2. Automatically calls `create_tables()` when table is missing
3. Health monitor checks `aiogram_states` table exists every 60s
4. Health monitor recovery now recreates tables, not just connection

**Result:** Bot survives PostgreSQL crashes and data loss.

## Diagnose WHY This Happened

After deploying the fix, find out WHY PostgreSQL lost data:

### 1. Check PostgreSQL Logs

```bash
make logs-db | tail -200
```

**Look for:**
- `FATAL` or `PANIC` messages
- `server terminated`
- `database system was interrupted`
- `recovery` messages
- Out of memory errors
- Disk full errors

### 2. Check Docker Container Restarts

```bash
docker ps -a | grep postgres
```

**Look at "STATUS" column:**
- If it says "Up X hours" < 14 hours → Container restarted
- If "CREATED" is recent → Container was recreated

```bash
# Check restart count
docker inspect soulnear_postgres | grep RestartCount
```

### 3. Check Volume Status

```bash
# List volumes
docker volume ls | grep postgres

# Inspect volume
docker volume inspect soulnear_postgres_data
```

**Look for:**
- Volume exists? (should be there)
- Mountpoint path exists?

### 4. Check Disk Space

```bash
df -h
```

**Problem if:**
- `/var/lib/docker` partition is > 90% full
- Root partition is full

### 5. Check Memory

```bash
# Check if OOM killer killed PostgreSQL
dmesg | grep -i oom | tail -20

# Check current memory
free -h

# Check Docker memory limits
docker stats --no-stream
```

### 6. Check System Logs

```bash
# Recent system events
journalctl -xe | tail -100

# Docker daemon logs
journalctl -u docker | tail -50
```

## Common Causes & Solutions

### Cause 1: Out of Disk Space

**Symptoms:**
- `no space left on device` in logs
- `df -h` shows 100% usage

**Fix:**
```bash
# Clean old Docker images/containers
docker system prune -a --volumes
```

### Cause 2: Out of Memory (OOM Killer)

**Symptoms:**
- `OOM` in dmesg
- PostgreSQL suddenly stops

**Fix:**
```bash
# Add memory limit to docker-compose.yml
# Under postgres service:
deploy:
  resources:
    limits:
      memory: 512M
    reservations:
      memory: 256M
```

### Cause 3: Volume Corruption

**Symptoms:**
- PostgreSQL logs show corruption errors
- Recovery loops

**Fix:**
```bash
# Backup what you can
make backup

# Nuclear option: recreate volume
./scripts/safe_redeploy.sh --clean
```

### Cause 4: Server Reboot

**Symptoms:**
- System uptime < 14 hours
- Docker containers all recently restarted

**Check:**
```bash
uptime  # Shows how long server has been up
```

**If server rebooted:**
- Check if docker-compose is set to start on boot
- Check if volume persisted across reboot

### Cause 5: Docker Daemon Restart

**Symptoms:**
- All containers restarted at same time
- Docker service logs show restart

**Fix:**
- Ensure `restart: unless-stopped` in docker-compose.yml (already set)
- Investigate why Docker daemon restarted

## Monitoring Setup (Prevent Future Issues)

### 1. Enable PostgreSQL Query Logging

In `docker-compose.yml`, add under `postgres` service:

```yaml
environment:
  POSTGRES_INITDB_ARGS: "-c logging_collector=on -c log_directory=/var/log/postgresql"
volumes:
  - ./postgres_logs:/var/log/postgresql
```

### 2. Add Disk Space Monitoring

```bash
# Add to crontab (run hourly)
0 * * * * df -h | mail -s "Disk Space Report" your@email.com
```

### 3. Add Memory Monitoring

```bash
# Check memory hourly
0 * * * * free -h >> /var/log/memory_usage.log
```

### 4. External Uptime Monitoring

Use a service like:
- UptimeRobot (free, checks every 5min)
- Pingdom
- Better Uptime

Check: `https://your-bot-api.com/health` endpoint every 5min

## After Deploy: Verify Fix Works

### 1. Deploy the Fix

```bash
git pull origin dev
./scripts/safe_redeploy.sh
```

### 2. Verify Bot Started

```bash
make logs-bot | tail -50
```

**Should see:**
```
✅ Database connection successful!
✅ Database tables created/verified
✅ Applied X new migration(s)
✅ Database health monitor started
```

### 3. Test Bot Responds

Send message to bot → Should respond immediately

### 4. Monitor for 24 Hours

```bash
# Watch logs in real-time
make logs-bot

# Every few hours, check:
make ps  # All services "Up (healthy)"
make health  # Database responding
```

### 5. Look for Recovery Messages

If PostgreSQL crashes again, you should see:

```
🚨 CRITICAL: Table missing in get! PostgreSQL may have crashed/restarted. Attempting recovery...
✅ Tables recreated successfully, retrying operation...
```

This means auto-recovery is working! ✅

## Test the Auto-Recovery (Optional)

Want to verify it works? Simulate a crash:

```bash
# 1. In one terminal, watch bot logs
make logs-bot

# 2. In another terminal, kill PostgreSQL
docker exec soulnear_postgres psql -U postgres -c "DROP TABLE aiogram_states;"

# 3. Try to interact with bot

# You should see:
# 🚨 CRITICAL: Table missing...
# ✅ Tables recreated successfully...
# Bot continues working ✅
```

## Long-Term Prevention

### 1. Backups

Add automated daily backups:

```bash
# Add to crontab
0 2 * * * cd /path/to/SoulNear && make backup
```

### 2. Health Checks

The health monitor now runs every 60s and checks:
- Database connection
- `aiogram_states` table exists
- Auto-recovery if unhealthy for 2+ checks

### 3. Logging

Keep logs for at least 7 days:

```bash
# Rotate bot logs
docker logs soulnear_bot > /var/log/soulnear_bot.log 2>&1
logrotate /etc/logrotate.d/soulnear_bot
```

### 4. Alerting

Set up alerts for:
- Bot down > 5 minutes
- Database errors in logs
- Disk space > 80%
- Memory usage > 90%

## Summary

**What you MUST do now:**
1. ✅ Deploy the fix: `git pull && ./scripts/safe_redeploy.sh`
2. ✅ Diagnose root cause (check logs/disk/memory above)
3. ✅ Set up monitoring (at minimum: UptimeRobot)

**What the fix does:**
- Auto-recreates tables if they disappear
- Health monitor checks tables exist every 60s
- Bot survives PostgreSQL crashes

**What you should investigate:**
- WHY PostgreSQL lost data (check all diagnostic steps above)
- Fix root cause (disk space? memory? corruption?)

---

**The bot will no longer die from missing tables, but you still need to find out WHY tables are disappearing in the first place.**

Check those PostgreSQL logs and report what you find.

