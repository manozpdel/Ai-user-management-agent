import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()


# Create and return a new database connection
def get_connection():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    return conn


# Create required database tables and triggers if they don't already exist
def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # Enable pgcrypto extension (needed for UUID generation)
    cursor.execute("""
        CREATE EXTENSION IF NOT EXISTS "pgcrypto";

        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            phone_number VARCHAR(50),
            location VARCHAR(255),
            age INTEGER,
            profession VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Function to automatically update the updated_at column
        CREATE OR REPLACE FUNCTION update_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        -- Remove old trigger if it exists
        DROP TRIGGER IF EXISTS set_updated_at ON users;

        -- Trigger that updates the updated_at field on every update
        CREATE TRIGGER set_updated_at
        BEFORE UPDATE ON users
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at();
    """)

    conn.commit()
    cursor.close()
    conn.close()