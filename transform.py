import pandas as pd
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    filename='pipeline.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def transform_bank_payload(raw_json):
    """
    Transforms nested APILayer Bank Data JSON into a clean, normalized pandas DataFrame.
    Performs schema validation and adds audit metadata.
    """
    logging.info("Starting transformation & data quality validation...")

    # 1. Data Quality Assertion: Ensure basic keys exist
    if not isinstance(raw_json, dict) or 'valid' not in raw_json:
        logging.error("Data Quality Failed: Invalid API payload structure.")
        raise ValueError("Invalid payload: missing core validation fields.")

    # 2. Extract top-level and nested dictionaries safely
    iban = raw_json.get('iban', '')
    is_valid = raw_json.get('valid', False)
    message = raw_json.get('message', '')

    iban_data = raw_json.get('iban_data', {})
    bank_data = raw_json.get('bank_data', {})

    # 3. Flatten into a normalized record dictionary
    transformed_record = {
        "iban": iban,
        "is_valid": is_valid,
        "validation_message": message,
        "country_name": iban_data.get('country', ''),
        "country_code": iban_data.get('country_code', ''),
        "is_sepa": iban_data.get('sepa_country', False),
        "checksum": iban_data.get('checksum', ''),
        "account_number": iban_data.get('account_number', ''),
        "bank_code": iban_data.get('bank_code', ''),
        "bank_name": bank_data.get('name', ''),
        "city": bank_data.get('city', ''),
        "bic_swift": bank_data.get('bic', ''),
        "processed_at": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    }

    # 4. Convert normalized record into a 1-row pandas DataFrame
    df = pd.DataFrame([transformed_record])

    logging.info(
        f"Transformation Complete. Rows: {len(df)} | Columns: {list(df.columns)}")
    return df


if __name__ == "__main__":
    # Test execution using sample extraction data
    from extract import fetch_bank_data

    test_iban = "GB33BUKB20201555555555"
    print("Fetching raw data for transformation test...")
    raw_payload = fetch_bank_data(test_iban)

    print("\nTransforming payload with pandas...")
    cleaned_df = transform_bank_payload(raw_payload)

    print("\nCleaned DataFrame Preview:")
    print(cleaned_df[['iban', 'bank_name', 'country_code',
          'bic_swift', 'is_sepa', 'processed_at']])
