"""Database migration utilities."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import AsyncSessionLocal


async def _detect_database_type(session: AsyncSession) -> str:
    """Detect the database type (sqlite or postgresql)."""
    try:
        # Try PostgreSQL specific query
        await session.execute(text("SELECT version();"))
        return "postgresql"
    except:
        # If PostgreSQL query fails, assume SQLite
        return "sqlite"


async def drop_session_activities_table():
    """Drop the session_activities table if it exists."""
    async with AsyncSessionLocal() as session:
        try:
            db_type = await _detect_database_type(session)

            if db_type == "postgresql":
                # PostgreSQL: use information_schema
                check_query = text("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'session_activities';
                """)
            else:
                # SQLite: use sqlite_master
                check_query = text("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name='session_activities';
                """)

            result = await session.execute(check_query)
            table_exists = result.fetchone() is not None

            if table_exists:
                if db_type == "postgresql":
                    drop_query = text("DROP TABLE IF EXISTS session_activities CASCADE;")
                else:
                    drop_query = text("DROP TABLE IF EXISTS session_activities;")

                await session.execute(drop_query)
                await session.commit()
                print("✅ session_activities table dropped successfully")
            else:
                print("ℹ️ session_activities table does not exist")

        except Exception as e:
            await session.rollback()
            print(f"❌ Error dropping session_activities table: {e}")
            raise


async def add_deleted_at_column():
    """Add deleted_at column to sessions table if it doesn't exist."""
    async with AsyncSessionLocal() as session:
        try:
            db_type = await _detect_database_type(session)

            # First check if sessions table exists
            if db_type == "postgresql":
                table_check_query = text("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'sessions';
                """)
            else:
                table_check_query = text("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name='sessions';
                """)

            table_result = await session.execute(table_check_query)
            table_exists = table_result.fetchone() is not None

            if not table_exists:
                print("ℹ️ sessions table does not exist yet, skipping column addition")
                return

            # Check if column exists
            if db_type == "postgresql":
                check_query = text("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'sessions' AND column_name = 'deleted_at';
                """)
                result = await session.execute(check_query)
                column_exists = result.fetchone() is not None
            else:
                check_query = text("PRAGMA table_info(sessions);")
                result = await session.execute(check_query)
                columns = result.fetchall()
                column_exists = any(col[1] == 'deleted_at' for col in columns)

            if not column_exists:
                if db_type == "postgresql":
                    add_column_query = text("ALTER TABLE sessions ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE;")
                else:
                    add_column_query = text("ALTER TABLE sessions ADD COLUMN deleted_at DATETIME;")

                await session.execute(add_column_query)
                await session.commit()
                print("✅ deleted_at column added to sessions table")
            else:
                print("ℹ️ deleted_at column already exists in sessions table")

        except Exception as e:
            await session.rollback()
            print(f"❌ Error adding deleted_at column: {e}")
            raise


async def create_score_records_table():
    """Create the score_records table if it doesn't exist."""
    async with AsyncSessionLocal() as session:
        try:
            db_type = await _detect_database_type(session)

            if db_type == "postgresql":
                # PostgreSQL: use information_schema
                check_query = text("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'score_records';
                """)
            else:
                # SQLite: use sqlite_master
                check_query = text("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name='score_records';
                """)

            result = await session.execute(check_query)
            table_exists = result.fetchone() is not None

            if not table_exists:
                if db_type == "postgresql":
                    create_query = text("""
                        CREATE TABLE score_records (
                            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::varchar,
                            student_id VARCHAR(36) NOT NULL,
                            message_id VARCHAR(36) NOT NULL,
                            session_id VARCHAR(20) NOT NULL,
                            overall_score INTEGER NOT NULL,
                            depth_score INTEGER NOT NULL,
                            breadth_score INTEGER NOT NULL,
                            application_score INTEGER NOT NULL,
                            metacognition_score INTEGER NOT NULL,
                            engagement_score INTEGER NOT NULL,
                            is_completed BOOLEAN DEFAULT FALSE,
                            evaluation_data JSONB,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                            FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
                            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                        );

                        CREATE INDEX idx_score_records_student_id ON score_records(student_id);
                        CREATE INDEX idx_score_records_message_id ON score_records(message_id);
                        CREATE INDEX idx_score_records_session_id ON score_records(session_id);
                        CREATE INDEX idx_score_records_created_at ON score_records(created_at DESC);
                    """)
                else:
                    create_query = text("""
                        CREATE TABLE score_records (
                            id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                            student_id TEXT NOT NULL,
                            message_id TEXT NOT NULL,
                            session_id TEXT NOT NULL,
                            overall_score INTEGER NOT NULL,
                            depth_score INTEGER NOT NULL,
                            breadth_score INTEGER NOT NULL,
                            application_score INTEGER NOT NULL,
                            metacognition_score INTEGER NOT NULL,
                            engagement_score INTEGER NOT NULL,
                            is_completed BOOLEAN DEFAULT FALSE,
                            evaluation_data TEXT,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                            FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
                            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                        );

                        CREATE INDEX idx_score_records_student_id ON score_records(student_id);
                        CREATE INDEX idx_score_records_message_id ON score_records(message_id);
                        CREATE INDEX idx_score_records_session_id ON score_records(session_id);
                        CREATE INDEX idx_score_records_created_at ON score_records(created_at DESC);
                    """)

                await session.execute(create_query)
                await session.commit()
                print("✅ score_records table created successfully")
            else:
                print("ℹ️ score_records table already exists")

        except Exception as e:
            await session.rollback()
            print(f"❌ Error creating score_records table: {e}")
            raise


async def run_migrations():
    """Run all pending migrations."""
    print("🔄 Running database migrations...")
    await drop_session_activities_table()
    await add_deleted_at_column()
    await create_score_records_table()
    print("✅ Migrations completed")