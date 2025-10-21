"""
SQLite-compatible database migration to add enhanced topic tracking fields to sessions table.

SQLite doesn't support 'ADD COLUMN IF NOT EXISTS', so we need to check column existence first.
"""

import asyncio
import logging
from sqlalchemy import text
from app.core.database import engine

logger = logging.getLogger(__name__)

async def check_column_exists(conn, table_name: str, column_name: str) -> bool:
    """Check if a column exists in SQLite table."""
    result = await conn.execute(text(f"PRAGMA table_info({table_name})"))
    columns = result.fetchall()
    return any(col[1] == column_name for col in columns)

async def migrate_add_topic_tracking_fields():
    """Add enhanced topic tracking fields to sessions table."""

    try:
        async with engine.begin() as conn:
            # Check which columns already exist
            existing_columns = []
            columns_to_add = [
                'topic_type', 'topic_source', 'pdf_noun_topic', 'pdf_sentence_topic',
                'pdf_summary_topic', 'pdf_original_content', 'manual_topic_content',
                'final_topic_content', 'topic_metadata'
            ]

            for column in columns_to_add:
                if await check_column_exists(conn, 'sessions', column):
                    existing_columns.append(column)
                    logger.info(f"Column {column} already exists, skipping...")

            # Add missing columns one by one
            for column in columns_to_add:
                if column not in existing_columns:
                    if column == 'topic_type':
                        sql = "ALTER TABLE sessions ADD COLUMN topic_type VARCHAR(20) DEFAULT 'manual'"
                    elif column == 'topic_source':
                        sql = "ALTER TABLE sessions ADD COLUMN topic_source VARCHAR(20) DEFAULT 'manual'"
                    elif column == 'pdf_noun_topic':
                        sql = "ALTER TABLE sessions ADD COLUMN pdf_noun_topic VARCHAR(500)"
                    elif column == 'pdf_sentence_topic':
                        sql = "ALTER TABLE sessions ADD COLUMN pdf_sentence_topic TEXT"
                    elif column == 'pdf_summary_topic':
                        sql = "ALTER TABLE sessions ADD COLUMN pdf_summary_topic TEXT"
                    elif column == 'pdf_original_content':
                        sql = "ALTER TABLE sessions ADD COLUMN pdf_original_content TEXT"
                    elif column == 'manual_topic_content':
                        sql = "ALTER TABLE sessions ADD COLUMN manual_topic_content TEXT"
                    elif column == 'final_topic_content':
                        sql = "ALTER TABLE sessions ADD COLUMN final_topic_content TEXT"
                    elif column == 'topic_metadata':
                        # SQLite uses JSON instead of JSONB
                        sql = "ALTER TABLE sessions ADD COLUMN topic_metadata JSON"

                    await conn.execute(text(sql))
                    logger.info(f"✅ Added column: {column}")

            # Create indexes (SQLite doesn't have IF NOT EXISTS for indexes, so we need to try/catch)
            try:
                await conn.execute(text("CREATE INDEX idx_sessions_topic_type ON sessions(topic_type)"))
                logger.info("✅ Created index: idx_sessions_topic_type")
            except Exception:
                logger.info("Index idx_sessions_topic_type already exists")

            try:
                await conn.execute(text("CREATE INDEX idx_sessions_topic_source ON sessions(topic_source)"))
                logger.info("✅ Created index: idx_sessions_topic_source")
            except Exception:
                logger.info("Index idx_sessions_topic_source already exists")

            # Update existing sessions to populate new fields
            if 'final_topic_content' not in existing_columns:
                await conn.execute(text("""
                    UPDATE sessions
                    SET
                        final_topic_content = topic,
                        topic_type = 'manual',
                        topic_source = 'manual'
                    WHERE final_topic_content IS NULL OR final_topic_content = ''
                """))

                await conn.execute(text("""
                    UPDATE sessions
                    SET final_topic_content = topic
                    WHERE final_topic_content IS NULL
                """))
                logger.info("✅ Updated existing sessions with topic data")

        logger.info("✅ Successfully added topic tracking fields to sessions table")
        return True

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

async def rollback_topic_tracking_fields():
    """Rollback the topic tracking fields migration."""

    # SQLite doesn't support DROP COLUMN, so we can't easily rollback
    # We would need to recreate the table without these columns
    logger.warning("SQLite doesn't support DROP COLUMN. Manual rollback required.")
    return False

if __name__ == "__main__":
    # Run the migration
    async def main():
        print("🔄 Running SQLite topic tracking fields migration...")
        success = await migrate_add_topic_tracking_fields()
        if success:
            print("✅ Migration completed successfully!")
        else:
            print("❌ Migration failed!")

    asyncio.run(main())