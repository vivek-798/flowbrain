import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, make_transient

# Ensure the backend directory is in the python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.models.user import User
from app.models.integration import Integration
from app.models.briefing import Briefing
from app.models.project import Project
from app.models.email import Email
from app.models.calendar_event import CalendarEvent
from app.models.business_context import BusinessContext

def run_migration():
    print("--- Starting Model-Aware Migration ---")
    
    # 1. Initialize DB connections
    sqlite_engine = create_engine("sqlite:///flowbrain.db")
    SqliteSession = sessionmaker(bind=sqlite_engine)
    sqlite_session = SqliteSession()

    if not settings.DIRECT_URL:
        print("Error: DIRECT_URL connection string is missing from backend/.env!")
        sys.exit(1)

    # Escape percent sign for SQLAlchemy connection engine if not already done
    pg_url = settings.DIRECT_URL
    pg_engine = create_engine(pg_url)
    PgSession = sessionmaker(bind=pg_engine)
    pg_session = PgSession()

    MODELS_IN_ORDER = [
        User,
        Integration,
        Briefing,
        Project,
        Email,
        CalendarEvent,
        BusinessContext
    ]

    try:
        print("Starting transaction...")
        # Bypassing FK constraints temporarily during bulk copy
        pg_session.execute(text("SET session_replication_role = 'replica';"))

        for model_class in MODELS_IN_ORDER:
            table_name = model_class.__tablename__
            print(f"Migrating table: {table_name}")

            sqlite_records = sqlite_session.query(model_class).all()
            if not sqlite_records:
                print(f"  No records found in SQLite. Skipping.")
                continue

            print(f"  Copying {len(sqlite_records)} records...")
            for record in sqlite_records:
                sqlite_session.expunge(record)  # Detach record from SQLite session
                make_transient(record)          # Clear instance state while keeping ID/data
                pg_session.add(record)          # Add to PostgreSQL session
            
            pg_session.flush()
            print(f"  Staged {len(sqlite_records)} records successfully.")

        # Re-enable triggers and foreign keys
        pg_session.execute(text("SET session_replication_role = 'origin';"))
        
        # Commit insertion
        pg_session.commit()
        print("Data copy committed successfully!")

        # 2. Reset sequences
        print("Synchronizing auto-increment ID sequences in PostgreSQL...")
        for model_class in MODELS_IN_ORDER:
            table_name = model_class.__tablename__
            pg_session.execute(text(f"SELECT setval('{table_name}_id_seq', COALESCE((SELECT MAX(id) FROM {table_name}), 1));"))
        pg_session.commit()
        print("Sequences synchronized successfully!")

    except Exception as e:
        pg_session.rollback()
        # Safely convert error string to ascii-escaped format to prevent console encoding failures
        err_msg = str(e).encode('ascii', 'backslashreplace').decode('ascii')
        print(f"\nMigration failed! Rolled back transaction. Error:\n{err_msg}")
        sys.exit(1)
    finally:
        sqlite_session.close()
        pg_session.close()

if __name__ == '__main__':
    run_migration()
