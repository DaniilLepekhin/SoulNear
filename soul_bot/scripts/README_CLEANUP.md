# 🧹 Database Cleanup Scripts

## Quick Start

```bash
# Go to scripts directory
cd soul_bot/scripts

# Clean everything (with confirmation)
ENV=test python cleanup_test_db.py --all

# Clean test users only (Алексей, Тест, etc.)
ENV=test python cleanup_test_db.py --test-users

# Clean specific user
ENV=test python cleanup_test_db.py --user-id 123456789

# Preview without deleting (dry run)
ENV=test python cleanup_test_db.py --all --dry-run
```

---

## Safety Features

✅ **Multiple safeguards:**
- Only works with `ENV=test`
- Checks database URL contains 'test'
- Requires explicit confirmation before deletion
- Shows statistics before/after cleanup
- Dry-run mode for previewing

❌ **Will NOT work on production:**
```bash
ENV=prod python cleanup_test_db.py --all
# ❌ UNSAFE: Current environment is 'prod' (not 'test')
# This script can ONLY run on test database!
```

---

## Usage Examples

### 1. Full Cleanup (for fresh test run)

```bash
ENV=test python cleanup_test_db.py --all
```

**Output:**
```
============================================================
                 🧹 Test Database Cleanup                  
============================================================

✅ Environment: test
ℹ️  Database: postgresql://user:pass@localhost:5432/soul_test...

ℹ️  Fetching current statistics...

Before Cleanup:
  👤 Users:          5
  🧠 Profiles:       5
  💬 Conversations:  127
  📝 Quizzes:        3

⚠️  This will DELETE ALL data from test database!
⚠️  Type 'DELETE ALL' to confirm: DELETE ALL

ℹ️  Deleting quiz sessions...
ℹ️  Deleting conversation history...
ℹ️  Deleting user profiles...
ℹ️  Deleting users...
✅ All data deleted successfully!

After Cleanup:
  👤 Users:          0
  🧠 Profiles:       0
  💬 Conversations:  0
  📝 Quizzes:        0

============================================================
                    ✨ Cleanup Complete                     
============================================================
```

---

### 2. Clean Test Users Only

```bash
ENV=test python cleanup_test_db.py --test-users
```

**Deletes users with names:**
- "Алексей"
- "Тест" / "Test"
- "testuser"
- Anything containing "test_"

**Output:**
```
ℹ️  Found 2 test users:
  - Алексей (ID: 123456789)
  - Тестовый Юзер (ID: 987654321)

⚠️  Delete these 2 test users? (yes/no): yes

ℹ️  Deleting: Алексей (ID: 123456789)...
ℹ️  Deleting: Тестовый Юзер (ID: 987654321)...
✅ Deleted 2 test users successfully!
```

---

### 3. Clean Specific User

```bash
ENV=test python cleanup_test_db.py --user-id 123456789
```

**Output:**
```
ℹ️  Found user: Алексей (ID: 123456789)

Related Data:
  🧠 Profile:        1
  💬 Conversations:  30
  📝 Quizzes:        1

⚠️  Delete this user and all related data? (yes/no): yes

ℹ️  Deleting quiz sessions...
ℹ️  Deleting conversation history...
ℹ️  Deleting user profile...
ℹ️  Deleting user...
✅ User 123456789 and all related data deleted successfully!
```

---

### 4. Dry Run (Preview)

```bash
ENV=test python cleanup_test_db.py --all --dry-run
```

**Output:**
```
⚠️  DRY RUN MODE - No data will be deleted

Before Cleanup:
  👤 Users:          5
  🧠 Profiles:       5
  💬 Conversations:  127
  📝 Quizzes:        3

ℹ️  Would delete all records from: quiz_sessions, conversation_history, user_profiles, users
```

---

## Use Cases

### For Level 2 Testing

```bash
# 1. Before test: Clean everything
cd soul_bot/scripts
ENV=test python cleanup_test_db.py --all

# 2. Run automated test (via agent)
cd ../..
node agent_test_runner.js LEVEL2_TEST_SCENARIO.json

# 3. After test: Check results, then cleanup
ENV=test python soul_bot/scripts/cleanup_test_db.py --test-users
```

### For Development

```bash
# Clean only your test account
ENV=test python cleanup_test_db.py --user-id YOUR_TELEGRAM_ID

# Preview what would be deleted
ENV=test python cleanup_test_db.py --all --dry-run
```

### Before Deployment

```bash
# Make sure test DB is clean
ENV=test python cleanup_test_db.py --all
```

---

## Script Options

| Option | Description | Example |
|--------|-------------|---------|
| `--all` | Delete ALL data | `--all` |
| `--user-id ID` | Delete specific user | `--user-id 123456789` |
| `--test-users` | Delete test users only | `--test-users` |
| `--dry-run` | Preview without deleting | `--all --dry-run` |

---

## Troubleshooting

### "UNSAFE: Current environment is 'prod'"

**Problem:** Script detected non-test environment

**Solution:**
```bash
# Set ENV explicitly
ENV=test python cleanup_test_db.py --all

# Or use .env.test
export ENV=test
python cleanup_test_db.py --all
```

---

### "Database URL doesn't contain 'test'"

**Problem:** Database URL looks suspicious

**Solution:**
- Check your `.env.test` file
- Verify `DATABASE_URL` contains 'test'
- Confirm with 'yes' if you're sure it's test DB

---

### No users found

```bash
ENV=test python cleanup_test_db.py --all
# ⚠️  Database is already empty!
```

**This is fine!** Database is already clean.

---

## Technical Details

### Deletion Order (respects foreign keys)

1. `quiz_sessions` (depends on users)
2. `conversation_history` (depends on users)
3. `user_profiles` (depends on users)
4. `users` (base table)

### Test User Detection

Pattern matching on `real_name` field:
- Contains "Алексей"
- Contains "Тест" or "Test"
- Contains "testuser"
- Starts with "test_"

Case-insensitive matching.

---

## Integration with Automated Tests

```python
# test_runner.py
import subprocess
import os

def setup_clean_database():
    """Clean test DB before test run"""
    result = subprocess.run(
        ['python', 'soul_bot/scripts/cleanup_test_db.py', '--all'],
        env={**os.environ, 'ENV': 'test'},
        input=b'DELETE ALL\n',  # Auto-confirm
        capture_output=True
    )
    
    if result.returncode != 0:
        raise Exception(f"Cleanup failed: {result.stderr.decode()}")
    
    print("✅ Test database cleaned")

# Usage
setup_clean_database()
run_level2_test()
```

---

**Готово! Безопасный cleanup для тестовой БД с защитой от продакшена.** 🧹

