# 🚀 Deployment Instructions — Critical Fixes

## ⚡ Quick Deploy (Recommended)

```bash
# На сервере
cd ~/SoulNear
git pull
make redeploy
```

Готово! 🎉

---

## 📋 Step-by-Step Deploy

Если хочешь контроль:

```bash
# 1. Backup current state (опционально)
docker-compose logs bot > logs_backup_$(date +%Y%m%d_%H%M%S).txt

# 2. Pull code
git pull

# 3. Clean everything (ВАЖНО: удалит volumes)
make clean-force ENV=prod

# 4. Rebuild with fixes
make rebuild ENV=prod

# 5. Monitor
make logs-bot
```

---

## ✅ Post-Deploy Verification

### 1. Check Logs (должны быть чистыми)
```bash
make logs-bot
```

**Ищем:**
- ✅ `Run polling for bot` — бот запустился
- ✅ `Загружен конфиг: .env.prod` — правильный конфиг
- ❌ НЕТ `AttributeError`
- ❌ НЕТ `InterfaceError`
- ❌ НЕТ `InvalidCatalogNameError`

### 2. Check Database
```bash
docker exec -it soulnear_postgres psql -U nikitagorokhov -l
```
Должна быть база `soul_bot` в списке.

### 3. Test Bot
1. Отправь `/start` боту
2. Отправь любое сообщение
3. Проверь, что нет краша в логах

---

## 🐛 If Something Goes Wrong

### "Connection refused"
```bash
docker-compose ps  # Check if containers running
make rebuild ENV=prod
```

### "Database doesn't exist"
```bash
# Manually create DB
docker exec -it soulnear_postgres psql -U nikitagorokhov -c "CREATE DATABASE soul_bot;"
docker-compose restart bot
```

### "Still seeing errors"
```bash
# Full nuclear option
docker system prune -a --volumes -f
make rebuild ENV=prod
```

---

## 📊 What Changed?

### Code Changes (9 files)
- ✅ Added None checks (10 locations)
- ✅ Configured connection pool
- ✅ Added DB auto-init script

### Infrastructure Changes
- ✅ New `docker/init-db.sh` — auto-creates DB
- ✅ Updated `docker-compose.yml` — mounts init script

**No breaking changes. No migrations needed.**

---

## 🎯 Success Criteria

После деплоя должно быть:
- [x] Бот запущен (logs показывают "Run polling")
- [x] База данных создана автоматически
- [x] Нет ошибок в логах
- [x] `/start` работает
- [x] Сообщения обрабатываются

---

## 💡 Pro Tips

**Monitor logs real-time:**
```bash
make logs-bot | grep -i error
```

**Check connection count:**
```bash
docker exec -it soulnear_postgres psql -U nikitagorokhov -d soul_bot -c "SELECT count(*) FROM pg_stat_activity;"
```

**Restart just bot (не трогая DB):**
```bash
docker-compose restart bot
```

---

## 📞 Support Commands

```bash
make logs-bot       # Bot logs
make logs-db        # Database logs
make shell-bot      # Enter bot container
make shell-db       # Enter DB container
docker ps           # List containers
docker-compose ps   # List compose services
```

---

**Deployment Time:** ~2-3 minutes  
**Downtime:** ~30 seconds  
**Risk Level:** 🟢 Low (defensive changes only)  
**Rollback Time:** <1 minute

**Ready?** → `make redeploy` 🚀

