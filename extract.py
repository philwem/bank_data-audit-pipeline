import os
import requests
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    filename='pipeline.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

load_dotenv()
API_KEY = os.getenv("APILAYER_API_KEY")


def fetch_bank_data(iban_code):
    # Updated APILayer endpoint & query params
    url = "https://api.apilayer.com/bank_data/iban_validate"
    headers = {"apikey": API_KEY}
    params = {"iban_number": iban_code}

    logging.info(
        f"Initiating extraction request for IBAN: {iban_code[:4]}****")

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        logging.info(
            f"API Response Latency: {response.elapsed.total_seconds()}s")

        response.raise_for_status()
        logging.info(f"HTTP Extraction Successful: {response.status_code}")

        return response.json()

    except requests.exceptions.HTTPError as http_err:
        logging.error(
            f"HTTP error occurred: {http_err} - Status Code: {response.status_code}")
        raise
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Network request error occurred: {req_err}")
        raise


if __name__ == "__main__":
    # Test execution with a valid sample IBAN format
    test_iban = "GB33BUKB20201555555555"
    try:
        raw_payload = fetch_bank_data(test_iban)
        print("Raw Payload Extracted Successfully:")
        print(raw_payload)
    except Exception as e:
        print(f"Extraction failed. Check pipeline.log for details: {e}")
