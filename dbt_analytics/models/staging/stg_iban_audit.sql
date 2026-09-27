with source_data as (
    select
        iban,
        is_valid,
        bank_name,
        country_code,
        processed_at::timestamp as processed_at
    from {{ source('motherduck_raw', 'dim_bank_directory') }}
)

select
    iban,
    coalesce(is_valid, false) as is_valid,
    upper(coalesce(bank_name, 'UNKNOWN')) as bank_name,
    coalesce(country_code, 'XX') as country_code,
    processed_at,
    date_trunc('day', processed_at) as audit_date
from source_data
