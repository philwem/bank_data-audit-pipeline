from datetime import datetime, timedelta
import os
from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator

default_args = {
    'owner': 'data_engineering',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=2),
}

with DAG(
    'financial_iban_audit_pipeline',
    default_args=default_args,
    description='Automated daily execution of financial IBAN audit pipeline into MotherDuck Cloud',
    schedule_interval='0 0 * * *',  # Executes daily at midnight (Cron: 00:00)
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['finance', 'motherduck', 'etl'],
) as dag:

  run_docker_etl = DockerOperator(
      task_id='run_iban_audit_container',
      image='bank-audit-pipeline:latest',
      container_name='airflow_iban_audit_run',
      api_version='auto',
      auto_remove=True,
      command='python main.py',
      docker_url='unix://var/run/docker.sock',
      network_mode='host',
      # Pass environment variables loaded from .env to the container
      environment={
          'APILAYER_API_KEY': os.getenv('APILAYER_API_KEY'),
          'MOTHERDUCK_TOKEN': os.getenv('MOTHERDUCK_TOKEN'),
      },
  )

  run_docker_etl
