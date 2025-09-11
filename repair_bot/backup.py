from config import POSTGRES_PASS
from functions import send_file_to_admins,execute


async def backup_bd():
    execute(f'PGPASSWORD={POSTGRES_PASS} pg_dumpall -U postgres -h localhost --exclude-database postgres -f postgres.sql')

    await send_file_to_admins('postgres.sql')
