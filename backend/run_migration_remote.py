"""
Remote migration runner for Railway PostgreSQL database.
This script can be executed on Railway to run the PostgreSQL migration.
"""

import asyncio
import logging
import os
from app.migrations.add_topic_tracking_fields import migrate_add_topic_tracking_fields

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Run the migration on Railway PostgreSQL."""
    print("🔄 Starting PostgreSQL migration on Railway...")

    # Check if we're in the right environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL environment variable not found!")
        return

    if "postgresql" not in database_url:
        print("❌ This script is for PostgreSQL only!")
        return

    print(f"📊 Database URL: {database_url[:50]}...")

    try:
        success = await migrate_add_topic_tracking_fields()
        if success:
            print("✅ Migration completed successfully on Railway!")
        else:
            print("❌ Migration failed!")

    except Exception as e:
        print(f"❌ Migration error: {e}")
        logger.error(f"Migration failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(main())