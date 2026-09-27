import os
import logging
import duckdb
import pandas as pd

# Configure logging
logging.basicConfig(
    filename='pipeline.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Path to local DuckDB database file
DUCKDB_PATH = "analytics.duckdb"


def load_to_duckdb(df, table_name="dim_bank_directory"):
    """
    Persists a cleaned pandas DataFrame directly into DuckDB.
    Creates table automatically if it doesn't exist, and appends new audit records.
    """
    logging.info(
        f"Initiating persistence write to DuckDB database ({DUCKDB_PATH})...")

    if df.empty:
        logging.warning("Load step skipped: Received an empty DataFrame.")
        return False

    try:
        # Establish connection to DuckDB file
        conn = duckdb.connect(DUCKDB_PATH)

        # DuckDB can directly query and register pandas DataFrames in memory
        conn.register("df_view", df)

        # Create table if not exists, then insert
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} AS 
            SELECT * FROM df_view WHERE 1=0;
        """)

        conn.execute(f"""
            INSERT INTO {table_name} 
            SELECT * FROM df_view;
        """)

        # Fetch row count for verification
        row_count = conn.execute(
            f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        conn.close()

        logging.info(
            f"DuckDB Persist Successful: Appended row(s). Total rows in '{table_name}': {row_count}")
        return True

    except Exception as e:
        logging.error(f"DuckDB Persistence Failure: {str(e)}")
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
        conn = duckdb.connect(DUCKDB_PATH)
        result_df = conn.execute(
            "SELECT iban, bank_name, bic_swift, processed_at FROM dim_bank_directory").df()
        print("\nDuckDB Query Result:")
        print(result_df)
        conn.close()
