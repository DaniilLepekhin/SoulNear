"""
Automatic migration runner - executes SQL migrations on startup.
Tracks which migrations have been applied to avoid duplicates.
"""
import asyncio
import logging
from pathlib import Path
from typing import List

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)


class MigrationRunner:
    """Handles database migrations automatically on startup."""
    
    def __init__(self, engine: AsyncEngine, migrations_dir: str = "database/migrations"):
        self.engine = engine
        self.migrations_dir = Path(migrations_dir)
        
    async def init_migrations_table(self) -> None:
        """Create migrations tracking table if it doesn't exist."""
        async with self.engine.begin() as conn:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    migration_name VARCHAR(255) PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            logger.info("✅ Migrations tracking table ready")
    
    async def get_applied_migrations(self) -> List[str]:
        """Get list of already applied migrations."""
        async with self.engine.connect() as conn:
            result = await conn.execute(
                text("SELECT migration_name FROM schema_migrations ORDER BY migration_name")
            )
            return [row[0] for row in result]
    
    async def mark_migration_applied(self, migration_name: str) -> None:
        """Mark a migration as applied."""
        async with self.engine.begin() as conn:
            await conn.execute(
                text("INSERT INTO schema_migrations (migration_name) VALUES (:name)"),
                {"name": migration_name}
            )
    
    async def run_migration(self, migration_file: Path) -> None:
        """Execute a single migration file."""
        migration_name = migration_file.name
        
        logger.info(f"🔄 Running migration: {migration_name}")
        
        sql_content = migration_file.read_text(encoding='utf-8')
        
        # Split by semicolons but ignore those in comments or strings
        statements = []
        current_statement = []
        in_comment = False
        
        for line in sql_content.split('\n'):
            stripped = line.strip()
            
            # Skip comment-only lines
            if stripped.startswith('--'):
                continue
                
            current_statement.append(line)
            
            # Check if line ends with semicolon (simple heuristic)
            if ';' in line and not line.strip().startswith('--'):
                statements.append('\n'.join(current_statement))
                current_statement = []
        
        # Execute each statement
        async with self.engine.begin() as conn:
            for stmt in statements:
                stmt = stmt.strip()
                if stmt and not stmt.startswith('--'):
                    try:
                        await conn.execute(text(stmt))
                    except Exception as e:
                        # Log but don't fail on errors like "column already exists"
                        if "already exists" in str(e).lower():
                            logger.warning(f"⚠️  {e} (skipping)")
                        else:
                            raise
        
        await self.mark_migration_applied(migration_name)
        logger.info(f"✅ Migration applied: {migration_name}")
    
    async def run_pending_migrations(self) -> None:
        """Run all pending migrations in order."""
        if not self.migrations_dir.exists():
            logger.warning(f"⚠️  Migrations directory not found: {self.migrations_dir}")
            return
        
        # Get all .sql files sorted by name
        migration_files = sorted(self.migrations_dir.glob("*.sql"))
        
        if not migration_files:
            logger.info("ℹ️  No migration files found")
            return
        
        # Initialize tracking table
        await self.init_migrations_table()
        
        # Get already applied migrations
        applied = await self.get_applied_migrations()
        logger.info(f"📊 Applied migrations: {len(applied)}")
        
        # Run pending migrations
        pending_count = 0
        for migration_file in migration_files:
            if migration_file.name not in applied:
                await self.run_migration(migration_file)
                pending_count += 1
        
        if pending_count > 0:
            logger.info(f"✅ Applied {pending_count} new migration(s)")
        else:
            logger.info("✅ All migrations up to date")


async def run_migrations(engine: AsyncEngine) -> None:
    """
    Main entry point for running migrations.
    Call this after database is ready but before starting the bot.
    """
    runner = MigrationRunner(engine)
    await runner.run_pending_migrations()

