# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

SoulNear is a multi-component Telegram bot ecosystem with AI-powered assistants. The project uses a unified codebase architecture after a recent refactoring that consolidated duplicate test/production bots.

## Core Architecture

### Main Components

**soul_bot/** - Unified production/test Telegram bot with AI assistant features
- Environment-based configuration (prod/test via ENV variable)
- OpenAI GPT integration with specialized assistants
- Payment processing via YooKassa  
- Voice message processing
- User analysis (relationships, money, confidence, fears)
- Premium features and media content

**webapp_v2/** - React + TypeScript frontend (Telegram WebApp)
- Modern React 19 with TypeScript
- Vite build system
- Framer Motion animations
- State management with Zustand

**webapp_api/** - Python/Quart backend API 
- Shares database and OpenAI assistants with main bot
- Quart async framework
- RESTful endpoints for chat interactions

**Support Bots:**
- repair_bot/ - System administration and monitoring
- support_bot/ - User support ticket handling

## Development Commands

### Main Bot (soul_bot/)

```bash
# Setup environment
cd soul_bot
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Configure environment files
cp .env.example .env.prod
cp .env.example .env.test
# Edit .env.prod and .env.test with actual tokens

# Run production bot
ENV=prod python bot.py
# OR use script
./scripts/run_prod.sh

# Run test bot  
ENV=test python bot.py
# OR use script
./scripts/run_test.sh

# Run tests
./run_tests.sh
python test_refactoring.py

# Validate configuration
python -c "import config; print(f'{config.ENV} - {config.TEST} - {config.POSTGRES_DB}')"
```

### Frontend (webapp_v2/)

```bash
cd webapp_v2
npm install

# Development
npm run dev

# Build
npm run build

# Lint
npm run lint

# Preview production build
npm run preview
```

### API Server (webapp_api/)

```bash
cd webapp_api
pip install -r requirements.txt
python app.py
# Runs on port 8888
```

## Architecture Patterns

### Configuration Management
- **Environment-based config**: Uses `.env.{ENV}` files (prod/test)
- **Config validation**: Required variables raise errors if missing
- **Secure defaults**: No hardcoded tokens in source code

### Database Layer
- **SQLAlchemy + AsyncPG**: Async ORM with PostgreSQL
- **Shared database**: webapp_api reads/writes same DB as main bot  
- **Repository pattern**: Modular data access in `database/repository/`

### Bot Architecture  
- **aiogram 3.x**: Modern async Telegram bot framework
- **Handler separation**: Admin vs user handlers in separate modules
- **Middleware system**: Events processing and state management
- **FSM states**: Conversation flow management

### AI Integration
- **OpenAI Assistants API**: Specialized assistants for different analysis types
- **Thread management**: Persistent conversation contexts
- **Voice processing**: Audio message transcription and response

## Key Directories

```
soul_bot/
├── bot/
│   ├── handlers/         # Telegram message handlers
│   │   ├── admin/       # Admin-only commands  
│   │   └── user/        # User interactions
│   ├── functions/       # Business logic
│   ├── keyboards/       # Inline/reply keyboards
│   ├── states/          # FSM state definitions
│   └── middlewares/     # Request processing
├── database/
│   ├── models/          # SQLAlchemy models
│   └── repository/      # Data access layer
├── voice/               # Voice processing utilities
└── ready/               # Media assets
```

## Environment Configuration

### Required Environment Variables

**.env.prod** (Production):
```bash
ENV=prod
BOT_TOKEN=your_prod_bot_token
POSTGRES_DB=soul_bot
TEST=false
```

**.env.test** (Testing):  
```bash
ENV=test
BOT_TOKEN=your_test_bot_token
POSTGRES_DB=soul_test_bot
TEST=true
```

**Common variables** (both files):
```bash
OPENAI_API_KEY=your_openai_key
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_db_password
SECRET_KEY=yookassa_secret
SHOP_ID=yookassa_shop_id
```

## Development Workflow

### Bot Development
1. Make changes in `soul_bot/`
2. Test with: `ENV=test python bot.py` 
3. Verify with: `ENV=prod python bot.py` (carefully)
4. Run tests: `python test_refactoring.py`

### Database Changes
1. Update models in `database/models/`
2. Create migration script if needed
3. Test on test database first
4. Apply to production database

### Frontend Development  
1. Work in `webapp_v2/src/`
2. Use `npm run dev` for hot reloading
3. Run `npm run lint` before committing
4. Build with `npm run build` 

## Testing Strategy

- **Config validation**: `test_refactoring.py` verifies environment switching
- **Unit tests**: Located in `tests/` directory  
- **Integration tests**: Test bot startup and core flows
- **Environment isolation**: Test and prod databases are separate

## Important Notes

### Recent Refactoring
- **Unified codebase**: Eliminated duplicate soul_test_bot/ directory
- **Environment-based config**: Single codebase handles both prod/test
- **Legacy cleanup**: Old config files backed up but can be removed

### Security Practices
- **No tokens in code**: All secrets via environment variables
- **Gitignore protection**: .env.prod and .env.test excluded from git
- **Template files**: .env.example and .TEMPLATE files for setup guidance

### Database Considerations
- **Shared database**: webapp_api uses same PostgreSQL as main bot
- **Thread safety**: Uses connection pooling for concurrent access  
- **Backup strategy**: repair_bot handles automated backups every 3 hours