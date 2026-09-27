import logging
import os
import duckdb
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    filename='pipeline.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

MOTHERDUCK_TOKEN = os.getenv("MOTHERDUCK_TOKEN")

# Use generic 'md:' connection string for MotherDuck to connect to default cloud workspace
if MOTHERDUCK_TOKEN:
    DATABASE_TARGET = f"md:?token={MOTHERDUCK_TOKEN}"
    logging.info("Targeting Cloud Storage Engine: MotherDuck Cloud")
else:
    DATABASE_TARGET = "analytics.duckdb"
    logging.info("Targeting Local Storage Engine: DuckDB (analytics.duckdb)")


def load_to_duckdb(df, table_name="dim_bank_directory"):
    """Persists Pandas DataFrame into DuckDB or MotherDuck Cloud."""
    logging.info(
        f"Initiating persistence write to target: {DATABASE_TARGET}...")

    if df.empty:
        logging.warning("Load step skipped: Empty DataFrame.")
        return False

    try:
        conn = duckdb.connect(DATABASE_TARGET)

        # If using MotherDuck Cloud, ensure database exists and switch context
        if MOTHERDUCK_TOKEN:
            conn.execute("CREATE DATABASE IF NOT EXISTS bank_audit_db;")
            conn.execute("USE bank_audit_db;")

        conn.register("df_view", df)

        # Create target table if it doesn't exist and append records
        conn.execute(
            f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM df_view WHERE 1=0;")
        conn.execute(f"INSERT INTO {table_name} SELECT * FROM df_view;")

        row_count = conn.execute(
            f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        conn.close()

        logging.info(
            f"Persistence Successful: Total records in '{table_name}': {row_count}")
        return True

    except Exception as e:
        logging.error(f"Persistence Failure: {str(e)}")
        raise


if __name__ == "__main__":
    try:
        from scripts.extract import fetch_bank_data
        from scripts.transform import transform_bank_payload
    except ImportError:
        from extract import fetch_bank_data
        from transform import transform_bank_payload

    test_iban = "GB33BUKB20201555555555"
    print("Testing Persistence Layer...")

    raw = fetch_bank_data(test_iban)
    cleaned_df = transform_bank_payload(raw)

    success = load_to_duckdb(cleaned_df)

    if success:
        print("\n✅ Data successfully persisted!")

        # Query database back using DuckDB SQL
        conn = duckdb.connect(DATABASE_TARGET)
        if MOTHERDUCK_TOKEN:
            conn.execute("USE bank_audit_db;")

        result_df = conn.execute(
            "SELECT iban, bank_name, bic_swift, processed_at FROM dim_bank_directory"
        ).df()

        print("\nQuery Result Preview:")
        print(result_df)
        conn.close()
