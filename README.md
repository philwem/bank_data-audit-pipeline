# Financial Data Audit Pipeline (APILayer → Pandas → DuckDB)

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![DuckDB](https://img.shields.io/badge/DuckDB-FFF000?style=for-the-badge&logo=duckdb&logoColor=black)
![License](https://img.shields.io/badge/License-MIT-blue.style=for-the-badge)

A modular, production-grade financial data ingestion and auditing pipeline built to validate international bank metadata (IBAN/BIC), normalize deeply nested JSON payloads, enforce data quality circuit breakers, and persist structured telemetry into an in-process columnar analytical database (DuckDB).

---

## 1. Problem Statement

Cross-border financial transactions frequently suffer from settlement delays, high drop-off rates, and compliance failures due to invalid or malformed International Bank Account Numbers (IBANs) and SWIFT/BIC codes. 

Traditional payment processing pipelines often fail at scale because:
1. **Unvalidated API Ingestion:** Unchecked upstream payloads contain schema mutations, null values, or bad bank identifiers that pollute downstream analytics databases.
2. **Heavy Row-Oriented Storage Overhead:** Storing transaction validation records in traditional row-based engines (like SQLite or PostgreSQL) introduces significant I/O latency when running aggregate analytical audits across millions of payment records.
3. **Lack of Telemetry & PII Leakage:** Unmasked sensitive customer identifiers (account numbers, IBANs) written directly to unencrypted system logs violate data protection regulations (GDPR/PCI-DSS).

**The Solution:** A decoupled, modular **ETL/ELT Data Pipeline** that automates verification via the APILayer Bank Data API, enforces strict schema assertions in memory using `pandas`, maks PII in execution logs, and persists clean audit records into a local **DuckDB OLAP Lakehouse**.

---

## 2. Pipeline Architecture

The pipeline follows a modular **Extract-Transform-Load (ETL)** pattern, separating network orchestration, data quality validation, and storage persistence.

![PipeLine Execution Flow](/Docs/Pipeline%20Execution%20Flow.png)

### Architectural Decisions & Tech Stack
* **Language & Runtime:** Python 3.9+ running inside a isolated virtual environment (`venv`).
* **Ingestion Layer (`extract.py`):** Uses `requests` with strict 30-second read timeouts, automated exception handling, and PII masking (`GB33****`) to prevent logging customer account numbers.
* **Transformation Layer (`transform.py`):** Utilizes `pandas` to unnest hierarchical JSON structures (`iban_data`, `bank_data`) into a flat tabular schema while injecting `processed_at` execution timestamps.
* **Storage Layer (`load.py`):** Leverages **DuckDB** for zero-copy memory transfers from pandas DataFrames, providing a columnar, vectorized OLAP environment optimized for low-latency SQL analytics.

---

## 3. Project Structure

bank-data-audit-pipeline/
├── .env                # API Credentials & Environment Variables (Git-ignored)
├── .gitignore          # Security rules preventing leak of secrets & database files
├── requirements.txt    # Frozen Python library dependencies
├── pipeline.log        # Execution telemetry, performance SLA tracking & audit logs
├── analytics.duckdb    # DuckDB columnar OLAP database file
├── extract.py          # REST API Client & PII-masked logging handler
├── transform.py        # Data normalization, schema validation & circuit breakers
├── load.py             # DuckDB zero-copy persistence engine
└── main.py             # Master ETL Pipeline Orchestrator entrypoint

