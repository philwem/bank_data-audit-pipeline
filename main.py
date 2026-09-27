import logging
from extract import fetch_bank_data
from transform import transform_bank_payload
from load import load_to_duckdb

logging.basicConfig(
    filename='pipeline.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def run_pipeline(iban_code):
    """
    Orchestrates the Financial Data Audit Pipeline: 
    Extract (APILayer) -> Transform (Pandas) -> Load (DuckDB)
    """
    logging.info("==================================================")
    logging.info("STARTING BANK DATA AUDIT PIPELINE (DUCKDB)")
    logging.info("==================================================")

    try:
        # Step 1: Extract
        raw_data = fetch_bank_data(iban_code)

        # Step 2: Transform
        cleaned_df = transform_bank_payload(raw_data)

        # Step 3: Load into DuckDB
        load_to_duckdb(cleaned_df)

        logging.info("PIPELINE EXECUTION COMPLETED SUCCESSFULLY.")
        print("\n✅ Pipeline execution completed successfully! Data persisted in DuckDB.")

    except Exception as e:
        logging.error(f"PIPELINE FAILED: {str(e)}")
        print(f"\n❌ Pipeline failed: {e}")


if __name__ == "__main__":
    test_iban = "GB33BUKB20201555555555"
    run_pipeline(test_iban)
