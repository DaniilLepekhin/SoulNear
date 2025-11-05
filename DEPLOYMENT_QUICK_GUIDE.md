# Quick Deployment Guide

## TL;DR - Commands You Need

### Normal Deploy (Keeps Database)
```bash
./scripts/safe_redeploy.sh
```
This is what you'll use 99% of the time.

### Fresh Start (Wipes Database)
```bash
./scripts/safe_redeploy.sh --clean
```
⚠️ Requires confirmation. Deletes all data.

### Quick Restart
```bash
make restart-bot  # Just restart bot
make restart      # Restart everything
```

### Check Status
```bash
make ps           # Service status
make logs-bot     # Watch bot logs
make logs-db      # Watch database logs
make health       # Health check
```

### Backup & Restore
```bash
make backup       # Manual backup
make restore      # Restore latest backup
```

## What's Different Now

### ✅ Fixed Issues
1. **Automatic migrations** - SQL migrations run on startup
2. **Connection resilience** - Auto-retry on connection failures (3x)
3. **Health monitoring** - Background task checks database every 60s
4. **Better error handling** - No more crashes from connection drops
5. **Automatic backups** - Backup before every deploy

### 🎯 Success Indicators

After deploy, check logs (`make logs-bot`). You should see:
```
✅ Database connection successful!
✅ Database tables created/verified
✅ Applied X new migration(s) (or "All migrations up to date")
✅ Database health monitor started
```

If you see all 4, you're golden.

### ⚠️ Troubleshooting

**Bot crashed?**
```bash
make logs-bot  # Check for errors
make restart-bot  # Quick restart
```

**Database issues?**
```bash
make logs-db  # Check PostgreSQL logs
make health   # Run health check
./scripts/safe_redeploy.sh --clean  # Nuclear option
```

**Tables missing?**
- Should never happen now (auto-created on startup)
- If it does: `./scripts/safe_redeploy.sh --clean`

## Architecture Changes

### Before (Broken)
```
PostgreSQL crashes → Tables gone → Bot crashes
Connection timeout → Bot stops responding
Migrations never run → Manual SQL needed
```

### After (Fixed)
```
PostgreSQL crashes → Bot recreates tables automatically
Connection timeout → Auto-retry 3x → Success
Migrations run automatically on startup
Health monitor detects issues early
```

## Full Documentation

See `docs/DATABASE_RESILIENCE.md` for complete details.

## Common Workflows

### Deploy New Code
```bash
git pull  # Or: let safe_redeploy.sh do it
./scripts/safe_redeploy.sh
# Wait for ✅ messages
# Test bot in Telegram
```

### Check Everything is OK
```bash
make ps  # All services should be "Up" with "(healthy)"
make logs-bot | grep "✅"  # Should see success messages
```

### Something is Wrong
```bash
# 1. Check logs
make logs-bot
make logs-db

# 2. Try restart
make restart-bot

# 3. Still broken? Check documentation
cat docs/DATABASE_RESILIENCE.md

# 4. Nuclear option
./scripts/safe_redeploy.sh --clean
```

### Monitor in Production
```bash
# Watch logs in real-time
make logs-bot

# In another terminal, check resource usage
docker stats

# Check database is responding
make health
```

## File Changes Summary

| File | What Changed |
|------|--------------|
| `database/migration_runner.py` | NEW - Runs SQL migrations automatically |
| `database/resilience.py` | NEW - Retry logic & health monitoring |
| `database/repository/aiogram_state.py` | Added retry decorators |
| `database/database.py` | Better connection pool settings |
| `bot.py` | Runs migrations + starts health monitor |
| `docker/init-db.sh` | Better PostgreSQL config |
| `scripts/safe_redeploy.sh` | Auto backup + better checks |

## Environment Variables

In `.env.prod` (already configured, but for reference):
```bash
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secret_password
POSTGRES_DB=soul_bot
```

## Need Help?

1. Check `docs/DATABASE_RESILIENCE.md` for detailed troubleshooting
2. Check bot logs: `make logs-bot`
3. Check database logs: `make logs-db`
4. Try restart: `make restart-bot`
5. Try clean redeploy: `./scripts/safe_redeploy.sh --clean`

---

**Remember:** 
- Always use `./scripts/safe_redeploy.sh` for deployments (not `docker-compose up`)
- Backups are automatic, but you can make manual ones with `make backup`
- The bot now survives database crashes and connection issues
- If something is really broken, `--clean` will fix it (but loses data)

