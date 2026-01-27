import sys
import os
from sqlalchemy import create_engine, text
from app.core.config import settings

def update_schema():
    print(f"Connecting to database: {settings.create_database_url}")
    engine = create_engine(settings.create_database_url)
    
    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        
        # Check sessions table state column type
        print("Checking sessions table...")
        try:
            conn.execute(text("ALTER TABLE sessions ALTER COLUMN state TYPE VARCHAR"))
        except Exception as e:
            print(f"Session table update info: {e}")

        # Add columns to transactions if not exist
        print("Updating transactions table...")
        columns = [
            ("transaction_date", "TIMESTAMP DEFAULT NOW()"),
            ("updated_at", "TIMESTAMP"),
        ]
        
        for col, col_type in columns:
            try:
                conn.execute(text(f"ALTER TABLE transactions ADD COLUMN {col} {col_type}"))
                print(f"Added column {col}")
            except Exception as e:
                if "already exists" in str(e):
                    print(f"Column {col} already exists")
                else:
                    print(f"Error adding {col}: {e}")
                    
        print("Schema update attempt complete.")

if __name__ == "__main__":
    update_schema()
