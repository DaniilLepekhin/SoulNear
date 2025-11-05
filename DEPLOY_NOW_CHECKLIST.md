# 🚀 Deploy Now - Step by Step Checklist

Follow these steps **exactly** to deploy the database fixes.

## Pre-Deploy Checklist

- [ ] You have SSH access to the server
- [ ] You're in the project directory
- [ ] You've read `DATABASE_FIX_SUMMARY.md` (or at least skimmed it)
- [ ] You understand this will fix the "relation does not exist" errors

## Deployment Steps

### Step 1: Backup Current State (Just in Case)

```bash
# If bot is running and accessible
make backup
```

**Expected output:** `✅ Backup created in backups/`

If this fails (bot not running), that's OK - continue anyway.

---

### Step 2: Pull Latest Code

```bash
git status  # Check you're on the right branch
git pull origin dev  # Or your main branch
```

**Expected:** You should see the new files downloading.

---

### Step 3: Verify New Files Exist

```bash
ls -la soul_bot/database/migration_runner.py
ls -la soul_bot/database/resilience.py
ls -la docs/DATABASE_RESILIENCE.md
```

**Expected:** All files should exist (not "No such file").

If files are missing, **STOP** - the code didn't pull correctly.

---

### Step 4: Deploy with Clean Database (First Time)

**⚠️ IMPORTANT:** This wipes the database. If you have important user data, skip this and do Step 5 instead.

```bash
./scripts/safe_redeploy.sh --clean
```

**Type:** `yes` when prompted

**Wait for:** ~60-90 seconds

**Expected output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔄 Safe Redeploy Starting
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
...
✅ PostgreSQL is ready!
...
✅ Bot appears to be running without errors
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Redeploy Complete!
```

**OR**

### Step 5: Deploy Preserving Database (If You Have User Data)

```bash
./scripts/safe_redeploy.sh
```

**No confirmation needed** - this is safe.

**Expected:** Same output as Step 4 but with backup message at start.

---

### Step 6: Verify Startup Success

```bash
make logs-bot | head -50
```

**Look for these 4 lines (MUST ALL BE PRESENT):**
```
✅ Database connection successful!
✅ Database tables created/verified
✅ Applied X new migration(s)  # X = 4 first time, 0 after that
✅ Database health monitor started
```

**If you see all 4:** ✅ Success! Continue to Step 7.

**If any are missing:** ❌ Something failed. Check troubleshooting below.

---

### Step 7: Verify Tables Exist

```bash
make shell-db
```

**In psql prompt, run:**
```sql
\dt
```

**Expected:** You should see a list of tables including:
- `aiogram_states` ← This one was missing before!
- `schema_migrations` ← This is new!
- `users`
- `user_profiles`
- etc.

**Type:** `\q` to exit psql

**If aiogram_states exists:** ✅ The main issue is fixed!

---

### Step 8: Verify Migrations Ran

```bash
make shell-db
```

**In psql prompt, run:**
```sql
SELECT * FROM schema_migrations;
```

**Expected:** 4 rows showing your migration files:
```
 migration_name              | applied_at
-----------------------------+------------------------
 001_add_moderate_fields.sql | 2025-11-05 12:34:56
 002_add_quiz_sessions.sql   | 2025-11-05 12:34:56
 003_remove_thread_ids.sql   | 2025-11-05 12:34:56
 004_cleanup_unused_fields...| 2025-11-05 12:34:56
```

**Type:** `\q` to exit

**If you see 4 migrations:** ✅ Migrations system working!

---

### Step 9: Test Bot Responds

**Open Telegram, send a message to your bot.**

**Expected:** Bot responds normally.

**If bot responds:** ✅ Everything works!

---

### Step 10: Monitor for 5 Minutes

```bash
make logs-bot
```

**Leave this running for 5 minutes.**

**Watch for:**
- Any errors (should be ZERO)
- Health check logs every 60s (optional, might not show in logs)
- Normal bot activity

**Press Ctrl+C to stop watching.**

---

## Success Criteria

✅ All checkmarks completed above
✅ Bot responds in Telegram
✅ No errors in logs for 5 minutes
✅ `aiogram_states` table exists

**If all checked:** 🎉 **You're done!** The fixes are deployed and working.

---

## Troubleshooting

### ❌ Problem: "Database tables created/verified" NOT in logs

**Fix:**
```bash
docker-compose down
docker-compose up -d postgres
sleep 10  # Wait for PostgreSQL
docker-compose up -d bot
make logs-bot
```

### ❌ Problem: Migrations show errors in logs

**Check migration syntax:**
```bash
cat soul_bot/database/migrations/001_add_moderate_fields.sql
```

**If SQL looks broken, restore backup:**
```bash
make restore  # Only if you made a backup in Step 1
```

### ❌ Problem: Bot won't start (keeps restarting)

**Check for missing environment variables:**
```bash
docker exec soulnear_bot env | grep POSTGRES
```

**Should see:**
```
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=...
POSTGRES_DB=soul_bot
```

**If any missing, check `.env.prod` exists and is correct.**

### ❌ Problem: Can't connect to database

**Check PostgreSQL is running:**
```bash
make ps
```

**Should see:**
```
soulnear_postgres  Up (healthy)  5432/tcp
```

**If not healthy:**
```bash
make logs-db  # Check what's wrong
```

### ❌ Problem: Old error still happens

**Nuclear option (wipes everything, fresh start):**
```bash
docker-compose down -v  # WIPES DATABASE
docker volume rm soulnear_postgres_data
./scripts/safe_redeploy.sh --clean
```

---

## Post-Deploy Monitoring (Next 24 Hours)

### Check Once Per Hour

```bash
make ps  # All should be "Up (healthy)"
```

### Watch Logs Occasionally

```bash
make logs-bot | tail -20  # Last 20 lines
```

### If You See Errors

```bash
# Full logs
make logs-bot > bot_errors.log

# Check for patterns
grep -i error bot_errors.log
grep -i "does not exist" bot_errors.log
```

**If errors continue after 24h:** Something else is wrong, not the database.

---

## Rollback (If Everything Breaks)

**Only if deploy completely fails and bot is unusable:**

```bash
# 1. Stop everything
docker-compose down

# 2. Revert code
git log --oneline -5  # Find commit before changes
git checkout <commit-hash>  # Replace with actual hash

# 3. Restore database backup
make restore  # Only if you made backup in Step 1

# 4. Restart old version
docker-compose up -d --build

# 5. Report what went wrong
make logs-bot > failed_deploy.log
```

**Then send `failed_deploy.log` for analysis.**

---

## What to Tell Users (If Needed)

> "Bot will be down for ~2 minutes for maintenance. This fixes stability issues."

That's it. Don't overcomplicate.

---

## Done!

After completing this checklist, your bot should:
- ✅ Never crash from "relation does not exist" errors
- ✅ Survive PostgreSQL crashes
- ✅ Auto-retry connection failures
- ✅ Run migrations automatically
- ✅ Monitor its own health

**Keep this file for future reference.** Next deploy will just be:
```bash
./scripts/safe_redeploy.sh
```

That's it.

---

## Quick Command Reference

```bash
# Deploy
./scripts/safe_redeploy.sh

# Check status
make ps

# Watch logs
make logs-bot

# Backup
make backup

# Restart
make restart-bot

# Emergency stop
docker-compose down

# Emergency fresh start
./scripts/safe_redeploy.sh --clean
```

**Print this checklist or keep it open during deploy.** Good luck! 🚀

