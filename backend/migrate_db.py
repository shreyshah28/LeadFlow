import sqlite3
import os
import sys
from datetime import datetime

def run_migration(db_path: str = None) -> bool:
    if db_path is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, "leadflow.db")

    if not os.path.exists(db_path):
        print(f"[Migration] Database file not found at: {db_path}")
        return False

    print(f"[Migration] Starting migration on: {db_path}")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    try:
        # 1. Record pre-migration count
        c.execute("SELECT count(*) FROM leads")
        pre_count = c.fetchone()[0]
        print(f"[Migration] Pre-migration lead count: {pre_count}")

        # 2. Check existing columns
        c.execute("PRAGMA table_info(leads)")
        columns = [row[1] for row in c.fetchall()]
        print(f"[Migration] Existing columns: {columns}")

        # 3. Add updated_at column if missing
        if "updated_at" not in columns:
            print("[Migration] Adding 'updated_at' DATETIME column to 'leads' table...")
            c.execute("ALTER TABLE leads ADD COLUMN updated_at DATETIME")
            # Populate updated_at from created_at
            c.execute("""
                UPDATE leads 
                SET updated_at = COALESCE(created_at, datetime('now')) 
                WHERE updated_at IS NULL
            """)
            print("[Migration] Populated 'updated_at' for existing records.")
        else:
            print("[Migration] 'updated_at' column already exists.")

        # 4. Add index for email if missing
        c.execute("PRAGMA index_list(leads)")
        index_names = [row[1] for row in c.fetchall()]
        if "ix_leads_email" not in index_names:
            print("[Migration] Creating index 'ix_leads_email' on leads(email)...")
            c.execute("CREATE INDEX IF NOT EXISTS ix_leads_email ON leads(email)")
        else:
            print("[Migration] 'ix_leads_email' already exists.")

        # 5. Ensure daily_email_logs table exists
        c.execute("""
            CREATE TABLE IF NOT EXISTS daily_email_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                delivery_date VARCHAR(50) NOT NULL UNIQUE,
                recipient VARCHAR(255) NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'SUCCESS',
                due_today_count INTEGER NOT NULL DEFAULT 0,
                overdue_count INTEGER NOT NULL DEFAULT 0,
                sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                error_message TEXT
            )
        """)
        c.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_daily_email_logs_delivery_date ON daily_email_logs (delivery_date)")
        c.execute("CREATE INDEX IF NOT EXISTS ix_daily_email_logs_status ON daily_email_logs (status)")
        print("[Migration] Verified 'daily_email_logs' table and indices.")

        # 5. Commit changes
        conn.commit()

        # 6. Verify post-migration integrity
        c.execute("SELECT count(*) FROM leads")
        post_count = c.fetchone()[0]
        print(f"[Migration] Post-migration lead count: {post_count}")

        if post_count != pre_count:
            raise RuntimeError(f"Data count mismatch! Pre: {pre_count}, Post: {post_count}")

        # 7. Check that updated_at is populated on all rows
        c.execute("SELECT count(*) FROM leads WHERE updated_at IS NULL")
        null_updated = c.fetchone()[0]
        if null_updated > 0:
            raise RuntimeError(f"Found {null_updated} rows with NULL updated_at after migration!")

        print("[Migration] Migration completed successfully with 100% data preservation!")
        return True

    except Exception as e:
        conn.rollback()
        print(f"[Migration ERROR] Migration failed: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)

