"""
Database migration to add enhanced topic tracking fields to sessions table.

This migration adds fields to properly track the 4 different topic types:
1. PDF 명사형 주제 (pdf_noun_topic)
2. PDF 한 문장 주제 (pdf_sentence_topic)
3. PDF 요약 줄글 (pdf_summary_topic)
4. 교사 직접 입력 주제 (manual_topic_content)
"""

import asyncio
import logging
from sqlalchemy import text
from app.core.database import engine

logger = logging.getLogger(__name__)

async def migrate_add_topic_tracking_fields():
    """Add enhanced topic tracking fields to sessions table."""

    migration_sql = """
    -- Add new topic tracking fields to sessions table
    ALTER TABLE sessions
    ADD COLUMN IF NOT EXISTS topic_type VARCHAR(20) DEFAULT 'manual',
    ADD COLUMN IF NOT EXISTS topic_source VARCHAR(20) DEFAULT 'manual',
    ADD COLUMN IF NOT EXISTS pdf_noun_topic VARCHAR(500),
    ADD COLUMN IF NOT EXISTS pdf_sentence_topic TEXT,
    ADD COLUMN IF NOT EXISTS pdf_summary_topic TEXT,
    ADD COLUMN IF NOT EXISTS pdf_original_content TEXT,
    ADD COLUMN IF NOT EXISTS manual_topic_content TEXT,
    ADD COLUMN IF NOT EXISTS final_topic_content TEXT,
    ADD COLUMN IF NOT EXISTS topic_metadata JSONB;

    -- Create indexes for better query performance
    CREATE INDEX IF NOT EXISTS idx_sessions_topic_type ON sessions(topic_type);
    CREATE INDEX IF NOT EXISTS idx_sessions_topic_source ON sessions(topic_source);

    -- Update existing sessions to populate new fields
    -- Set final_topic_content to existing topic field for all existing sessions
    UPDATE sessions
    SET
        final_topic_content = topic,
        topic_type = 'manual',
        topic_source = 'manual'
    WHERE final_topic_content IS NULL OR final_topic_content = '';

    -- For any remaining NULL values, set to existing topic
    UPDATE sessions
    SET final_topic_content = topic
    WHERE final_topic_content IS NULL;
    """

    try:
        async with engine.begin() as conn:
            # Execute the migration
            await conn.execute(text(migration_sql))
            logger.info("✅ Successfully added topic tracking fields to sessions table")

        return True

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

async def rollback_topic_tracking_fields():
    """Rollback the topic tracking fields migration."""

    rollback_sql = """
    -- Remove the added columns
    ALTER TABLE sessions
    DROP COLUMN IF EXISTS topic_type,
    DROP COLUMN IF EXISTS topic_source,
    DROP COLUMN IF EXISTS pdf_noun_topic,
    DROP COLUMN IF EXISTS pdf_sentence_topic,
    DROP COLUMN IF EXISTS pdf_summary_topic,
    DROP COLUMN IF EXISTS pdf_original_content,
    DROP COLUMN IF EXISTS manual_topic_content,
    DROP COLUMN IF EXISTS final_topic_content,
    DROP COLUMN IF EXISTS topic_metadata;

    -- Drop the indexes
    DROP INDEX IF EXISTS idx_sessions_topic_type;
    DROP INDEX IF EXISTS idx_sessions_topic_source;
    """

    try:
        async with engine.begin() as conn:
            await conn.execute(text(rollback_sql))
            logger.info("✅ Successfully rolled back topic tracking fields")

        return True

    except Exception as e:
        logger.error(f"❌ Rollback failed: {e}")
        return False

if __name__ == "__main__":
    # Run the migration
    async def main():
        print("🔄 Running topic tracking fields migration...")
        success = await migrate_add_topic_tracking_fields()
        if success:
            print("✅ Migration completed successfully!")
        else:
            print("❌ Migration failed!")

    asyncio.run(main())