import os
import logging
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


load_dotenv()

logging.basicConfig(
    filename='pipeline.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Connect to MotherDuck if token exists, otherwise fallback to local DuckDB file
MOTHERDUCK_TOKEN = os.getenv("MOTHERDUCK_TOKEN")
DATABASE_TARGET = f"md:bank_audit_db?token={MOTHERDUCK_TOKEN}" if MOTHERDUCK_TOKEN else "analytics.duckdb"


def load_to_duckdb(df, table_name="dim_bank_directory"):
    logging.info(
        f"Initiating persistence write to target: {DATABASE_TARGET}...")

    if df.empty:
        logging.warning("Load step skipped: Empty DataFrame.")
        return False

    try:
        conn = duckdb.connect(DATABASE_TARGET)
        conn.register("df_view", df)

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
    from extract import fetch_bank_data
    from transform import transform_bank_payload

    test_iban = "GB33BUKB20201555555555"
    print("Testing DuckDB Persistence Layer...")

    raw = fetch_bank_data(test_iban)
    cleaned_df = transform_bank_payload(raw)

    success = load_to_duckdb(cleaned_df)

    if success:
        print("\nData successfully persisted into DuckDB: 'analytics.duckdb'")

        # Query database back using DuckDB SQL
        conn = duckdb.connect(DATABASE_TARGET)
        result_df = conn.execute(
            "SELECT iban, bank_name, bic_swift, processed_at FROM dim_bank_directory").df()
        print("\nDuckDB Query Result:")
        print(result_df)
        conn.close()
