import os
import logging
import requests
import duckdb
import pandas as pd

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

MOTHERDUCK_TOKEN = os.getenv("MOTHERDUCK_TOKEN")
APILAYER_KEY = os.getenv("APILAYER_KEY") or os.getenv("APILAYER_API_KEY")
TARGET_DATABASE = "bank_audit_db"

TARGET_COUNTRY = os.getenv("TARGET_COUNTRY", "DE")
PER_PAGE = 50
PAGE = 1

if not MOTHERDUCK_TOKEN:
    raise ValueError(
        "CRITICAL: MOTHERDUCK_TOKEN environment variable is not set.")
if not APILAYER_KEY:
    raise ValueError("CRITICAL: APILAYER_KEY environment variable is not set.")


def fetch_bank_data_from_apilayer(country="DE", page=1, per_page=50):
    """Fetches bank details and IBAN structure data from APILayer API."""
    url = f"https://api.apilayer.com/bank_data/all?per_page={per_page}&page={page}&country={country}"
    headers = {"apikey": APILAYER_KEY}

    logging.info(
        f"Fetching bank data from APILayer for country '{country}' (Page {page})...")

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, dict):
            records = data.get("data", data.get("banks", [data]))
        elif isinstance(data, list):
            records = data
        else:
            records = []

        logging.info(
            f"Successfully retrieved {len(records)} record(s) from APILayer.")
        return records

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch data from APILayer API: {str(e)}")
        raise e


def stream_apilayer_to_motherduck():
    """Ingests APILayer records into MotherDuck raw storage layer."""
    records = fetch_bank_data_from_apilayer(
        country=TARGET_COUNTRY, page=PAGE, per_page=PER_PAGE)

    if not records:
        logging.warning(
            "No records returned from APILayer. Exiting ingestion task.")
        return

    logging.info("Connecting to MotherDuck Cloud Lakehouse...")
    conn = duckdb.connect(
        f"md:{TARGET_DATABASE}?motherduck_token={MOTHERDUCK_TOKEN}")

    try:
        # Ensure target schema exists
        conn.execute("""
            CREATE TABLE IF NOT EXISTS raw_iban_audit (
                iban VARCHAR,
                valid BOOLEAN,
                bank_name VARCHAR,
                country_code VARCHAR,
                processed_at TIMESTAMP
            );
        """)

        # Parse fields returned by APILayer into a list of dicts
        formatted_records = []
        for item in records:
            if not isinstance(item, dict):
                continue

            iban_val = item.get("iban") or item.get(
                "bic") or item.get("bank_code") or "N/A"
            bank_name_val = item.get("bank_name") or item.get(
                "name") or item.get("bank") or "UNKNOWN"
            country_val = item.get("country_code") or item.get(
                "country") or TARGET_COUNTRY

            is_valid_val = bool(iban_val and iban_val != "N/A")

            formatted_records.append({
                "iban": str(iban_val),
                "valid": is_valid_val,
                "bank_name": str(bank_name_val),
                "country_code": str(country_val)
            })

        logging.info(
            f"Prepared {len(formatted_records)} record(s) for MotherDuck insertion.")

        # Convert list to pandas DataFrame so DuckDB can scan it
        df = pd.DataFrame(formatted_records)

        # Register DataFrame into DuckDB session
        conn.register("apilayer_temp_records", df)

        # Stream records directly into MotherDuck table
        query = """
        INSERT INTO raw_iban_audit (
            iban,
            valid,
            bank_name,
            country_code,
            processed_at
        )
        SELECT 
            iban,
            valid,
            COALESCE(bank_name, 'UNKNOWN') AS bank_name,
            COALESCE(country_code, 'XX') AS country_code,
            CURRENT_TIMESTAMP AS processed_at
        FROM apilayer_temp_records;
        """

        conn.execute(query)
        logging.info(
            "Successfully appended APILayer records into MotherDuck `raw_iban_audit`.")

    except Exception as e:
        logging.error(f"Failed during MotherDuck ingestion: {str(e)}")
        raise e
    finally:
        conn.close()
        logging.info("Closed MotherDuck connection.")


if __name__ == "__main__":
    stream_apilayer_to_motherduck()
